# 项目来源清单

本目录登记项目恢复时使用的资料及其可信度。来源用于提取事实和需求，历史实现不等于新工程设计。

## S1：Unitree 官方资料

- 名称：G1 调试规范
- 链接：https://support.unitree.com/home/zh/G1_developer/debugging_specification
- 提供者：Unitree 官方文档中心
- 登记日期：2026-08-31
- 用途：确认实机调试模式、网络连接、开发边界和安全要求。
- 规则：涉及 G1 状态机、运动接口、调试模式和硬件安全时，以当前机器人版本对应的官方资料和实机只读检查为准。

官方站点是动态页面，仓库只保存链接和审计结论，不复制可能更新的网页正文。实际操作前须重新核对页面与机器人软件版本。

## S2：历史飞书项目文档

- 文件：`G1 导航建图.pdf`（仅本地保存，不进入公开 Git 仓库）
- 页数：48
- 导出日期：2026-08-31（PDF 元数据）
- 用途：恢复历史上下文、已验证的实机连通性和原项目目标。
- 限制：文档混有仿真、FAST-LIO、PCD 投影、临时桥接节点和阶段性猜测，不能作为当前架构的直接实现规范。

详细取舍见 [feishu-audit.md](feishu-audit.md)。

## S3：官方软件上游

- Unitree ROS 2：https://github.com/unitreerobotics/unitree_ros2
- Unitree SDK2：https://github.com/unitreerobotics/unitree_sdk2
- SLAM Toolbox Humble：https://docs.ros.org/en/humble/p/slam_toolbox/
- Navigation2：https://docs.nav2.org/

`unitree_ros2` 用于 Unitree DDS 消息兼容和实机数据探测。SLAM Toolbox 官方接口规定建图输入为 `sensor_msgs/LaserScan`，并要求可用的 `odom_frame -> base_frame` TF；因此是否需要适配层必须由当前 G1 的真实 `/scan`、`/odom` 和 TF 探测结果决定。

## 来源优先级

出现冲突时按以下顺序处理：

1. 当前 G1 实机的软件版本、只读观测和安全状态。
2. Unitree 当前官方文档及官方 SDK/API。
3. ROS 2、SLAM Toolbox、Nav2 的对应发行版官方文档。
4. 飞书文档中有明确成功证据的实机记录。
5. 飞书中的计划、仿真结论和临时实现。
