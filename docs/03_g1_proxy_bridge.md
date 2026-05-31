# 03 g1_proxy_bridge 说明

## 功能定位

`g1_proxy_bridge` 是本项目的核心自写 ROS 2 包，用来把 Isaac Sim 中 Carter 的话题抽象成 G1 上层接口。

## 输入与输出

### 输入

```text
/g1/cmd_vel                         geometry_msgs/Twist
/chassis/odom                       nav_msgs/Odometry
/front_3d_lidar/lidar_points        sensor_msgs/PointCloud2
/chassis/imu                        sensor_msgs/Imu
```

### 输出

```text
/cmd_vel                            geometry_msgs/Twist
/g1/odom                            nav_msgs/Odometry
/g1/lidar_points                    sensor_msgs/PointCloud2
/g1/imu                             sensor_msgs/Imu
/tf                                 odom → g1_base_link
/tf_static                          g1_base_link → g1_lidar_link
/tf_static                          g1_base_link → g1_imu_link
```

## 工作逻辑

```text
teleop / Nav2
    ↓
/g1/cmd_vel
    ↓
g1_proxy_bridge
    ↓
/cmd_vel
    ↓
Isaac Sim Carter
```

传感器方向：

```text
Isaac Sim Carter sensors
    ↓
/chassis/odom, /front_3d_lidar/lidar_points, /chassis/imu
    ↓
g1_proxy_bridge
    ↓
/g1/odom, /g1/lidar_points, /g1/imu
```

## 编译

```bash
cd ~/mayibo/ws_g1
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select g1_proxy_bridge
source install/setup.bash
```

## 启动

```bash
ros2 launch g1_proxy_bridge g1_proxy_bridge.launch.py
```

## 检查

```bash
ros2 topic list -t | grep /g1
ros2 topic hz /g1/lidar_points
ros2 topic hz /g1/imu
ros2 topic hz /g1/odom
```

检查 frame：

```bash
ros2 topic echo /g1/lidar_points --once | grep frame_id
ros2 topic echo /g1/imu --once | grep frame_id
```

预期：

```text
g1_lidar_link
g1_imu_link
```

检查 TF：

```bash
ros2 run tf2_ros tf2_echo odom g1_base_link
ros2 run tf2_ros tf2_echo g1_base_link g1_lidar_link
ros2 run tf2_ros tf2_echo g1_base_link g1_imu_link
```

## 参数

主要参数见：

```text
launch/g1_proxy_bridge.launch.py
```

常用参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `g1_cmd_vel_topic` | `/g1/cmd_vel` | 上层控制输入 |
| `carter_cmd_vel_topic` | `/cmd_vel` | Isaac Sim Carter 控制入口 |
| `carter_odom_topic` | `/chassis/odom` | Carter 里程计 |
| `carter_lidar_topic` | `/front_3d_lidar/lidar_points` | Carter 3D LiDAR |
| `carter_imu_topic` | `/chassis/imu` | Carter IMU |
| `g1_odom_topic` | `/g1/odom` | G1 抽象里程计 |
| `g1_lidar_topic` | `/g1/lidar_points` | G1 抽象点云 |
| `g1_imu_topic` | `/g1/imu` | G1 抽象 IMU |
| `odom_frame` | `odom` | 里程计坐标系 |
| `base_frame` | `g1_base_link` | G1 基座坐标系 |
| `lidar_frame` | `g1_lidar_link` | G1 雷达坐标系 |
| `imu_frame` | `g1_imu_link` | G1 IMU 坐标系 |
