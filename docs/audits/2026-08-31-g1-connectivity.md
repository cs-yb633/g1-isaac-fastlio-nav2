# G1 Gate 1 连接与只读数据审计

审计日期：2026-08-31  
范围：有线网络、DDS 发现、只读传感器与里程计数据。未发送运动请求，未切换 FSM，未启动建图服务。

## 网络

| 项目 | 结果 |
|---|---|
| 电脑接口 | `enp6s0`，`UP/LOWER_UP` |
| 电脑地址 | `192.168.123.222/24` |
| G1 地址 | `192.168.123.164` |
| ICMP | 3/3 成功，0% 丢包 |
| 往返延迟 | 平均 0.247 ms |
| ARP/邻居状态 | `REACHABLE` |

## 已确认持续发布的数据

| ROS 2 话题 | 类型 | 帧 | 频率/内容 |
|---|---|---|---|
| `/dog_odom` | `nav_msgs/msg/Odometry` | `odom -> robot_center` | 约 51.2 Hz |
| `/dog_imu_raw` | `sensor_msgs/msg/Imu` | 待进一步记录 | 约 51.2 Hz |
| `/utlidar/cloud_livox_mid360` | `sensor_msgs/msg/PointCloud2` | `livox_frame` | 约 10.0 Hz，单帧约 20,064 点 |

以上话题均有一个来自 G1 bare DDS application 的发布者，数据时间戳和当前系统时间一致。

## 已发现但当前无数据

- `/unitree/slam_mapping/odom`
- `/unitree/slam_relocation/odom`

两者存在 DDS 发布端，但在本次未启动官方 mapping/relocation 会话时没有收到样本。这不是网络故障。

## 导航接口缺口

- 当前没有原生 `/scan`。
- 当前没有 `/tf` 或 `/tf_static`。
- SLAM Toolbox 不能直接使用当前图，必须先建立：
  - Mid360 PointCloud2 到二维 LaserScan 的标准转换；
  - `odom -> robot_center` 动态 TF；
  - `robot_center -> livox_frame` 的已核验静态 TF；
  - 必要时把导航基准帧规范为 `base_link`/`base_footprint`，但不能猜测外参。

优先使用 `pointcloud_to_laserscan`、`robot_localization`、`robot_state_publisher` 或标准 TF 工具。只有标准组件无法表达实际数据时才新增最小适配代码。

## 结论

Gate 1 通过：G1 有线网络、CycloneDDS 发现、基础里程计、IMU 和 Mid360 原始点云均正常。尚不满足 SLAM Toolbox 启动条件，下一阶段应先完成只读 TF 与 `/scan` 链路，不开放任何运动权限。
