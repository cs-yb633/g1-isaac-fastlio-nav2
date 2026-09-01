"""Record a bounded, read-only CSV sample of /dog_odom."""

import csv
import math
from pathlib import Path

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from .odom_validation import (
    DEFAULT_CHILD_FRAME,
    DEFAULT_LARGE_JUMP_M,
    DEFAULT_MAX_ABS_POSITION_M,
    DEFAULT_ODOM_FRAME,
    DEFAULT_QUATERNION_NORM_TOLERANCE,
    ValidationRules,
    validate_odometry_fields,
)


CSV_FIELDS = (
    "sequence_index",
    "receive_time_ns",
    "header_stamp_ns",
    "header_frame_id",
    "child_frame_id",
    "position_x",
    "position_y",
    "position_z",
    "orientation_x",
    "orientation_y",
    "orientation_z",
    "orientation_w",
    "quaternion_norm",
    "linear_velocity_x",
    "linear_velocity_y",
    "linear_velocity_z",
    "angular_velocity_x",
    "angular_velocity_y",
    "angular_velocity_z",
    "position_magnitude",
    "timestamp_monotonic",
    "timestamp_delta_sec",
    "frame_id_consistent",
    "child_frame_id_consistent",
    "position_jump_m",
    "large_jump",
    "valid",
    "validation_errors",
)


