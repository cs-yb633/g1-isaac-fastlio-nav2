# Unitree G1 Isaac Sim FAST-LIO Nav2

> 基于 **ROS 2 Humble + Isaac Sim** 的 Unitree G1 导航仿真与实机前期数据链路整理。当前仓库采用两条并行主线：
>
> 1. **仿真主线**：G1 作为上层导航主体，Carter 作为隐藏运动代理，通过 `g1_proxy_bridge` 将 Isaac Sim 中 Carter 的传感器与运动接口抽象为 `/g1/*`，接入 **3D LiDAR + IMU + FAST-LIO** 做建图/定位。
> 2. **实机主线 v0.2**：先不让机器人移动，优先打通 **5060Ti 实机电脑 ↔ G1 机载电脑** 的有线 DDS/ROS2 数据接收、录包、实时点云与地图生成，为后续 Nav2 和真实底盘接口做准备。

> Safety note: 实机阶段默认只做只读数据采集与建图，不运行会让 G1 移动的官方导航、`g1_loco_client move`、`set_velocity` 或任何速度控制命令。

## 1. 项目状态

### v0.1 已完成：Isaac Sim G1 代理仿真链路

- [x] ROS 2 Humble 基础导航链路学习与验证
- [x] TurtleBot3 / Gazebo / Cartographer / Nav2 入门闭环
- [x] Isaac Sim 中加载 Nova Carter ROS2 Navigation Sample
- [x] Unitree G1 URDF 导入 Isaac Sim
- [x] G1 绑定 Carter，Carter 作为隐藏运动代理
- [x] 编写 `g1_proxy_bridge`，统一抽象 `/g1/*` 上层接口
- [x] 发布 `/g1/cmd_vel`、`/g1/odom`、`/g1/lidar_points`、`/g1/imu`
- [x] 使用 FAST-LIO 对 3D LiDAR + IMU 做建图测试

### v0.2 新增：实机只读数据链路与安全路线

- [x] 明确 3090 与 5060Ti 的分工：3090 做 Isaac Sim/离线仿真，5060Ti 连接 G1 实机
- [x] 明确实机阶段先做有线 DDS 接收、录 bag、点云显示、2D 地图生成
- [x] 将 WiFi 作为 ssh/ping 辅助连接，DDS 点云默认切到有线连接排查
- [x] 新增实机安全说明：不让机器人动，不运行官方移动/导航命令
- [x] 新增实机只读检查脚本与录包脚本模板
- [x] 新增实机阶段文档：有线 DDS、数据采集、官方 SLAM → 2D map → Nav2 路线
- [ ] 将 FAST-LIO 定位结果统一接入 `/g1/odom` 或 `/g1/pose`
- [ ] 将定位结果接入 Nav2，完成 Isaac Sim 中 A → B 目标点导航
- [ ] 在实机上完成只读点云/IMU/里程计 rosbag 记录
- [ ] 基于实机数据完成 3D/2D 地图生成
- [ ] 后续再接 Nav2 `/cmd_vel` 到 G1 LocoClient 执行层

## 2. 设计原则

当前项目不是直接做完整的 G1 双足动力学控制，而是先验证“感知—建图—定位—导航”的上层软件链路。

核心原则：

1. **先仿真、再实机**：仿真中用 Carter 代理运动，实机中先只读采集数据；
2. **先感知建图、后导航控制**：实机阶段暂不碰运动控制；
3. **坚持 3D LiDAR + IMU 路线**：不把主线退化成 `pointcloud_to_laserscan` 的 2D `/scan`；
4. **接口统一**：仿真与实机都尽量向 `/g1/*` 接口靠拢；
5. **安全优先**：真实 G1 阶段任何移动命令都必须单独确认、单独隔离。

## 3. 系统架构

### 3.1 仿真链路

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

### 3.2 实机 v0.2 链路

```text
Unitree G1 onboard computer
  ├── unitree_sdk2-main
  ├── unitree_sdk2_python
  └── sensors / official SLAM data
          ↓ wired network / DDS
5060Ti lab workstation
  ├── ~/G1_SLAM
  ├── g1_slam workspace
  ├── ROS 2 data receive
  ├── rosbag record
  ├── point cloud / map visualization
  └── 2D pgm/yaml map generation
          ↓ later
Nav2 planning
          ↓ later, after safety isolation
G1 locomotion execution layer
```

## 4. 推荐环境

| 场景 | 推荐配置 / 状态 |
|---|---|
| 仿真电脑 | RTX 3090 workstation |
| 实机电脑 | 5060Ti lab workstation |
| OS | Ubuntu 22.04 |
| ROS | ROS 2 Humble |
| Simulator | NVIDIA Isaac Sim |
| 仿真工作空间 | `~/mayibo/ws_g1` |
| 实机工作空间 | `~/G1_SLAM` / `g1_slam` |
| 常用 ROS_DOMAIN_ID | 项目中常用 `42`，但以实际 DDS 配置为准 |
| 实机网络 | 优先有线，例如 `enp6s0` |
| 仿真 LiDAR topic | `/front_3d_lidar/lidar_points` → `/g1/lidar_points` |
| 仿真 IMU topic | `/chassis/imu` → `/g1/imu` |

