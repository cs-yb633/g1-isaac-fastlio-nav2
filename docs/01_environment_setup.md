# 01 环境配置

## 推荐环境

```text
Ubuntu 22.04
ROS 2 Humble
NVIDIA Isaac Sim
Python 3.10
colcon
```

## ROS 2 基础环境

```bash
source /opt/ros/humble/setup.bash
```

如果使用项目环境脚本，例如：

```bash
source ~/mayibo/enter_mayibo.sh
```

需要确认：

```bash
echo $ROS_DISTRO
echo $ROS_DOMAIN_ID
echo $CONDA_PREFIX
```

项目中常用：

```bash
ROS_DISTRO=humble
ROS_DOMAIN_ID=42
```

## 工作空间建议

```bash
mkdir -p ~/mayibo/ws_g1/src
cd ~/mayibo/ws_g1
```

将本仓库放到：

```bash
~/mayibo/ws_g1/src/g1-isaac-fastlio-nav2
```

编译：

```bash
cd ~/mayibo/ws_g1
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Isaac Sim 启动建议

Isaac Sim 建议从干净终端启动，不要直接从已经 source ROS、conda、工作空间的终端启动，避免环境变量冲突。

示例：

```bash
cd /home/eirl3090/isaacsim
./isaac-sim.sh
```

进入 Isaac Sim 后：

1. 打开保存好的 G1 + Carter 代理场景；
2. 启用 ROS2 Bridge extension；
3. 点击 Play；
4. 在 ROS 2 终端检查话题。

## 检查 ROS 2 与 Isaac Sim 是否连通

```bash
ros2 topic list
```

如果能看到：

```text
/front_3d_lidar/lidar_points
/chassis/imu
/chassis/odom
/tf
/clock
/cmd_vel
```

说明 Isaac Sim 与 ROS 2 通信基本正常。

## 常见环境问题

### 1. 看不到 Isaac Sim 话题

检查：

```bash
echo $ROS_DOMAIN_ID
```

Isaac Sim 和 ROS 2 终端必须在同一个 `ROS_DOMAIN_ID` 下。

### 2. 话题存在但没有数据

确认 Isaac Sim 是否点击 Play。

### 3. TF 时间异常

如果使用仿真时间，检查：

```bash
ros2 topic echo /clock --once
```

必要时在节点参数中启用 `use_sim_time:=true`。
