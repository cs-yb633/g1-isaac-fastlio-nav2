# G1 Nav

Unitree G1 实机二维建图与 Nav2 导航工程。当前完成 Gate 1 只读连接审计，并已建立 Gate 2/3 的只读代码基础。

## 项目边界

- 只支持真实 G1，不包含仿真。
- 使用 ROS 2 Humble、SLAM Toolbox 和 Nav2。
- 建图结果由 SLAM Toolbox 直接保存，不使用 PCD 投影生成 Nav2 地图。
- 实机运动默认关闭，并通过分级安全验收后才允许启用。

恢复范围、安全门和历史方案取舍分别见：

- [恢复基线](docs/RECOVERY_BASELINE.md)
- [来源清单](docs/sources/README.md)
- [飞书资料审计](docs/sources/feishu-audit.md)
- [Docker 环境使用说明](docs/USAGE.md)
- [架构](docs/ARCHITECTURE.md)
- [TF 树与约束](docs/TF_TREE.md)
- [安全门状态](docs/GATES.md)
- [`/dog_odom` 只读记录与分析](docs/ODOMETRY_CHARACTERIZATION.md)
- [手动 FSM 工具与安全约束](docs/SAFETY_FSM.md)
- [2026-09-01 Gate 2 前置复核](docs/audits/2026-09-01-gate2-preflight.md)

## 当前状态

- 主机：Ubuntu 24.04；ROS 不安装到宿主机。
- 运行环境：Docker 中的 Ubuntu 22.04 + ROS 2 Humble。
- Unitree 通信：官方 `unitree_ros2` 消息定义 + CycloneDDS 0.10.x。
- 2026-08-31 已通过 `enp6s0` 完成一次实机只读审计；每次接机仍须重新验证接口和网络。
- 已确认 `/dog_odom`（`odom -> robot_center`）和 `/utlidar/cloud_livox_mid360`（`livox_frame`）；机器人未发布 `/scan` 或 TF。
- 已加入带 startup qualification 的平面里程计 TF 适配器、只读 CSV probe/analyzer 和点云转换启动文件；LiDAR 外参未知，因此 `/scan_raw` 尚不能宣称可用。
- 尚未发送运动指令。源码新增了独立、默认 dry-run、不会被 bringup 自动启动的手动 FSM 工具；它不包含速度控制。

## 构建开发容器

```bash
docker compose build g1-nav
docker compose run --rm g1-nav bash
```

容器通过 host network 访问实机 DDS，不使用 `--privileged`。启动时会根据 `G1_NETWORK_INTERFACE` 生成 CycloneDDS 网卡配置。

## 当前构建

```bash
docker compose run --rm g1-nav bash -lc \
  'colcon build --symlink-install && source install/setup.bash && colcon test && colcon test-result --verbose'
```

只读感知启动方法及外参显式参数见 [使用说明](docs/USAGE.md)。

## 下一验收点

下一步是在另行确认的人工安全条件下，用已经准备好的只读工具完成 Gate 2B 动态 `/dog_odom` characterization；不是直接进入 SLAM。随后再核验 `livox_frame` 权威外参，外参未核验前不得以零值或估计值绕过 Gate 3。