class DogOdomProbe(Node):
    def __init__(self):
        super().__init__("dog_odom_probe")
        self.declare_parameter("odom_topic", "/dog_odom")
        self.declare_parameter("sample_count", 50)
        self.declare_parameter("duration_sec", 0.0)
        self.declare_parameter("output_path", "/tmp/dog_odom_probe.csv")
        self.declare_parameter("odom_frame", DEFAULT_ODOM_FRAME)
        self.declare_parameter("source_child_frame", DEFAULT_CHILD_FRAME)
        self.declare_parameter(
            "quaternion_norm_tolerance", DEFAULT_QUATERNION_NORM_TOLERANCE
        )
        self.declare_parameter("max_abs_position_m", DEFAULT_MAX_ABS_POSITION_M)
        self.declare_parameter("large_jump_m", DEFAULT_LARGE_JUMP_M)

        self._sample_limit = self.get_parameter("sample_count").value
        self._duration_sec = self.get_parameter("duration_sec").value
        if not isinstance(self._sample_limit, int) or self._sample_limit < 0:
            raise ValueError("sample_count must be an integer >= 0")
        if not math.isfinite(self._duration_sec) or self._duration_sec < 0.0:
            raise ValueError("duration_sec must be finite and >= 0")
        if self._sample_limit == 0 and self._duration_sec == 0.0:
            raise ValueError("sample_count and duration_sec cannot both be zero")
        self._large_jump_m = self.get_parameter("large_jump_m").value
        if not math.isfinite(self._large_jump_m) or self._large_jump_m <= 0.0:
            raise ValueError("large_jump_m must be finite and positive")

        self._rules = ValidationRules(
            odom_frame=self.get_parameter("odom_frame").value,
            child_frame=self.get_parameter("source_child_frame").value,
            quaternion_norm_tolerance=self.get_parameter(
                "quaternion_norm_tolerance"
            ).value,
            max_abs_position_m=self.get_parameter("max_abs_position_m").value,
        )
        self._output_path = Path(self.get_parameter("output_path").value).expanduser()
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self._output_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=CSV_FIELDS)
        self._writer.writeheader()
        self._file.flush()

        self._count = 0
        self._valid_count = 0
        self._rejected_count = 0
        self._done = False
        self._previous_received_stamp_ns = None
        self._previous_valid_stamp_ns = None
        self._previous_position = None
        self._subscription = self.create_subscription(
            Odometry,
            self.get_parameter("odom_topic").value,
            self._on_odometry,
            qos_profile_sensor_data,
        )
        if self._duration_sec > 0.0:
            self._stop_timer = self.create_timer(self._duration_sec, self._finish)
        self.get_logger().info(
            f"Recording read-only odometry to {self._output_path}; "
            f"sample_count={self._sample_limit} duration_sec={self._duration_sec:g}"
        )

    @property
    def done(self):
        return self._done

    def _on_odometry(self, message):
        if self._done:
            return
        pose = message.pose.pose
        twist = message.twist.twist
        position = (pose.position.x, pose.position.y, pose.position.z)
        quaternion = (
            pose.orientation.x,
            pose.orientation.y,
            pose.orientation.z,
            pose.orientation.w,
        )
        linear_velocity = (twist.linear.x, twist.linear.y, twist.linear.z)
        angular_velocity = (twist.angular.x, twist.angular.y, twist.angular.z)
        stamp_ns = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        timestamp_delta_sec = ""
        timestamp_monotonic = True
        if self._previous_received_stamp_ns is not None:
            timestamp_delta_sec = (
                stamp_ns - self._previous_received_stamp_ns
            ) / 1_000_000_000.0
            timestamp_monotonic = stamp_ns > self._previous_received_stamp_ns

        validation = validate_odometry_fields(
            frame_id=message.header.frame_id,
            child_frame_id=message.child_frame_id,
            stamp_ns=stamp_ns,
            position=position,
            quaternion=quaternion,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
            rules=self._rules,
            previous_valid_stamp_ns=self._previous_valid_stamp_ns,
        )
        position_jump_m = ""
        large_jump = False
        if self._previous_position is not None and all(
            math.isfinite(value) for value in position + self._previous_position
        ):
            position_jump_m = math.sqrt(
                sum(
                    (current - previous) ** 2
                    for current, previous in zip(position, self._previous_position)
                )
            )
            large_jump = position_jump_m > self._large_jump_m

        row = {
            "sequence_index": self._count,
            "receive_time_ns": self.get_clock().now().nanoseconds,
            "header_stamp_ns": stamp_ns,
            "header_frame_id": message.header.frame_id,
            "child_frame_id": message.child_frame_id,
            "position_x": position[0],
            "position_y": position[1],
            "position_z": position[2],
            "orientation_x": quaternion[0],
            "orientation_y": quaternion[1],
            "orientation_z": quaternion[2],
            "orientation_w": quaternion[3],
            "quaternion_norm": validation.quaternion_norm,
            "linear_velocity_x": linear_velocity[0],
            "linear_velocity_y": linear_velocity[1],
            "linear_velocity_z": linear_velocity[2],
            "angular_velocity_x": angular_velocity[0],
            "angular_velocity_y": angular_velocity[1],
            "angular_velocity_z": angular_velocity[2],
            "position_magnitude": validation.position_magnitude,
            "timestamp_monotonic": timestamp_monotonic,
            "timestamp_delta_sec": timestamp_delta_sec,
            "frame_id_consistent": message.header.frame_id == self._rules.odom_frame,
            "child_frame_id_consistent": (
                message.child_frame_id == self._rules.child_frame
            ),
            "position_jump_m": position_jump_m,
            "large_jump": large_jump,
            "valid": validation.valid,
            "validation_errors": ";".join(validation.errors),
        }
        self._writer.writerow(row)
        self._file.flush()
        self._count += 1
        if validation.valid:
            self._valid_count += 1
            self._previous_valid_stamp_ns = stamp_ns
        else:
            self._rejected_count += 1
        self._previous_received_stamp_ns = stamp_ns
        self._previous_position = position
        if self._sample_limit and self._count >= self._sample_limit:
            self._finish()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self._file.flush()
        self.get_logger().info(
            f"Probe complete: samples={self._count} valid={self._valid_count} "
            f"rejected={self._rejected_count} output={self._output_path}"
        )

    def close(self):
        if not self._file.closed:
            self._file.close()


def main(args=None):
    rclpy.init(args=args)
    node = DogOdomProbe()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.5)
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