> Isaac Sim 建议从干净终端启动，不要在 conda/ROS 环境已经污染的终端里直接启动。

## 5. 仓库结构

```text
g1-isaac-fastlio-nav2/
├── README.md
├── LICENSE
├── third_party.md
├── ROADMAP.md
├── docs/
│   ├── 00_project_overview.md
│   ├── 01_environment_setup.md
│   ├── 02_isaac_sim_scene_setup.md
│   ├── 03_g1_proxy_bridge.md
│   ├── 04_fast_lio_mapping.md
│   ├── 05_nav2_integration_plan.md
│   ├── 06_troubleshooting.md
│   ├── 07_real_robot_wired_dds.md
│   ├── 08_real_robot_data_pipeline.md
│   ├── 09_release_v0_2.md
│   ├── 10_safety_notes.md
│   └── progress_log.md
├── src/
│   └── g1_proxy_bridge/
├── launch/
│   └── g1_proxy_bridge.launch.py
├── config/
│   ├── fast_lio/
│   ├── nav2/
│   └── unitree/
├── scripts/
│   ├── check_topics.sh
│   ├── check_tf.sh
│   ├── record_bag.sh
│   ├── real_g1_network_readonly_check.sh
│   ├── record_real_g1_bag_readonly.sh
│   └── push_v02_update.sh
└── assets/
    └── images/
```

## 6. 快速开始：仿真代理桥

### 6.1 克隆仓库到 ROS 2 工作空间

```bash
mkdir -p ~/mayibo/ws_g1/src
cd ~/mayibo/ws_g1/src
git clone https://github.com/cs-yb633/g1-isaac-fastlio-nav2.git
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

如果只想做只读验证，不希望 `/g1/cmd_vel` 转发给 Carter，可以关闭速度转发：

```bash
ros2 launch g1_proxy_bridge g1_proxy_bridge.launch.py enable_cmd_vel_forwarding:=false
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

### 6.6 仿真键盘控制

> 仅限 Isaac Sim 代理场景。不要在实机阶段直接照抄这一步。

```bash
sudo apt install ros-humble-teleop-twist-keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/g1/cmd_vel
```

命令链路：

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

## 7. 快速开始：实机只读数据检查

实机阶段默认目标是：**接收数据、录包、看点云、建图，不让机器人动。**

```bash
cd ~/G1_SLAM
source /opt/ros/humble/setup.bash
# 如果你的工作空间已经编译：
# source install/setup.bash
```

检查有线网卡和 ROS2/DDS 基础状态：

```bash
cd /path/to/g1-isaac-fastlio-nav2
bash scripts/real_g1_network_readonly_check.sh
```

只读录包模板：

```bash
bash scripts/record_real_g1_bag_readonly.sh
```

更多步骤见：

- `docs/07_real_robot_wired_dds.md`
- `docs/08_real_robot_data_pipeline.md`
- `docs/10_safety_notes.md`

## 8. FAST-LIO 建图

本仓库不直接包含第三方 FAST-LIO 源码，请按照你使用的 FAST-LIO / FAST-LIO2 / FAST_LIO_LOCALIZATION_HUMANOID 版本自行放置第三方仓库。

仿真核心输入：

```text
LiDAR: /g1/lidar_points
IMU:   /g1/imu
```

可参考模板：

```text
config/fast_lio/g1_isaac_fastlio.template.yaml
config/fast_lio/g1_real_mid360_fastlio.template.yaml
```

项目中曾观察到的 FAST-LIO 输出包括：

```text
/Laser_map_1
/cloud_registered_1
/path_1
/Odometry_loc
```

## 9. Nav2 接入路线

当前 Nav2 接入仍属于 roadmap。优先级为：

1. 仿真中验证 FAST-LIO 位姿输出；
2. 统一 map / odom / g1_base_link TF；
3. 生成 2D 栅格地图 `pgm/yaml`；
4. Nav2 加载地图和定位；
5. RViz 发送目标点；
6. 先在仿真代理场景闭环；
7. 实机阶段在安全隔离后，再将 Nav2 `/cmd_vel` 接到底层执行层。

## 10. 第三方与许可证说明

本仓库不会直接分发未确认许可证的 Unitree 官方模型、SDK、Isaac Sim 示例资产或第三方 FAST-LIO 源码。相关内容请参考 `third_party.md`。

## 11. 当前版本定位

```text
v0.1 = Isaac Sim G1 proxy + FAST-LIO mapping workflow
v0.2 = Real G1 wired DDS read-only data pipeline + safety-first migration notes
```

v0.2 的重点不是“让 G1 动起来”，而是把仿真仓库扩展成**仿真—实机过渡仓库**：先把真实 G1 的数据稳定拿到、记录下来、可视化出来，再进入 Nav2 和底层执行。
