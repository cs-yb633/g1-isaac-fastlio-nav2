# 手动 G1 FSM 工具

`g1_fsm_tool` 是与导航 bringup 完全隔离的一次性人工工具。它不会自动运行，不发送速度，不在失败时尝试其他 FSM，也不会被 Nav2 调用。

## 已提供模式

| 名称 | FSM ID | 官方 Python API 对应 | 主要风险 |
|---|---:|---|---|
| `start` | 500 | `Start()` | 机器人可能站立或进入可运动状态 |
| `sit` | 3 | `Sit()` | 机器人可能执行坐下动作 |
| `damp` | 1 | `Damp()` | 机器人可能失去姿态并倒下 |
| `zero_torque` | 0 | `ZeroTorque()` | 机器人可能立即失去支撑并倒下 |

来源是项目 Dockerfile 固定提交中的官方 G1 `LocoClient`：

- https://github.com/unitreerobotics/unitree_sdk2_python/blob/65691c8a8bc53b98d3976dba4dbf9d5d20b2e7f5/unitree_sdk2py/g1/loco/g1_loco_client.py

不同 SDK 版本对其他 StandUp/Squat 快捷方法并不一致，因此本工具没有猜测或加入这些 ID。

## 默认 dry-run

以下命令不初始化 DDS，也不发送请求：

```bash
ros2 run g1_nav_control g1_fsm_tool start
ros2 run g1_nav_control g1_fsm_tool sit
ros2 run g1_nav_control g1_fsm_tool damp
ros2 run g1_nav_control g1_fsm_tool zero_torque
```

输出 JSON 中必须是：

```text
dry_run: true
dds_initialized: false
request_sent: false
```

## 只读查询

连接网线后，只读取当前 FSM：

```bash
ros2 run g1_nav_control g1_fsm_tool status \
  --network-interface enp6s0
```

先执行 status，并由现场人员确认机器人支撑、周围净空、急停和当前姿态，再考虑任何切换。

## 显式执行

实际切换必须同时提供：

1. `--execute`；
2. 刚刚读取并人工确认的 `--expect-current-id`；
3. 与所选模式一致的 `--confirm-target-id`；
4. 完整风险确认字符串。

模板：

```bash
ros2 run g1_nav_control g1_fsm_tool <mode> \
  --network-interface enp6s0 \
  --execute \
  --expect-current-id <live_current_id> \
  --confirm-target-id <target_id> \
  --acknowledge-risk I_UNDERSTAND_G1_MAY_MOVE_OR_FALL
```

工具会在发送前再次读取 FSM。若它不等于 `--expect-current-id`，请求被拒绝。`SetFsmId` 返回成功后还会读取目标状态；失败时不会自动 Start、Damp、ZeroTorque 或发送速度作为“修复”。

## 与导航的边界

- `sensing.launch.py` 不启动此工具；
- 没有 FSM 自动序列；
- 没有 `/cmd_vel` 订阅或速度接口；
- 不允许把它加入 Nav2 launch；
- 工具存在不代表 Gate 6 或自主运动已经开放。
