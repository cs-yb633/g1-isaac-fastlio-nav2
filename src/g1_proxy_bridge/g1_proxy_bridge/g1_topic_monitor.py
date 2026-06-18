#!/usr/bin/env python3
"""Read-only topic monitor for the G1 navigation workflow.

This node subscribes to configured topics and periodically prints message counts.
It never publishes motion commands, so it is safe for real-robot data checks.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, PointCloud2


class G1TopicMonitor(Node):
    """Monitor selected G1 topics without commanding the robot."""

    def __init__(self) -> None:
        super().__init__('g1_topic_monitor')
        self.declare_parameter('lidar_topic', '/g1/lidar_points')
        self.declare_parameter('imu_topic', '/g1/imu')
        self.declare_parameter('odom_topic', '/g1/odom')
        self.declare_parameter('report_period_sec', 5.0)

        self.lidar_topic = self.get_parameter('lidar_topic').value
        self.imu_topic = self.get_parameter('imu_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.report_period_sec = float(self.get_parameter('report_period_sec').value)

        self.counts: Dict[str, int] = defaultdict(int)
        self.last_counts: Dict[str, int] = defaultdict(int)

        self.create_subscription(PointCloud2, self.lidar_topic, lambda msg: self._tick(self.lidar_topic), 10)
        self.create_subscription(Imu, self.imu_topic, lambda msg: self._tick(self.imu_topic), 50)
        self.create_subscription(Odometry, self.odom_topic, lambda msg: self._tick(self.odom_topic), 20)
        self.create_timer(self.report_period_sec, self.report)

        self.get_logger().info('G1 read-only topic monitor started.')
        self.get_logger().info(f'LiDAR topic: {self.lidar_topic}')
        self.get_logger().info(f'IMU topic:   {self.imu_topic}')
        self.get_logger().info(f'Odom topic:  {self.odom_topic}')

    def _tick(self, topic: str) -> None:
        self.counts[topic] += 1

    def report(self) -> None:
        lines = []
        for topic in [self.lidar_topic, self.imu_topic, self.odom_topic]:
            total = self.counts[topic]
            delta = total - self.last_counts[topic]
            self.last_counts[topic] = total
            hz = delta / self.report_period_sec if self.report_period_sec > 0.0 else 0.0
            lines.append(f'{topic}: total={total}, approx_hz={hz:.2f}')
        self.get_logger().info(' | '.join(lines))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = G1TopicMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
