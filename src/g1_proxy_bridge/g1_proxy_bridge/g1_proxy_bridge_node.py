#!/usr/bin/env python3
"""Expose Isaac Sim Carter topics as Unitree G1-style /g1/* interfaces.

This node is intentionally simple:
- /g1/cmd_vel is forwarded to Carter's /cmd_vel.
- Carter odometry is republished as /g1/odom with G1 frame names.
- Carter PointCloud2 and IMU messages are republished as /g1/lidar_points and /g1/imu.
- TF is published as odom -> g1_base_link plus static sensor frames.

The node does not implement real Unitree G1 locomotion. It is a simulation
adapter for the "G1 visual model + hidden Carter motion proxy" workflow.
"""

from __future__ import annotations

import copy
import math
from typing import Iterable, Tuple

import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu, PointCloud2
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster


def quaternion_from_rpy(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
    """Convert roll, pitch, yaw to quaternion x, y, z, w."""
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return x, y, z, w


def make_transform(
    parent_frame: str,
    child_frame: str,
    xyz: Iterable[float],
    rpy: Iterable[float],
    stamp,
) -> TransformStamped:
    """Create a TransformStamped from xyz + rpy."""
    x, y, z = list(xyz)
    roll, pitch, yaw = list(rpy)
    qx, qy, qz, qw = quaternion_from_rpy(roll, pitch, yaw)

    tf = TransformStamped()
    tf.header.stamp = stamp
    tf.header.frame_id = parent_frame
    tf.child_frame_id = child_frame
    tf.transform.translation.x = float(x)
    tf.transform.translation.y = float(y)
    tf.transform.translation.z = float(z)
    tf.transform.rotation.x = float(qx)
    tf.transform.rotation.y = float(qy)
    tf.transform.rotation.z = float(qz)
    tf.transform.rotation.w = float(qw)
    return tf


class G1ProxyBridge(Node):
    """Bridge Isaac Sim Carter topics into /g1/* topics."""

    def __init__(self) -> None:
        super().__init__('g1_proxy_bridge')

        # Topic parameters.
        self.declare_parameter('g1_cmd_vel_topic', '/g1/cmd_vel')
        self.declare_parameter('carter_cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('carter_odom_topic', '/chassis/odom')
        self.declare_parameter('carter_lidar_topic', '/front_3d_lidar/lidar_points')
        self.declare_parameter('carter_imu_topic', '/chassis/imu')
        self.declare_parameter('g1_odom_topic', '/g1/odom')
        self.declare_parameter('g1_lidar_topic', '/g1/lidar_points')
        self.declare_parameter('g1_imu_topic', '/g1/imu')

        # Frame parameters.
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'g1_base_link')
        self.declare_parameter('lidar_frame', 'g1_lidar_link')
        self.declare_parameter('imu_frame', 'g1_imu_link')

        # Approximate sensor transforms from the current Isaac Sim proxy scene.
        self.declare_parameter('lidar_xyz', [-0.232, 0.0, 0.526])
        self.declare_parameter('lidar_rpy', [0.0, 0.0, 0.0])
        self.declare_parameter('imu_xyz', [-0.218, 0.024, 0.156])
        self.declare_parameter('imu_rpy', [0.0, 0.0, 0.0])

        self.g1_cmd_vel_topic = self.get_parameter('g1_cmd_vel_topic').value
        self.carter_cmd_vel_topic = self.get_parameter('carter_cmd_vel_topic').value
        self.carter_odom_topic = self.get_parameter('carter_odom_topic').value
        self.carter_lidar_topic = self.get_parameter('carter_lidar_topic').value
        self.carter_imu_topic = self.get_parameter('carter_imu_topic').value
        self.g1_odom_topic = self.get_parameter('g1_odom_topic').value
        self.g1_lidar_topic = self.get_parameter('g1_lidar_topic').value
        self.g1_imu_topic = self.get_parameter('g1_imu_topic').value

        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value
        self.lidar_frame = self.get_parameter('lidar_frame').value
        self.imu_frame = self.get_parameter('imu_frame').value

        self.lidar_xyz = list(self.get_parameter('lidar_xyz').value)
        self.lidar_rpy = list(self.get_parameter('lidar_rpy').value)
        self.imu_xyz = list(self.get_parameter('imu_xyz').value)
        self.imu_rpy = list(self.get_parameter('imu_rpy').value)

        self.cmd_vel_pub = self.create_publisher(Twist, self.carter_cmd_vel_topic, 10)
        self.odom_pub = self.create_publisher(Odometry, self.g1_odom_topic, 10)
        self.lidar_pub = self.create_publisher(PointCloud2, self.g1_lidar_topic, 10)
        self.imu_pub = self.create_publisher(Imu, self.g1_imu_topic, 50)

        self.create_subscription(Twist, self.g1_cmd_vel_topic, self.on_cmd_vel, 10)
        self.create_subscription(Odometry, self.carter_odom_topic, self.on_odom, 20)
        self.create_subscription(PointCloud2, self.carter_lidar_topic, self.on_lidar, 10)
        self.create_subscription(Imu, self.carter_imu_topic, self.on_imu, 50)

        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_tf_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_sensor_transforms()

        # Re-send static transforms a few times after startup to make RViz/debugging easier.
        self.static_timer = self.create_timer(2.0, self.publish_static_sensor_transforms)

        self.get_logger().info('G1 proxy bridge started.')
        self.get_logger().info(f'Command: {self.g1_cmd_vel_topic} -> {self.carter_cmd_vel_topic}')
        self.get_logger().info(f'Odom:    {self.carter_odom_topic} -> {self.g1_odom_topic}')
        self.get_logger().info(f'LiDAR:   {self.carter_lidar_topic} -> {self.g1_lidar_topic}')
        self.get_logger().info(f'IMU:     {self.carter_imu_topic} -> {self.g1_imu_topic}')

    def publish_static_sensor_transforms(self) -> None:
        """Publish base->sensor transforms."""
        now = self.get_clock().now().to_msg()
        lidar_tf = make_transform(
            self.base_frame,
            self.lidar_frame,
            self.lidar_xyz,
            self.lidar_rpy,
            now,
        )
        imu_tf = make_transform(
            self.base_frame,
            self.imu_frame,
            self.imu_xyz,
            self.imu_rpy,
            now,
        )
        self.static_tf_broadcaster.sendTransform([lidar_tf, imu_tf])

    def on_cmd_vel(self, msg: Twist) -> None:
        """Forward G1 cmd_vel to the Carter motion proxy."""
        self.cmd_vel_pub.publish(msg)

    def on_odom(self, msg: Odometry) -> None:
        """Republish Carter odometry as G1 odometry and broadcast odom->base TF."""
        out = copy.deepcopy(msg)
        out.header.frame_id = self.odom_frame
        out.child_frame_id = self.base_frame
        self.odom_pub.publish(out)

        tf = TransformStamped()
        tf.header.stamp = out.header.stamp
        tf.header.frame_id = self.odom_frame
        tf.child_frame_id = self.base_frame
        tf.transform.translation.x = out.pose.pose.position.x
        tf.transform.translation.y = out.pose.pose.position.y
        tf.transform.translation.z = out.pose.pose.position.z
        tf.transform.rotation = out.pose.pose.orientation
        self.tf_broadcaster.sendTransform(tf)

    def on_lidar(self, msg: PointCloud2) -> None:
        """Republish LiDAR point cloud with G1 LiDAR frame."""
        out = copy.deepcopy(msg)
        out.header.frame_id = self.lidar_frame
        self.lidar_pub.publish(out)

    def on_imu(self, msg: Imu) -> None:
        """Republish IMU message with G1 IMU frame."""
        out = copy.deepcopy(msg)
        out.header.frame_id = self.imu_frame
        self.imu_pub.publish(out)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = G1ProxyBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
