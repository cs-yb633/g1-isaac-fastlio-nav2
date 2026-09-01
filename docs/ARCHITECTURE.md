# G1 Nav 架构

本工程按安全门逐步恢复二维导航能力。当前代码只覆盖只读感知适配，不包含控制链路。

## 包边界

- `g1_nav_adapter`：订阅 `/dog_odom`，严格校验消息后发布导航所需动态 TF。它不积分、不滤波、不修改时间戳。
- `g1_nav_description`：保存经核验的机器人导航几何描述。当前只声明 `base_footprint`；未知物理帧和传感器外参不会写入模型。
- `g1_nav_bringup`：启动里程计适配器和 `pointcloud_to_laserscan`。传感器 TF 默认关闭。

## 数据流与权限

```text
/dog_odom (odom -> robot_center)
  -> g1_odom_tf_node
  -> /tf: odom -> base_footprint -> robot_center

/utlidar/cloud_livox_mid360 (livox_frame)
  -> pointcloud_to_laserscan
  -> /scan_raw   [仅在已核验 livox_frame 外参可用时]
```

所有节点都只有订阅传感器/里程计和发布派生 TF/扫描的权限。工程中没有运动话题发布者、运动服务客户端、LocoClient 或 FSM 调用。

`g1_nav_adapter` 还提供只读 `dog_odom_probe` 和离线 `dog_odom_analyze`。probe 与 TF adapter 复用集中校验规则；CSV 运行数据不进入 Git。TF adapter 默认等待连续 5 帧合法数据后才开始发布，但不会平均、替换或重写任何样本。

## TF 权威

`map -> odom` 必须只有一个权威发布者。未来建图时由 SLAM Toolbox 发布；未来定位/导航时由选定的定位组件发布。两者不得同时争用该变换。`g1_odom_tf_node` 从不发布 `map -> odom`。

`odom -> base_footprint` 来自 `/dog_odom` 的平面投影。`base_footprint -> robot_center` 保存被投影掉的 z、roll 和 pitch 残差，数学定义见 [TF 树](TF_TREE.md)。这只是坐标分解，不代表已经确认 `robot_center` 的机械含义。

## 尚未解决

- `robot_center` 的实际机械基准点和轴定义尚未由厂商资料或测量确认。
- `robot_center`（或其他合适父帧）到 `livox_frame` 的六自由度外参尚未核验。
- `/scan_raw` 的高度、角度和距离参数只是保守诊断初值，必须在核验外参后用实测数据调整。
- 本阶段不启动 SLAM Toolbox、Nav2 或任何运动控制。
