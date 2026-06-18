# 06 常见问题排查

## 1. ROS 2 看不到 Isaac Sim 话题

检查 Isaac Sim 是否点击 Play：

```bash
ros2 topic list
```

检查 `ROS_DOMAIN_ID`：

```bash
echo $ROS_DOMAIN_ID
```

Isaac Sim 和 ROS 2 终端必须一致。

## 2. `/g1/*` 没有数据

先确认 Carter 原始数据是否存在：

```bash
ros2 topic hz /front_3d_lidar/lidar_points
ros2 topic hz /chassis/imu
ros2 topic hz /chassis/odom
```

如果原始数据有，而 `/g1/*` 没有，检查：

```bash
ros2 node list
ros2 node info /g1_proxy_bridge
```

## 3. 键盘控制无效

确认 teleop 是否 remap 到 `/g1/cmd_vel`：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/g1/cmd_vel
```

检查桥是否转发到 `/cmd_vel`：

```bash
ros2 topic echo /cmd_vel
```

## 4. TF 报错

检查：

```bash
ros2 run tf2_ros tf2_echo odom g1_base_link
ros2 run tf2_ros tf2_echo g1_base_link g1_lidar_link
ros2 run tf2_ros tf2_echo g1_base_link g1_imu_link
```

如果 `/tf_static` 没有输出，检查 `g1_proxy_bridge` 是否正常启动。

## 5. FAST-LIO 地图漂移

重点检查：

1. LiDAR 与 IMU 的 frame 是否正确；
2. 外参是否正确；
3. Isaac Sim 是否使用稳定时间；
4. 是否机器人运动太快；
5. 点云频率是否稳定；
6. IMU 角速度和线加速度是否合理。

## 6. Nav2 不动

逐项检查：

```bash
ros2 lifecycle nodes
ros2 topic echo /g1/cmd_vel
ros2 topic echo /cmd_vel
ros2 run tf2_ros tf2_echo map g1_base_link
ros2 run tf2_ros tf2_echo odom g1_base_link
```

Nav2 常见失败点：

1. lifecycle 没有 active；
2. TF 树断裂；
3. 没有地图；
4. costmap 没有障碍物数据；
5. controller 输出话题没有连到机器人；
6. 初始位姿不稳定。

## 7. GitHub 仓库过大

不要上传：

```text
rosbag
pcd 点云地图
Isaac Sim usd 大场景
build/install/log
```

建议只上传：

```text
代码
配置模板
文档
截图
小型示例参数
```


## Real G1 DDS point cloud is zero

Current project decision: treat WiFi as useful for `ping` / `ssh`, but prefer wired connection for DDS sensor data.

Checklist:

```bash
ip addr show enp6s0
printenv | grep ROS_DOMAIN_ID
ros2 topic list
ros2 topic hz <pointcloud_topic>
```

Do not start official navigation or locomotion commands while debugging DDS reception.

## Accidentally connected a motion command path

Stop immediately:

```bash
Ctrl+C
```

Then inspect running nodes:

```bash
ros2 node list
ros2 topic info /cmd_vel
ros2 topic info /g1/cmd_vel
```

During v0.2, real-robot work should stay read-only.
