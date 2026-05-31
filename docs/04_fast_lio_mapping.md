# 04 FAST-LIO 建图流程

## 目标

使用 Isaac Sim 发布的 3D LiDAR 与 IMU 数据，通过 `g1_proxy_bridge` 转换成 `/g1/*` 后，接入 FAST-LIO 完成建图与定位输出。

## 输入话题

FAST-LIO 应使用：

```text
/g1/lidar_points    sensor_msgs/PointCloud2
/g1/imu             sensor_msgs/Imu
```

而不是：

```text
/scan
```

本项目路线明确不使用 `pointcloud_to_laserscan`。

## 检查传感器数据

```bash
ros2 topic hz /g1/lidar_points
ros2 topic hz /g1/imu
ros2 topic echo /g1/lidar_points --once | grep frame_id
ros2 topic echo /g1/imu --once | grep frame_id
```

预期：

```text
/g1/lidar_points 约 35~40 Hz
/g1/imu          约 35~40 Hz
frame_id: g1_lidar_link
frame_id: g1_imu_link
```

## FAST-LIO 配置

不同 FAST-LIO 分支的参数文件格式不完全一致，本仓库提供的是模板：

```text
config/fast_lio/g1_isaac_fastlio.template.yaml
```

核心要点：

```yaml
common:
  lid_topic: "/g1/lidar_points"
  imu_topic: "/g1/imu"
```

外参需要根据 Isaac Sim 中 LiDAR 与 IMU 相对 `g1_base_link` 的实际位置调整。

项目中曾经记录过的近似位置：

```text
g1_base_link → g1_lidar_link: [-0.232, 0.000, 0.526]
g1_base_link → g1_imu_link:   [-0.218, 0.024, 0.156]
```

注意：FAST-LIO 通常需要 LiDAR 与 IMU 之间的外参，而不是它们分别相对于 base 的位置。需要根据具体 FAST-LIO 分支确认参数含义。

## 运行后检查

```bash
ros2 topic list | grep -E "Odometry|cloud|Laser|path"
```

曾经观察到的输出：

```text
/Laser_map_1
/Odometry_loc
/cloud_registered_1
/cloud_registered_body_1
/path_1
```

检查里程计：

```bash
ros2 topic echo /Odometry_loc --once
```

检查点云：

```bash
ros2 topic hz /cloud_registered_1
```

## 录包

```bash
./src/g1-isaac-fastlio-nav2/scripts/record_bag.sh mapping_01
```

默认记录：

```text
/g1/lidar_points
/g1/imu
/g1/odom
/g1/cmd_vel
/tf
/tf_static
/clock
```

## 常见问题

### 1. FAST-LIO 没有输出

检查：

1. `/g1/lidar_points` 是否有频率；
2. `/g1/imu` 是否有频率；
3. frame_id 是否和配置一致；
4. 是否使用了仿真时间；
5. FAST-LIO 参数文件是否读取成功。

### 2. 地图严重扭曲

可能原因：

1. LiDAR / IMU 时间不同步；
2. 外参错误；
3. IMU 坐标方向不符合 FAST-LIO 预期；
4. Isaac Sim 时间与 ROS 时间设置不一致；
5. 机器人运动过快或旋转过猛。

### 3. 点云看不到

检查 RViz Fixed Frame 是否设置正确，例如：

```text
odom
map
camera_init
```

具体取决于 FAST-LIO 输出坐标系。
