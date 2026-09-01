# TF 树与约束

## 当前只读树

```text
odom
└── base_footprint                 g1_odom_tf_node，动态
    └── robot_center               g1_odom_tf_node，动态残差
        └── ... livox_frame        未确定，不默认发布
```

Gate 1 实测 `/dog_odom` 表达 `T_odom_robot_center`。适配器从每一条消息直接计算：

```text
T_odom_base_footprint = [x, y, 0, yaw]
T_base_footprint_robot_center =
  inverse(T_odom_base_footprint) * T_odom_robot_center
```

两个 TF 使用原始 Odometry 消息时间戳。节点不使用接收时间，不做滤波或积分。输入必须是精确的 `odom -> robot_center`，位置和四元数必须有限，四元数模长必须在容差内；任一位置分量还必须处于可配置的绝对限值内（`max_abs_position_m` 默认 1000 m）。任一检查失败时整条消息被拒绝，不发布两个 TF 中的任何一个。

2026-09-01 的追加只读检查中，第一次单条 `/dog_odom` 读取曾出现有限但明显无效的 `x=4.009699584e24`；随后 6 条重复样本和 250 条连续采集均处于毫米级附近，且时间戳严格递增。该瞬态的来源尚未解释。位置限值可以阻止它进入 TF，但不能代替实机根因调查。

平面变换保留 x、y 和 yaw。第二段变换精确保留原始姿态中的 z、roll、pitch 残差，因此组合结果仍等于输入的三维里程计位姿。

## 传感器外参规则

`livox_frame` 是点云消息中观测到的帧名，但其相对机器人本体的位置和姿态未知。启动文件不会提供零值或“看起来合理”的默认外参。只有通过 CAD、厂商资料或受控测量核验以下信息后，才能显式启用静态 TF：

- 父帧名称；
- x、y、z（米）；
- roll、pitch、yaw（弧度）。

2026-09-01 实机读取的 `mode_machine=5` 与 Unitree 当前模型清单中的
`g1_29dof_rev_1_0` 系列一致。该系列官方 URDF 确实包含
`torso_link -> mid360_link` 固定关节，但这还不能直接补齐运行 TF：

- `robot_center` 是否等于 URDF 的 `pelvis` 尚未确认；
- `pelvis -> torso_link` 穿过三个腰部转动关节，需要正确 joint state；
- 点云使用 `livox_frame`，URDF 使用 `mid360_link`，两者关系尚未确认；
- mode 5 对应多个手部变体，仍应核对实机/App 中的完整 Machine Type。

参考官方模型清单与对应 URDF：

- https://github.com/unitreerobotics/unitree_ros/blob/master/robots/g1_description/README.md
- https://github.com/unitreerobotics/unitree_ros/blob/master/robots/g1_description/g1_29dof_rev_1_0.urdf

## 未来树

SLAM 或定位启用后，树顶部可以增加 `map -> odom`，但任何时刻只能有一个发布者。Nav2 不应另行发布 `odom -> base_footprint`。
