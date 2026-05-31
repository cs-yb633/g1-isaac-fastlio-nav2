# 02 Isaac Sim 场景设置

## 场景基础

本项目建议以 Isaac Sim 的 Nova Carter ROS2 Navigation 示例作为基础场景。

Carter 提供：

- 差速/轮式底盘运动能力；
- 里程计 `/chassis/odom`；
- 3D LiDAR `/front_3d_lidar/lidar_points`；
- IMU `/chassis/imu`；
- `/cmd_vel` 控制入口；
- `/tf` 与 `/clock`。

## G1 模型导入

将 Unitree G1 URDF 导入 Isaac Sim 后，需要注意：

1. mesh 路径是否正确；
2. 模型尺度是否正确；
3. G1 是否放置在 Carter 上方或绑定到 Carter；
4. 是否保留 G1 可视化部分；
5. 是否隐藏 Carter 外观但保留其运动与传感器。

## 为什么绑定到 Carter

直接驱动 G1 双足模型需要完整的运动控制、接触动力学和步态控制，这不是当前阶段重点。

当前阶段只需要验证：

```text
导航算法输出 cmd_vel
        ↓
机器人在仿真环境中移动
        ↓
传感器产生随运动变化的数据
        ↓
SLAM / Localization / Nav2 能闭环
```

因此 Carter 是一个稳定的“运动代理”。

## 推荐接口抽象

在 Isaac Sim 中保留 Carter 原始接口：

```text
/cmd_vel
/chassis/odom
/front_3d_lidar/lidar_points
/chassis/imu
```

在 ROS 2 中通过 `g1_proxy_bridge` 抽象为：

```text
/g1/cmd_vel
/g1/odom
/g1/lidar_points
/g1/imu
```

这样上层算法只感知 G1，不直接依赖 Carter 名称。

## 保存场景

建议将 Isaac Sim 场景保存到本地，例如：

```text
/home/eirl3090/mayibo/isaac_scenes/g1_carter_proxy_g1_nav.usd
```

但不建议直接把 `.usd` 大文件上传到 GitHub。可以在 README 中说明场景搭建步骤，并上传少量截图。
