# 飞书历史资料审计

## 可继承的事实和需求

- 项目对象是 Unitree G1 实机，电脑通过有线网络连接机器人。
- 历史电脑端有线接口为 `enp6s0`，曾使用 `192.168.123.222/24`。
- G1 开发计算单元曾通过 `192.168.123.164` 提供 ping、SSH 和 DDS 通信。
- 历史记录显示电脑曾稳定接收到 Mid360 点云和 Unitree SLAM 相关 DDS 数据。
- 键盘操控建图、保存地图、加载地图以及最终接入 Nav2 是项目的核心用户流程。
- 实机运动必须具备低速限制、加速度限制、命令超时自动停止、明确急停和人工监护。
- Nav2 不得把未经限幅和安全检查的速度指令直接发送给实体机器人。

这些内容是恢复时需要重新验证的线索，不是对重装后环境的现状保证。网卡名称、IP、DDS 话题、FSM 和接口权限都必须重新探测。

## 明确排除

以下内容不进入当前主线，也不为兼容历史代码而保留：

- Isaac Sim、Gazebo、MuJoCo、Carter 代理及所有仿真资产。
- FAST-LIO 和 DeepGlint 仓库方案。
- PCD 录制、PCD 落盘、PCD 投影为 PGM/YAML 的建图路线。
- `save_mapping_pcd.py`、`pcd_to_nav2_map.py`、`make_safe_nav_map.py`。
- 仿真话题 `/g1/lidar_points`、`/g1/imu`、`/g1/odom`、`/g1/cmd_vel` 的历史抽象约定。
- `g1_proxy_bridge`、`g1_fake_controller` 和 Carter 相关 TF。
- 为了跑通演示而设置的临时 `map -> odom` 静态 TF。
- 旧 `g1_cmd_vel_bridge.py` 的代码结构和 FSM 辅助脚本实现。

历史节点名只用于理解曾经解决过的问题。新工程优先采用官方接口、标准 ROS 2 消息和已有成熟包；确实缺少适配层时，再实现职责单一、可测试、默认禁止实机运动的新组件。

## 当前目标链路

```text
Unitree G1 实机传感器
          ↓
ROS 2 标准传感器话题、里程计与 TF
          ↓
SLAM Toolbox 在线建图
          ↓
直接保存 Nav2 2D 地图
          ↓
Nav2 定位、规划、局部避障
          ↓
独立安全层（限速、限加速度、watchdog、急停）
          ↓
Unitree 官方高层运动接口
```

## 必须重新验证的未知项

- G1 具体型号、自由度版本、当前固件和运动服务版本。
- Mid360 数据由哪个官方服务发布，以及重装后可用的真实 DDS 话题和消息类型。
- 是否已经有官方 ROS 2 驱动能直接提供 `sensor_msgs/LaserScan`、`nav_msgs/Odometry` 和完整 TF。
- 若只有 `PointCloud2`，SLAM Toolbox 所需二维扫描的裁剪、坐标系和时间戳策略。
- 可用里程计来源及 `odom -> base_link` 的连续性和漂移特征。
- SLAM Toolbox 保存地图后，Nav2 采用 AMCL 还是 SLAM Toolbox localization mode；由实机数据质量决定。
- Nav2 速度输出到 Unitree 高层运动服务的当前官方推荐接口、FSM 前置条件及失联停止行为。

