# 依赖锁定

首次恢复基线锁定于 2026-08-31。

| 依赖 | 固定值 | 上游 |
|---|---|---|
| ROS 基础镜像（amd64） | `ros:humble-ros-base-jammy@sha256:2a7ca548c7f0f87bc6393ee161dea3283e1c6fa280916f8944b1afadde2d26ec` | https://hub.docker.com/_/ros |
| Unitree ROS 2 | `668d1ec5a05d1c38d3306bdca7d59f2ba3581a88` | https://github.com/unitreerobotics/unitree_ros2 |
| CycloneDDS 0.10.x | `5041f3560c088c99e5088b2b8520b69169621196` | https://github.com/eclipse-cyclonedds/cyclonedds |
| ROS 2 发行版 | Humble / Ubuntu 22.04 Jammy | https://docs.ros.org/en/humble/ |

Unitree 官方 `unitree_ros2` 文档要求 CycloneDDS 0.10.x，并推荐 Ubuntu 22.04 + ROS 2 Humble。其仓库主分支中的 `setup.sh` 仍包含 Foxy 和示例网卡名，故本项目不直接 source 该文件，而是在容器入口中显式加载 Humble、消息工作空间和当前网卡配置。

SLAM Toolbox、Nav2、RViz2 和辅助 ROS 包通过该固定 Jammy 镜像的 ROS apt 仓库安装。构建日志需记录实际 apt 包版本；升级基础镜像或上述提交必须单独验证实机 DDS 兼容性。
