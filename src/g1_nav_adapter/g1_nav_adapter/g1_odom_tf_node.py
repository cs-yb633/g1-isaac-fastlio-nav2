"""Broadcast a planar navigation TF decomposition of /dog_odom."""

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from tf2_ros import TransformBroadcaster

from .odom_validation import (
    DEFAULT_CHILD_FRAME,
    DEFAULT_MAX_ABS_POSITION_M,
    DEFAULT_ODOM_FRAME,
    DEFAULT_QUATERNION_NORM_TOLERANCE,
    ValidationRules,
    validate_odometry_fields,
)
from .planar_odometry import planar_odometry_transforms
from .startup_qualification import (
    DEFAULT_STARTUP_VALID_SAMPLES,
    StartupQualification,
)


class G1OdomTfNode(Node):
    def __init__(self):
        super().__init__("g1_odom_tf_node")
        self.declare_parameter("odom_topic", "/dog_odom")
        self.declare_parameter("odom_frame", DEFAULT_ODOM_FRAME)
        self.declare_parameter("source_child_frame", DEFAULT_CHILD_FRAME)
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter(
            "quaternion_norm_tolerance", DEFAULT_QUATERNION_NORM_TOLERANCE
        )
        self.declare_parameter("max_abs_position_m", DEFAULT_MAX_ABS_POSITION_M)
        self.declare_parameter(
            "startup_valid_samples", DEFAULT_STARTUP_VALID_SAMPLES
        )
        self.declare_parameter("statistics_log_period_sec", 30.0)

        self._odom_frame = self.get_parameter("odom_frame").value
        self._source_child_frame = self.get_parameter("source_child_frame").value
        self._base_frame = self.get_parameter("base_frame").value
        self._norm_tolerance = self.get_parameter("quaternion_norm_tolerance").value
        self._max_abs_position_m = self.get_parameter("max_abs_position_m").value
        for parameter_name, frame in (
            ("odom_frame", self._odom_frame),
            ("source_child_frame", self._source_child_frame),
            ("base_frame", self._base_frame),
        ):
            if not isinstance(frame, str) or not frame or frame.startswith("/"):
                raise ValueError(
                    f"{parameter_name} must be a non-empty TF frame without a leading '/'"
                )
        if len({self._odom_frame, self._source_child_frame, self._base_frame}) != 3:
            raise ValueError("odom, source child, and base frames must be distinct")

        self._rules = ValidationRules(
            odom_frame=self._odom_frame,
            child_frame=self._source_child_frame,
            quaternion_norm_tolerance=self._norm_tolerance,
            max_abs_position_m=self._max_abs_position_m,
        )
        startup_samples = self.get_parameter("startup_valid_samples").value
        self._qualification = StartupQualification(startup_samples)
        self._previous_valid_stamp_ns = None

        self._broadcaster = TransformBroadcaster(self)
        self._subscription = self.create_subscription(
            Odometry,
            self.get_parameter("odom_topic").value,
            self._on_odometry,
            qos_profile_sensor_data,
        )
        statistics_period = self.get_parameter("statistics_log_period_sec").value
        if not isinstance(statistics_period, (int, float)) or statistics_period < 0.0:
            raise ValueError("statistics_log_period_sec must be >= 0")
        if statistics_period > 0.0:
            self._statistics_timer = self.create_timer(
                statistics_period, self._log_statistics
            )

    def _log_statistics(self):
        stats = self._qualification.statistics
        self.get_logger().info(
            "odometry statistics: "
            f"received_count={stats.received_count} "
            f"valid_count={stats.valid_count} "
            f"rejected_count={stats.rejected_count} "
            f"startup_valid_streak={stats.startup_valid_streak} "
            f"qualified={stats.qualified}"
        )

    @staticmethod
    def _to_message(stamp, parent, child, transform):
        message = TransformStamped()
        message.header.stamp = stamp
        message.header.frame_id = parent
        message.child_frame_id = child
        message.transform.translation.x = transform.translation[0]
        message.transform.translation.y = transform.translation[1]
        message.transform.translation.z = transform.translation[2]
        message.transform.rotation.x = transform.rotation[0]
        message.transform.rotation.y = transform.rotation[1]
        message.transform.rotation.z = transform.rotation[2]
        message.transform.rotation.w = transform.rotation[3]
        return message

    def _on_odometry(self, message):
        pose = message.pose.pose
        twist = message.twist.twist
        position = (pose.position.x, pose.position.y, pose.position.z)
        quaternion = (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
        )
        stamp_ns = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        validation = validate_odometry_fields(
            frame_id=message.header.frame_id,
            child_frame_id=message.child_frame_id,
            stamp_ns=stamp_ns,
            position=position,
            quaternion=quaternion,
            linear_velocity=(twist.linear.x, twist.linear.y, twist.linear.z),
            angular_velocity=(twist.angular.x, twist.angular.y, twist.angular.z),
            rules=self._rules,
            previous_valid_stamp_ns=self._previous_valid_stamp_ns,
        )
        publish_allowed, just_qualified = self._qualification.observe(validation.valid)
        if not validation.valid:
            self.get_logger().warning(
                "Rejecting invalid odometry sample: " + ", ".join(validation.errors),
                throttle_duration_sec=5.0,
            )
            return
        self._previous_valid_stamp_ns = stamp_ns
        if just_qualified:
            self.get_logger().info(
                "Startup qualification complete after "
                f"{self._qualification.required_valid_samples} consecutive valid samples"
            )
        if not publish_allowed:
            return

        odom_to_base, base_to_source = planar_odometry_transforms(
            position,
            quaternion,
            self._norm_tolerance,
            self._max_abs_position_m,
        )

        self._broadcaster.sendTransform(
            [
                self._to_message(
                    message.header.stamp,
                    self._odom_frame,
                    self._base_frame,
                    odom_to_base,
                ),
                self._to_message(
                    message.header.stamp,
                    self._base_frame,
                    self._source_child_frame,
                    base_to_source,
                ),
            ]
        )


def main(args=None):
    rclpy.init(args=args)
    node = G1OdomTfNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
