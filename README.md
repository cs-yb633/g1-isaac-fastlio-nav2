# Unitree G1 Isaac Sim FAST-LIO Nav2

> 基于 **ROS 2 Humble + Isaac Sim** 的 Unitree G1 导航仿真流程。当前阶段采用 **G1 作为上层导航主体 + Carter 作为隐藏运动代理** 的方案，通过 `g1_proxy_bridge` 将 Isaac Sim 中 Carter 的传感器与运动接口抽象为 `/g1/*`，并接入 **3D LiDAR + IMU + FAST-LIO** 完成建图/定位，为后续接入 Nav2 做目标点导航打基础。

## 1. 项目状态

当前仓库是第一版开源整理，重点沉淀已经跑通和正在打通的流程：

- [x] ROS 2 Humble 基础导航链路学习与验证
- [x] TurtleBot3 / Gazebo / Cartographer / Nav2 入门闭环
- [x] Isaac Sim 中加载 Nova Carter ROS2 Navigation Sample
- [x] Unitree G1 URDF 导入 Isaac Sim
- [x] G1 绑定 Carter，Carter 作为隐藏运动代理
- [x] 编写 `g1_proxy_bridge`，统一抽象 `/g1/*` 上层接口
- [x] 发布 `/g1/cmd_vel`、`/g1/odom`、`/g1/lidar_points`、`/g1/imu`
- [x] 使用 FAST-LIO 对 3D LiDAR + IMU 做建图测试
- [ ] 将 FAST-LIO 定位结果统一接入 `/g1/odom` 或 `/g1/pose`
- [ ] 将定位结果接入 Nav2，完成 Isaac Sim 中 A → B 目标点导航
- [ ] 迁移到 Unitree G1 实机

## 2. 为什么采用 Carter 代理方案

当前目标不是实现完整的 G1 双足动力学控制，而是先验证“感知—建图—定位—导航”的上层软件链路。

因此本项目采用：

```text
Isaac Sim Nova Carter Sample
        ↓
Carter 负责底层运动与仿真传感器
        ↓
G1 模型绑定到 Carter 并作为可见主体
        ↓
g1_proxy_bridge 将 Carter 接口抽象成 /g1/*
        ↓
FAST-LIO 使用 /g1/lidar_points + /g1/imu 建图定位
        ↓
后续 Nav2 使用 FAST-LIO 位姿结果进行导航
```

这种方式的优点是：

1. 避开早期直接做双足步态控制的复杂性；
2. 先打通 ROS 2 导航上层架构；
3. 方便后续把 `/g1/*` 接口迁移到真实 Unitree G1；
4. 保持 3D LiDAR + IMU 路线，不退化成 2D `/scan`。

## 3. 系统架构

```text
┌─────────────────────────────────────────────┐
│ Isaac Sim                                   │
│                                             │
│  Nova Carter ROS2 Navigation Sample         │
│    ├── /cmd_vel                             │
│    ├── /chassis/odom                        │
│    ├── /front_3d_lidar/lidar_points         │
│    └── /chassis/imu                         │
│                                             │
│  Unitree G1 Visual Model                    │
│    └── attached to Carter base_link         │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ ROS 2 Humble                                │
│                                             │
│  g1_proxy_bridge                            │
│    ├── /g1/cmd_vel       → /cmd_vel          │
│    ├── /chassis/odom     → /g1/odom          │
│    ├── lidar points      → /g1/lidar_points  │
│    ├── imu               → /g1/imu           │
│    └── TF: odom → g1_base_link              │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ FAST-LIO                                    │
│  input:  /g1/lidar_points + /g1/imu         │
│  output: /Odometry_loc, /cloud_registered_* │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│ Nav2 Roadmap                                │
│  使用 FAST-LIO 位姿结果替代 AMCL             │
│  实现 Isaac Sim 中 2D Nav Goal A → B 导航    │
└─────────────────────────────────────────────┘
```

## 4. 推荐环境

| 项目 | 建议版本 / 状态 |
|---|---|
| OS | Ubuntu 22.04 |
| ROS | ROS 2 Humble |
| Simulator | NVIDIA Isaac Sim |
| GPU | 建议 NVIDIA RTX 3090 或同级以上 |
| Workspace | `~/mayibo/ws_g1` |
| ROS_DOMAIN_ID | 项目中常用 `42` |
| LiDAR topic | `/front_3d_lidar/lidar_points` → `/g1/lidar_points` |
| IMU topic | `/chassis/imu` → `/g1/imu` |

> 注意：Isaac Sim 建议从干净终端启动，不要在 conda/ROS 环境已经污染的终端里直接启动。

## 5. 仓库结构

