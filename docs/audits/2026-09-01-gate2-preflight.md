# G1 Gate 2 前置只读复核

复核日期：2026-09-01  
范围：有线网络、DDS 发现、里程计/传感器消息头和里程计连续采样。未发送运动请求，未切换 FSM。

## 网络

- `enp6s0`：`UP/LOWER_UP`，`192.168.123.222/24`。
- G1：`192.168.123.164`，3/3 ICMP 成功，0% 丢包，平均 0.233 ms。

## DDS 与 frame

- `/dog_odom`：`nav_msgs/msg/Odometry`，一个 bare DDS publisher，Reliable、Keep Last 1。
- 消息 frame：`odom -> robot_center`。
- `/dog_imu_raw` frame：`dog_imu_link`。
- `/utlidar/cloud_livox_mid360` frame：`livox_frame`。
- 原始 ROS 图中仍没有 `/tf`、`/tf_static` 或 `/scan`。
- `/lowstate.mode_machine` 本次读数为 `5`；本记录不推断其机械型号或 FSM 语义。

## `/dog_odom` 异常与连续采样

第一次单条读取出现：

```text
position.x = 4.009699584011969e+24
position.y = -0.0013438260648399591
position.z = 0.0011015234049409628
```

这是有限浮点数，但显然不是可接受的里程计坐标。随后六次单条读取均恢复正常。再连续收集 250 帧，结果为：

| 字段 | 最小值 | 最大值 |
|---|---:|---:|
| x (m) | 0.00307855 | 0.00367949 |
| y (m) | -0.00228409 | -0.00188007 |
| z (m) | 0.72613460 | 0.72621459 |
| qx | 0.00751817 | 0.00779319 |
| qy | 0.00560706 | 0.00602382 |
| qz | -0.00147046 | -0.00110189 |
| qw | 0.99995095 | 0.99995524 |

250 帧中没有 NaN、Inf、绝对位置大于 100 m 的样本，也没有非递增时间戳。异常首帧的根因仍未知，不能仅凭后续正常样本把它关闭。

## 本次代码保护与边界

`g1_odom_tf_node` 除 finite 和四元数检查外，增加了可配置的绝对位置上限；默认 1000 m，足以拒绝本次巨值。该保护不能替代根因调查和直线、旋转、闭环、静止实验。

实现期间做过一次约四秒的默认只读 launch smoke test，仅启动 TF 适配器和点云转换器；传感器静态 TF 保持禁用，没有控制发布者或运动服务客户端。未发送任何 G1 运动/FSM 请求。

## TF 适配器静止实机检查

只单独运行适配器约十余秒并读取派生 `/tf`，没有启动点云转换或任何控制节点：

- `odom -> base_footprint` 可查询，z、roll、pitch 均为零；当时 x/y 约为 `0.004/-0.002 m`，yaw 约 `-0.1°`。
- `base_footprint -> robot_center` 可查询，x/y 为零；高度约 `0.726 m`，roll/pitch 约 `0.85°/0.69°`。
- `/tf` 平均频率约 `51.18 Hz`，采样间隔约 0.019--0.021 s。
- 运行期间没有出现输入拒绝日志。限时结束时 ROS CLI 产生一次 context shutdown 警告，不是输入或变换错误。

这只验证了静止状态下的数学分解和发布频率，尚未验证移动时轴方向、连续性或复位行为。

## 型号线索（仍需实机确认）

本次 `/lowstate.mode_machine` 为 `5`。Unitree 当前模型清单把 5 对应到多个
`g1_29dof_rev_1_0` 变体（无手、Dex3、Inspire Hand），因此可确认 29 DoF Rev 1.0
系列线索，但仅靠这个字段仍不能选定完整硬件模型：

- https://github.com/unitreerobotics/unitree_ros/blob/master/robots/g1_description/README.md

对应官方 `g1_29dof_rev_1_0.urdf` 的 Mid360 固定关节与旧
`g1_29dof.urdf` 数值不同，而且 URDF child 是 `mid360_link`，实机点云 frame 是
`livox_frame`。在核实具体手型、`robot_center` 是否等于 `pelvis`、腰部关节状态来源，
以及 `mid360_link` 与 `livox_frame` 的关系前，不把该 URDF 数值写入运行配置：

- https://github.com/unitreerobotics/unitree_ros/blob/master/robots/g1_description/g1_29dof_rev_1_0.urdf

## 结论

Gate 1 复核通过，Gate 2 的静止检查通过。Gate 2 尚未整体通过：需要在受控人工移动实验中验证 TF 连续性、轴方向、reset 行为，并调查异常首帧。Gate 3 仍阻塞于 `robot_center` 实体语义与 `livox_frame` 六自由度外参核验。
