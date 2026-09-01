# 安全门状态

| Gate | 范围 | 状态 | 证据/退出条件 |
|---|---|---|---|
| 0 | 环境与依赖恢复 | PASS | Docker/ROS 2 Humble 环境和依赖锁已建立 |
| 1 | 网络与只读数据发现 | PASS | [2026-08-31 实机审计](audits/2026-08-31-g1-connectivity.md)及 [2026-09-01 复核](audits/2026-09-01-gate2-preflight.md) |
| 2A | Static planar TF | **PASS** | [工具与资格门验证](audits/2026-09-01-gate2-tools-validation.md)：纯数学测试、静止 TF 分解、原始时间戳和约 51 Hz 发布检查通过；启动资格门默认要求连续 5 帧合法数据 |
| 2B | Dynamic odometry characterization | **PENDING** | 工具已准备；需在人工安全条件下完成静止、直线、旋转和闭环数据记录与分析 |
| 2C | Reset / jump behavior | **PENDING** | 工具已准备；需记录节点重启、DDS 重连及人工授权的状态变化前后行为，并调查异常首帧 |
| 3A | Authoritative LiDAR extrinsic | **BLOCKED** | `robot_center`、实机型号链及 `livox_frame` 六自由度关系尚未权威核验 |
| 3B | PointCloud2 -> LaserScan raw conversion | **PREPARED** | `/scan_raw` 配置和只读 launch 已有；传感器 TF 默认关闭，不宣称输出可用 |
| 3C | TF-aligned dynamic scan validation | **BLOCKED by Gate 3A** | 只有权威外参建立后才能进行动态扫描验证 |
| 4 | rosbag baseline | **PENDING / NOT OPEN** | 先完成 Gate 2B/2C；只允许记录，不包含动作自动化 |
| 5 | offline SLAM Toolbox | **PENDING / NOT OPEN** | 依赖 Gate 3 和 Gate 4 数据；本阶段不启动 SLAM Toolbox |
| 6 | keyboard motion | **FORBIDDEN / NOT OPEN** | 需要另行明确授权、现场监护和安全方案 |
| 7+ | mapping / localization / Nav2 | **NOT OPEN** | 建图、定位和自主导航均未开放 |

“代码完成”不等同于 Gate 通过。不得通过猜测外参、自动执行实验动作或接通控制接口绕过任何 Gate。
