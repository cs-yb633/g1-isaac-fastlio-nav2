# 05 Nav2 对接计划

## 目标

在不使用 AMCL / SLAM Toolbox 2D 定位的情况下，将 FAST-LIO 的 3D LiDAR + IMU 定位结果接入 Nav2，实现 Isaac Sim 中 G1 的目标点导航。

## 核心问题

Nav2 需要稳定的 2D 导航输入：

```text
map → odom → base_link
```

其中：

- `map → odom` 通常由定位模块提供；
- `odom → base_link` 通常由里程计模块提供；
- costmap 需要障碍物输入；
- controller 输出 `/cmd_vel`。

本项目当前已有：

```text
/g1/odom
/g1/lidar_points
/g1/imu
FAST-LIO 输出 /Odometry_loc
```

需要进一步决定：

1. FAST-LIO 输出是否作为 `map → g1_base_link`；
2. 是否需要拆成 `map → odom` + `odom → g1_base_link`；
3. Nav2 costmap 使用 3D 点云还是预处理后的 2D/voxel obstacle layer；
4. Nav2 输出 `/cmd_vel` 是否 remap 到 `/g1/cmd_vel`。

## 推荐路线

### 阶段 1：只验证定位 TF

目标：让 RViz 中 G1 的定位结果稳定。

```text
FAST-LIO /Odometry_loc
        ↓
转换 TF
        ↓
map 或 camera_init → g1_base_link
```

检查：

```bash
ros2 run tf2_ros tf2_echo map g1_base_link
```

或：

```bash
ros2 run tf2_ros tf2_echo camera_init g1_base_link
```

### 阶段 2：统一 Nav2 需要的 TF 树

目标 TF：

```text
map → odom → g1_base_link → g1_lidar_link
                         → g1_imu_link
```

如果 FAST-LIO 直接输出 `map → g1_base_link`，而 `/g1/odom` 也在发布 `odom → g1_base_link`，则需要计算并发布：

```text
map → odom
```

避免同时发布两个互相冲突的 `base_link` 位姿。

### 阶段 3：最小 Nav2 bringup

先关闭复杂层，只保留最小闭环：

```text
planner_server
controller_server
bt_navigator
behavior_server
map_server 或静态地图
```

控制输出：

```bash
/cmd_vel → /g1/cmd_vel
```

或者在 Nav2 参数中直接设定输出为 `/g1/cmd_vel`。

### 阶段 4：costmap 处理

Nav2 默认更习惯 2D costmap。由于本项目坚持 3D 点云路线，可以考虑：

1. 使用 voxel layer 接收 PointCloud2；
2. 使用点云障碍层生成 2D costmap；
3. 不将 3D LiDAR 退化成 `/scan`，但允许 costmap 内部做高度过滤；
4. 后续再考虑更完整的 3D navigation。

## 最小闭环目标

第一版 Nav2 闭环不追求复杂避障，只追求：

```text
RViz 发送 2D Nav Goal
        ↓
Nav2 规划路径
        ↓
Nav2 输出速度
        ↓
/g1/cmd_vel
        ↓
Isaac Sim 中 G1 代理移动
        ↓
FAST-LIO 定位持续更新
```

## 成功标志

- RViz 中机器人位姿稳定；
- TF 树无断裂；
- Nav2 lifecycle 节点 active；
- 发送目标点后 `/g1/cmd_vel` 有输出；
- Isaac Sim 中 G1 能向目标移动；
- 运动过程中 FAST-LIO 不丢定位。
