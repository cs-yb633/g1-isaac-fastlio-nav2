# 00 项目总览

## 项目目标

本项目目标是在 Isaac Sim 中完成 Unitree G1 的导航建图仿真流程，重点验证：

1. G1 模型在 Isaac Sim 中作为导航主体显示；
2. Carter 作为隐藏运动代理负责底层移动；
3. ROS 2 中抽象出统一的 `/g1/*` 接口；
4. 使用 3D LiDAR + IMU 接入 FAST-LIO；
5. 后续接入 Nav2，实现目标点导航。

## 当前策略

当前不直接做 G1 双足动力学控制，而是采用“代理运动 + 上层导航抽象”的工程路线。

```text
Carter 底盘运动能力
        +
G1 可视化模型
        +
g1_proxy_bridge 接口抽象
        =
可复现的 G1 导航仿真平台
```

## 为什么不用 2D /scan

项目路线明确保留 3D LiDAR / PointCloud2 输入，不使用 `pointcloud_to_laserscan` 将 3D 点云退化成 2D `/scan`。

主要原因：

1. G1 实机更可能面对三维环境感知；
2. FAST-LIO 本身是 LiDAR-Inertial Odometry 路线；
3. 3D 点云路线更适合后续迁移到实机；
4. 2D `/scan` 虽然容易接 Nav2，但会损失三维信息。

## 当前完成状态

- G1 URDF 已导入 Isaac Sim；
- G1 已绑定 Carter 并跟随运动；
- Carter 已隐藏，G1 作为可见主体；
- Isaac Sim 可发布 3D LiDAR、IMU、Odom、TF；
- `g1_proxy_bridge` 已能抽象 `/g1/*` 接口；
- FAST-LIO 建图测试已跑通；
- 下一步是把 FAST-LIO 定位输出接入 Nav2。
