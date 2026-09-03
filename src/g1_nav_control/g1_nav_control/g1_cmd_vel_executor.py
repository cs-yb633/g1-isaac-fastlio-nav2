"""Receive /cmd_vel and execute it only through explicit safety gates."""

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node

from .loco_command_sink import LocoCommandSink
from .velocity_safety import safe_velocity, VelocityWatchdog


class G1CmdVelExecutor(Node):
    """Guarded ROS 2 Twist executor for the G1 LocoClient."""

    LOG_INTERVAL_SECONDS = 0.2
    WATCHDOG_TIMER_SECONDS = 0.05

    def __init__(self) -> None:
        super().__init__("g1_cmd_vel_executor")

        self.declare_parameter("dry_run", True)
        self.declare_parameter("network_interface", "enp6s0")
        self.declare_parameter("enable_motion", False)
        self.declare_parameter("max_vx", 0.20)
        self.declare_parameter("max_vy", 0.0)
        self.declare_parameter("max_wz", 0.40)
        self.declare_parameter("cmd_timeout", 0.3)

        self._dry_run = self.get_parameter("dry_run").value
        self._enable_motion = self.get_parameter("enable_motion").value
        if not isinstance(self._dry_run, bool) or not isinstance(
            self._enable_motion, bool
        ):
            raise ValueError("dry_run and enable_motion must be booleans")

        network_interface = self.get_parameter("network_interface").value
        self._max_vx = float(self.get_parameter("max_vx").value)
        self._max_vy = float(self.get_parameter("max_vy").value)
        self._max_wz = float(self.get_parameter("max_wz").value)
        timeout = float(self.get_parameter("cmd_timeout").value)

        # Validate configuration before creating ROS entities.
        safe_velocity(
            0.0,
            0.0,
            0.0,
            max_vx=self._max_vx,
            max_vy=self._max_vy,
            max_wz=self._max_wz,
        )
        self._watchdog = VelocityWatchdog(timeout)
        self._command_sink = LocoCommandSink(
            dry_run=self._dry_run,
            enable_motion=self._enable_motion,
            network_interface=network_interface,
            command_duration=timeout,
        )
        self._last_command_log_time = float("-inf")

        if self._command_sink.current_fsm_id is not None:
            self.get_logger().info(
                f"Current G1 FSM: {self._command_sink.current_fsm_id}"
            )
        if not self._dry_run and not self._enable_motion:
            self.get_logger().warning(
                "MOTION DISABLED: velocity commands cannot reach SetVelocity"
            )

        self._subscription = self.create_subscription(
            Twist, "/cmd_vel", self._on_cmd_vel, 10
        )
        self._timer = self.create_timer(
            self.WATCHDOG_TIMER_SECONDS, self._on_watchdog
        )

    def _now_seconds(self) -> float:
        return self.get_clock().now().nanoseconds / 1_000_000_000.0

    def _on_cmd_vel(self, msg: Twist) -> None:
        velocity = safe_velocity(
            msg.linear.x,
            msg.linear.y,
            msg.angular.z,
            max_vx=self._max_vx,
            max_vy=self._max_vy,
            max_wz=self._max_wz,
        )
        if velocity is None:
            self.get_logger().warning("Rejected /cmd_vel containing NaN or Inf")
            return

        now = self._now_seconds()
        self._watchdog.accept(velocity, now)
        result = self._command_sink.apply(velocity)
        if now - self._last_command_log_time >= self.LOG_INTERVAL_SECONDS:
            if result == "dry_run":
                prefix = "DRY-RUN"
            elif result == "motion_disabled":
                prefix = "MOTION DISABLED"
            elif result == "fsm_rejected":
                prefix = f"FSM {self._command_sink.current_fsm_id} REJECTED"
            else:
                prefix = "COMMAND SENT"
            self.get_logger().info(
                f"{prefix} vx={velocity.vx:.3f} "
                f"vy={velocity.vy:.3f} wz={velocity.wz:.3f}"
            )
            self._last_command_log_time = now

    def _on_watchdog(self) -> None:
        if self._watchdog.check(self._now_seconds()):
            result = self._command_sink.apply(self._watchdog.desired)
            if result == "dry_run":
                prefix = "DRY-RUN"
            elif result == "motion_disabled":
                prefix = "MOTION DISABLED"
            elif result == "fsm_rejected":
                prefix = f"FSM {self._command_sink.current_fsm_id} REJECTED"
            else:
                prefix = "COMMAND SENT"
            self.get_logger().info(f"{prefix} watchdog STOP")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = G1CmdVelExecutor()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