```text
g1-isaac-fastlio-nav2/
├── README.md
├── LICENSE
├── third_party.md
├── .gitignore
├── docs/
│   ├── 00_project_overview.md
│   ├── 01_environment_setup.md
│   ├── 02_isaac_sim_scene_setup.md
│   ├── 03_g1_proxy_bridge.md
│   ├── 04_fast_lio_mapping.md
│   ├── 05_nav2_integration_plan.md
│   ├── 06_troubleshooting.md
│   └── progress_log.md
├── src/
│   └── g1_proxy_bridge/
├── launch/
│   └── g1_proxy_bridge.launch.py
├── config/
│   ├── fast_lio/
│   └── nav2/
├── scripts/
│   ├── check_topics.sh
│   ├── check_tf.sh
│   ├── record_bag.sh
│   ├── setup_workspace.sh
│   └── push_to_github_template.sh
└── assets/
    └── images/
```

## 6. 快速开始

### 6.1 克隆仓库到 ROS 2 工作空间

```bash
mkdir -p ~/mayibo/ws_g1/src
cd ~/mayibo/ws_g1/src
git clone <your-repo-url> g1-isaac-fastlio-nav2
```

如果你是先下载 zip，可以把整个仓库解压到：

```bash
~/mayibo/ws_g1/src/g1-isaac-fastlio-nav2
```

### 6.2 编译 `g1_proxy_bridge`

```bash
cd ~/mayibo/ws_g1
source /opt/ros/humble/setup.bash
colcon build --symlink-install --packages-select g1_proxy_bridge
source install/setup.bash
```

### 6.3 启动 Isaac Sim 场景

1. 从干净终端启动 Isaac Sim；
2. 打开保存好的 G1 + Carter 代理场景；
3. 确认 ROS2 Bridge extension 已启用；
4. 点击 Play；
5. 在 ROS 2 终端检查 Carter 原始话题：

```bash
ros2 topic list
ros2 topic hz /front_3d_lidar/lidar_points
ros2 topic hz /chassis/imu
ros2 topic hz /chassis/odom
```

### 6.4 启动 G1 代理桥

```bash
cd ~/mayibo/ws_g1
source install/setup.bash
ros2 launch g1_proxy_bridge g1_proxy_bridge.launch.py
```

或者直接：

```bash
ros2 run g1_proxy_bridge g1_proxy_bridge_node
```

### 6.5 检查 `/g1/*` 话题

```bash
./src/g1-isaac-fastlio-nav2/scripts/check_topics.sh
```

预期看到：

```text
/g1/cmd_vel
/g1/odom
/g1/lidar_points
/g1/imu
```

并且频率大致为：

```text
/g1/lidar_points 约 35~40 Hz
/g1/imu          约 35~40 Hz
/g1/odom         约 35~40 Hz
```

### 6.6 键盘控制

安装：

```bash
sudo apt install ros-humble-teleop-twist-keyboard
```

启动：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/g1/cmd_vel
```

此时命令链路为：

```text
teleop_twist_keyboard
        ↓
/g1/cmd_vel
        ↓
g1_proxy_bridge
        ↓
/cmd_vel
        ↓
Isaac Sim Carter
        ↓
G1 跟随运动
```

## 7. FAST-LIO 建图

本仓库不直接包含第三方 FAST-LIO 源码，请按照你使用的 FAST-LIO / FAST-LIO2 / FAST_LIO_LOCALIZATION_HUMANOID 版本自行放置第三方仓库。

核心输入应改为：

```text
LiDAR: /g1/lidar_points
IMU:   /g1/imu
```

可参考模板：

```text
config/fast_lio/g1_isaac_fastlio.template.yaml
```

建图成功后通常可以检查：

```bash
ros2 topic list | grep -E "Odometry|cloud|Laser|path"
ros2 topic echo /Odometry_loc --once
ros2 topic hz /cloud_registered_1
```

项目中曾经观察到的 FAST-LIO 输出包括：

```text
/Laser_map_1
/Odometry_loc
/cloud_registered_1
/cloud_registered_body_1
/path_1
```

## 8. Nav2 对接路线

当前建议路线：

```text
FAST-LIO
  ↓
/Odometry_loc 或等价定位输出
  ↓
统一转换为 map → odom 或 /g1/odom
  ↓
Nav2 planner/controller/bt_navigator
  ↓
/cmd_vel 或 /g1/cmd_vel
  ↓
Isaac Sim 中 G1 代理运动
```

详细计划见：

```text
docs/05_nav2_integration_plan.md
```

## 9. 常用检查命令

```bash
# 查看话题
ros2 topic list -t

# 检查频率
ros2 topic hz /g1/lidar_points
ros2 topic hz /g1/imu
ros2 topic hz /g1/odom

# 检查 frame_id
ros2 topic echo /g1/lidar_points --once | grep frame_id
ros2 topic echo /g1/imu --once | grep frame_id

# 检查 TF
ros2 run tf2_ros tf2_echo odom g1_base_link
ros2 run tf2_ros tf2_echo g1_base_link g1_lidar_link
ros2 run tf2_ros tf2_echo g1_base_link g1_imu_link
```

## 10. 参考资料

见 [`third_party.md`](./third_party.md)。

## 11. License

本仓库中自写代码和文档默认采用 MIT License。第三方资源、模型、示例场景、论文代码等遵循其原始许可证。
