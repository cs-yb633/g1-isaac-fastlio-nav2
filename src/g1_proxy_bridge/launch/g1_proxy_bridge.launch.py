from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='g1_proxy_bridge',
            executable='g1_proxy_bridge_node',
            name='g1_proxy_bridge',
            output='screen',
            parameters=[{
                # Topics from Isaac Sim Carter.
                'carter_cmd_vel_topic': '/cmd_vel',
                'carter_odom_topic': '/chassis/odom',
                'carter_lidar_topic': '/front_3d_lidar/lidar_points',
                'carter_imu_topic': '/chassis/imu',

                # G1-style public interface.
                'g1_cmd_vel_topic': '/g1/cmd_vel',
                'g1_odom_topic': '/g1/odom',
                'g1_lidar_topic': '/g1/lidar_points',
                'g1_imu_topic': '/g1/imu',

                # Frame names.
                'odom_frame': 'odom',
                'base_frame': 'g1_base_link',
                'lidar_frame': 'g1_lidar_link',
                'imu_frame': 'g1_imu_link',

                # Approximate transforms measured from the current Isaac Sim proxy setup.
                'lidar_xyz': [-0.232, 0.0, 0.526],
                'lidar_rpy': [0.0, 0.0, 0.0],
                'imu_xyz': [-0.218, 0.024, 0.156],
                'imu_rpy': [0.0, 0.0, 0.0],
            }]
        )
    ])
