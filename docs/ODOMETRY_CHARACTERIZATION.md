# `/dog_odom` 只读记录与分析

本工具链只订阅 `/dog_odom` 并写 CSV，不发布机器人控制话题、不调用 Unitree API，也不会自动执行实验动作。

## 启动前 50 帧 probe

在容器中构建并 source 工作区后：

```bash
mkdir -p /workspace/recordings
ros2 run g1_nav_adapter dog_odom_probe --ros-args \
  -p sample_count:=50 \
  -p output_path:=/workspace/recordings/dog_odom_startup.csv
```

CSV 每帧包含接收时间、消息时间戳、frame、位姿、四元数模长、线/角速度、时间戳单调性、帧一致性、位置跳变和集中校验结果。运行数据目录 `recordings/` 被 Git 忽略。

核心校验参数与 TF adapter 共用同一实现：

```text
odom_frame=odom
source_child_frame=robot_center
quaternion_norm_tolerance=0.001
max_abs_position_m=1000.0
```

probe 另有仅用于报告的 `large_jump_m`，默认 0.5 m。所有阈值集中定义在 `odom_validation.py`，可通过 ROS parameter 覆盖。

## 限时 recorder

`dog_odom_probe` 同时承担只读 recorder。把样本上限设为 0，并指定持续时间：

```bash
ros2 run g1_nav_adapter dog_odom_probe --ros-args \
  -p sample_count:=0 \
  -p duration_sec:=120.0 \
  -p output_path:=/workspace/recordings/static_120s.csv
```

不要把动作写进脚本。下一阶段的静止、直线、旋转、方形闭环、重启或重连实验必须由现场人员在各自安全条件与授权下单独执行，recorder 只负责被动记录。

建议每个 CSV 配套人工记录：实验名称、开始/结束时间、机器人状态、操作者、场地和是否发生 reset/DDS 重连。不要记录密码、序列号或可识别场地信息到公开仓库。

## 离线分析

```bash
ros2 run g1_nav_adapter dog_odom_analyze \
  --input /workspace/recordings/static_120s.csv
```

输出为便于人工阅读和批处理的 JSON，包括：

- duration、sample count、mean rate、min/max dt；
- initial/final pose 及 delta x/y/z/yaw；
- max absolute roll/pitch；
- timestamp regressions、invalid/rejected samples、large jumps；
- planar path length、net displacement、closure error 和 yaw closure error。

invalid/rejected 样本保留在计数和 raw jump 检查中，但不会污染首末位姿、姿态极值或路径长度计算。

`closure_error` 只是首末位姿的数值比较，只有对应 CSV 确实来自闭环实验时才具有闭环含义。

## TF startup qualification

`g1_odom_tf_node` 参数 `startup_valid_samples` 默认是 5：

1. 启动后等待连续 5 帧通过集中校验的 `/dog_odom`；
2. 第 5 帧才开始发布 TF，仍使用该帧原始时间戳；
3. qualification 前任一坏帧把连续计数清零；
4. qualification 后坏帧只被拒绝，不取消 qualification，也不使用上一帧替代；
5. `startup_valid_samples:=1` 可恢复接近原先的首帧发布行为。

节点定期输出 `received_count`、`valid_count`、`rejected_count`、`startup_valid_streak` 和 `qualified`。周期由 `statistics_log_period_sec` 控制，设为 0 可关闭周期日志。

## 严格禁止

本流程不得启动或调用 LocoClient、SetVelocity、Move、Start、SetFsmId、Damp、StandUp、HighStand、BalanceStand、StopMove、`cmd_vel` 到机器人或任何 raw DDS control request。
