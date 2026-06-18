from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    enable_cmd_vel_forwarding = LaunchConfiguration('enable_cmd_vel_forwarding')
    publish_odom_tf = LaunchConfiguration('publish_odom_tf')
    publish_static_sensor_tf = LaunchConfiguration('publish_static_sensor_tf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'enable_cmd_vel_forwarding',
            default_value='true',
            description='Forward /g1/cmd_vel to Carter /cmd_vel. Set false for read-only diagnostics.',
        ),
        DeclareLaunchArgument(
            'publish_odom_tf',
            default_value='true',
            description='Publish odom -> g1_base_link TF from republished odometry.',
        ),
        DeclareLaunchArgument(
            'publish_static_sensor_tf',
            default_value='true',
            description='Publish g1_base_link -> sensor static transforms.',
        ),
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

                # Safety / behavior toggles.
                'enable_cmd_vel_forwarding': enable_cmd_vel_forwarding,
                'publish_odom_tf': publish_odom_tf,
                'publish_static_sensor_tf': publish_static_sensor_tf,

                # Approximate transforms measured from the current Isaac Sim proxy setup.
                'lidar_xyz': [-0.232, 0.0, 0.526],
                'lidar_rpy': [0.0, 0.0, 0.0],
                'imu_xyz': [-0.218, 0.024, 0.156],
                'imu_rpy': [0.0, 0.0, 0.0],
            }]
        )
    ])
