# Gate 2 工具与 startup qualification 只读验证

验证日期：2026-09-01  
范围：静止 G1 的 `/dog_odom` 订阅、CSV probe、离线 analyzer、TF startup qualification 和时间戳一致性。未发送运动请求，未切换 FSM，未启动点云、SLAM 或 Nav2。

## 50 帧 startup probe

`dog_odom_probe` 记录了序号 0--49：

```text
samples=50
valid=50
rejected=0
duration=0.954676362 s
mean_rate=51.3262943867 Hz
min_dt=0.019000230 s
max_dt=0.020221276 s
timestamp_regressions=0
large_jumps=0 (threshold 0.5 m)
maximum_jump=0.0000569236 m
```

静止首末平面位移为 `0.0002144571 m`，yaw 差为 `0.0000782954 rad`。运行 CSV 位于被 Git 忽略的 `runtime/`，不进入 baseline commit。

先前出现过的 `position.x=4.009699584e24` 在本次 50 帧中 **not reproduced**。先前异常是当次单条读取获得的第一条样本；数值本身是 finite，但会触发集中校验错误 `position_absolute_limit`。节点级测试确认它在 qualification 前会清零连续计数，在 qualification 后会被单帧拒绝，两个场景都不会进入 TF，也不会用上一帧替代。

## startup qualification 实机检查

默认参数：

```text
startup_valid_samples=5
```

实机日志首先报告：

```text
Startup qualification complete after 5 consecutive valid samples
```

后续周期统计累计到 1128 帧时仍为：

```text
valid_count=1128
rejected_count=0
startup_valid_streak=5
qualified=True
```

受限运行期间 `/tf` 约 `51.18--51.19 Hz`。并行观察到 100 个原始 odom 时间戳和 95 个 `odom -> base_footprint` TF 时间戳；95/95 TF 时间戳都能在原始 odom 集合中精确匹配，证明没有改写为接收时间。

## 数学性质

测试验证完整关系：

```text
T_odom_base_footprint * T_base_footprint_robot_center
≈ T_odom_robot_center
```

覆盖普通六自由度姿态、仅 yaw、明显 roll/pitch、接近正负 pi 的 yaw，以及固定种子生成的 250 组合法随机姿态。随机组最大误差：

```text
max translation error = 3.5527136788005009e-15 m
max quaternion component L2 error = 2.5589376332604516e-16
assertion epsilon = 1e-11
```

测试同时检查平面段 z=0 且四元数 x/y=0；对 residual 不施加“只能含 z/roll/pitch”的错误假设，以完整 SE(3) 重组为最终判据。

## 结论

Gate 2A 保持 PASS。Gate 2B/2C 所需只读工具已准备且通过静止验证，但动态和 reset 实验尚未执行。异常首帧没有在本轮复现，因此根因仍未解决。
