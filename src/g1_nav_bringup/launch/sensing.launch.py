"""Read-only odometry TF and point-cloud conversion bringup."""

import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _validated_sensor_tf(context):
    enabled = LaunchConfiguration("publish_sensor_tf").perform(context).lower()
    if enabled not in ("true", "1", "yes", "on"):
        return [
            LogInfo(
                msg=(
                    "WARNING: Sensor TF publication is disabled. /scan_raw cannot be produced "
                    "until a verified transform to livox_frame is supplied explicitly."
                )
            )
        ]

    required = (
        "sensor_parent_frame",
        "sensor_x",
        "sensor_y",
        "sensor_z",
        "sensor_roll",
        "sensor_pitch",
        "sensor_yaw",
    )
    values = {name: LaunchConfiguration(name).perform(context) for name in required}
    missing = [name for name, value in values.items() if not value.strip()]
    if missing:
        raise RuntimeError(
            "publish_sensor_tf:=true requires verified explicit values for: "
            + ", ".join(missing)
        )
    parent_frame = values["sensor_parent_frame"]
    if parent_frame.startswith("/") or parent_frame == "livox_frame":
        raise RuntimeError(
            "sensor_parent_frame must be a distinct TF frame without a leading '/'"
        )
    for name in required[1:]:
        try:
            number = float(values[name])
        except ValueError as error:
            raise RuntimeError(f"{name} must be a finite numeric value") from error
        if not math.isfinite(number):
            raise RuntimeError(f"{name} must be finite")
    return []


def generate_launch_description():
    config = str(
        Path(get_package_share_directory("g1_nav_bringup"))
        / "config"
        / "pointcloud_to_laserscan.yaml"
    )
    arguments = [
        DeclareLaunchArgument("publish_sensor_tf", default_value="false"),
        DeclareLaunchArgument("sensor_parent_frame", default_value=""),
        DeclareLaunchArgument("sensor_x", default_value=""),
        DeclareLaunchArgument("sensor_y", default_value=""),
        DeclareLaunchArgument("sensor_z", default_value=""),
        DeclareLaunchArgument("sensor_roll", default_value=""),
        DeclareLaunchArgument("sensor_pitch", default_value=""),
        DeclareLaunchArgument("sensor_yaw", default_value=""),
    ]
    sensor_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="verified_livox_static_tf",
        condition=IfCondition(LaunchConfiguration("publish_sensor_tf")),
        arguments=[
            "--x", LaunchConfiguration("sensor_x"),
            "--y", LaunchConfiguration("sensor_y"),
            "--z", LaunchConfiguration("sensor_z"),
            "--roll", LaunchConfiguration("sensor_roll"),
            "--pitch", LaunchConfiguration("sensor_pitch"),
            "--yaw", LaunchConfiguration("sensor_yaw"),
            "--frame-id", LaunchConfiguration("sensor_parent_frame"),
            "--child-frame-id", "livox_frame",
        ],
    )
    return LaunchDescription(
        arguments
        + [
            OpaqueFunction(function=_validated_sensor_tf),
            Node(
                package="g1_nav_adapter",
                executable="g1_odom_tf_node",
                name="g1_odom_tf",
                output="screen",
            ),
            sensor_tf,
            Node(
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                output="screen",
                parameters=[config],
                remappings=[
                    ("cloud_in", "/utlidar/cloud_livox_mid360"),
                    ("scan", "/scan_raw"),
                ],
            ),
        ]
    )
