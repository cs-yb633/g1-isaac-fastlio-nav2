# Progress Log

## 阶段 0：ROS 2 / Nav2 基础链路

完成内容：

- Ubuntu + ROS 2 Humble 环境搭建；
- TurtleBot3 + Gazebo 仿真；
- Cartographer 建图；
- 地图导出；
- Nav2 + AMCL 定位；
- RViz 设置初始位姿；
- 发送 Nav2 Goal；
- 完成近距离、远距离、转弯导航测试。

收获：

- 理解 `/scan`、`/odom`、`/tf`、`map`、`odom`、`base_link` 的基础关系；
- 理解 Nav2 生命周期节点；
- 初步掌握 RViz 调试方法。

## 阶段 1：G1 ROS 2 可视化与 Gazebo 尝试

完成内容：

- 阅读 Unitree G1 相关资料；
- 获取并查看 G1 URDF；
- 在 RViz2 中显示 G1 模型；
- 尝试 Gazebo 中加载 G1；
- 编写早期 fake controller / joint state / TF 测试节点。

问题：

- Gazebo GUI 加载 G1 不稳定；
- GUI 容易卡顿或崩溃；
- 仿真传感器和运动控制链路不够顺畅。

结论：

- 转向 Isaac Sim 作为主要仿真环境。

## 阶段 2：Isaac Sim + Carter 代理

完成内容：

- 使用 Isaac Sim Nova Carter ROS2 Navigation Sample；
- 确认 ROS2 Bridge 正常；
- 确认 `/front_3d_lidar/lidar_points`、`/chassis/imu`、`/chassis/odom`、`/cmd_vel`；
- 导入 G1 URDF；
- 将 G1 绑定到 Carter；
- 隐藏 Carter，保留运动能力；
- 保存场景。

关键结果：

```text
/front_3d_lidar/lidar_points 约 37 Hz
/chassis/imu                 约 37 Hz
/chassis/odom                约 38 Hz
```

## 阶段 3：G1 上层接口抽象

完成内容：

- 编写 `g1_proxy_bridge`；
- 将 Carter 原始话题转换为 `/g1/*`；
- 发布 TF：`odom → g1_base_link`；
- 发布静态 TF：`g1_base_link → g1_lidar_link`、`g1_base_link → g1_imu_link`；
- 键盘控制 `/g1/cmd_vel`，转发到 Isaac Sim `/cmd_vel`。

关键结果：

```text
/g1/cmd_vel
/g1/odom
/g1/lidar_points
/g1/imu
```

## 阶段 4：FAST-LIO 建图测试

完成内容：

- 编译 FAST-LIO ROS2 相关分支；
- 使用 `/g1/lidar_points` + `/g1/imu` 输入；
- 在 Isaac Sim 中移动 G1；
- FAST-LIO 输出点云地图和定位结果。

观察到输出：

```text
/Laser_map_1
/Odometry_loc
/cloud_registered_1
/cloud_registered_body_1
/path_1
```

记录 bag：

```text
mapping_01: 约 304.89 s，约 777.2 MiB
test_01:    约 47.65 s，约 131.3 MiB
```

## 阶段 5：下一步计划

待完成：

- 将 FAST-LIO 定位输出统一为 Nav2 可用的 TF；
- 明确 `map → odom → g1_base_link` 关系；
- 配置 Nav2 最小导航闭环；
- 在 RViz 中发送 2D Nav Goal；
- Isaac Sim 中 G1 完成 A → B 目标点导航；
- 梳理实机迁移路线。
