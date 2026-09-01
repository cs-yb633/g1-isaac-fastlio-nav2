FROM ros:humble-ros-base-jammy@sha256:2a7ca548c7f0f87bc6393ee161dea3283e1c6fa280916f8944b1afadde2d26ec

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG DEBIAN_FRONTEND=noninteractive
ARG LOCAL_UID=1001
ARG LOCAL_GID=1001
ARG UNITREE_ROS2_REV=668d1ec5a05d1c38d3306bdca7d59f2ba3581a88
ARG CYCLONEDDS_REV=5041f3560c088c99e5088b2b8520b69169621196

ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    git \
    iproute2 \
    iputils-ping \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-pointcloud-to-laserscan \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-robot-state-publisher \
    ros-humble-rosidl-generator-dds-idl \
    ros-humble-rviz2 \
    ros-humble-slam-toolbox \
    ros-humble-teleop-twist-keyboard \
    ros-humble-tf2-tools \
    ros-humble-xacro \
    && rm -rf /var/lib/apt/lists/*

# Unitree publishes ROS-compatible DDS types but requires CycloneDDS 0.10.x.
# Build the exact official message workspace against a pinned CycloneDDS revision.
RUN git clone https://github.com/unitreerobotics/unitree_ros2.git /opt/unitree_ros2 \
    && git -C /opt/unitree_ros2 checkout "${UNITREE_ROS2_REV}" \
    && git clone https://github.com/eclipse-cyclonedds/cyclonedds.git \
        /opt/unitree_ros2/cyclonedds_ws/src/cyclonedds \
    && git -C /opt/unitree_ros2/cyclonedds_ws/src/cyclonedds checkout "${CYCLONEDDS_REV}" \
    && source /opt/ros/humble/setup.bash \
    && export LD_LIBRARY_PATH=/opt/ros/humble/lib:${LD_LIBRARY_PATH:-} \
    && cd /opt/unitree_ros2/cyclonedds_ws \
    && colcon build --merge-install --packages-select cyclonedds \
    && source install/setup.bash \
    && colcon build --merge-install --packages-select unitree_go unitree_hg unitree_api \
    && rm -rf build log .git src/cyclonedds/.git

RUN groupadd --gid "${LOCAL_GID}" developer \
    && useradd --uid "${LOCAL_UID}" --gid "${LOCAL_GID}" --create-home --shell /bin/bash developer

COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/g1-nav-entrypoint

USER developer
WORKDIR /workspace

ENTRYPOINT ["/usr/local/bin/g1-nav-entrypoint"]
CMD ["bash"]
