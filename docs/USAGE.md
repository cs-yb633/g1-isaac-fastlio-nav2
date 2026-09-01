# Docker 环境使用说明

Docker 镜像 `g1-nav:humble` 就是本项目的隔离开发环境。ROS 2、Nav2、SLAM Toolbox、Unitree 消息和 CycloneDDS 全部在镜像内，不需要再创建 Conda 环境，也不要在宿主机 source 其他 ROS 环境。

以下命令默认在项目目录执行：

```bash
cd /opt/ext_disk/pub/MYB/G1-Nav
```

## 1. 首次构建

镜像已经在当前电脑构建完成。以后只有 Dockerfile 或依赖锁发生变化时才需要重新执行：

```bash
docker compose build g1-nav
```

## 2. 进入开发环境

```bash
docker compose run --rm g1-nav bash
```

看到容器 shell 后，可检查环境：

```bash
echo "$ROS_DISTRO"
echo "$RMW_IMPLEMENTATION"
ros2 pkg prefix slam_toolbox
ros2 pkg prefix nav2_bringup
```

正常结果应包含 `humble`、`rmw_cyclonedds_cpp` 和 `/opt/ros/humble`。

输入 `exit` 或按 `Ctrl+D` 退出。`--rm` 会删除这次临时容器，但镜像和项目文件不会丢失；项目目录通过 volume 挂载，源码、配置和地图仍保存在宿主机。

## 3. 查看或停止容器

通常 `run --rm` 退出后不会留下容器。仍可检查：

```bash
docker ps
docker compose ps
```

如果另一个终端中有本项目容器仍在运行：

```bash
docker compose down
```

## 4. 连接 G1 前配置有线网络

只有网线已经连接 G1 时才执行。先查看实际接口：

```bash
ip -brief link
ip -brief address
```

当前历史配置是电脑 `enp6s0=192.168.123.222/24`、G1 `192.168.123.164`。重新接机时仍须核验，不能假定固件或网络未变化。

若接口仍为 `enp6s0`，可在宿主机临时配置：

```bash
sudo ip link set enp6s0 up
sudo ip address replace 192.168.123.222/24 dev enp6s0
ping -c 3 192.168.123.164
```

不要使用会清空其他地址的 `ip addr flush`。若网卡名不同，在项目根目录创建 `.env`：

```dotenv
LOCAL_UID=1001
LOCAL_GID=1001
G1_NETWORK_INTERFACE=实际网卡名
ROS_DOMAIN_ID=0
DISPLAY=:0
```

可从 [.env.example](../.env.example) 复制；`.env` 不进入 Git。

## 5. Gate 1：只读探测 G1

进入容器：

```bash
docker compose run --rm g1-nav bash
```

容器采用 host network，因此可以直接看到宿主网卡。先做网络和 ROS 图检查：

```bash
ip -brief address
ping -c 3 192.168.123.164
ros2 topic list -t
```

重点寻找标准接口及 Unitree LiDAR 接口：

```bash
ros2 topic list -t | grep -E '(^|/)(scan|odom|tf|utlidar|lowstate|sportmodestate)'
```

本机已确认的原始接口是 `/dog_odom`、`/dog_imu_raw` 和
`/utlidar/cloud_livox_mid360`。继续执行：

```bash
ros2 topic info /dog_odom --verbose
ros2 topic echo /dog_odom --once
ros2 topic hz /dog_odom

ros2 topic echo /dog_imu_raw --field header --once
ros2 topic echo /utlidar/cloud_livox_mid360 --field header --once
ros2 topic list | grep -E '^/(tf|tf_static|scan)$' || true
```

不要直接打印完整点云消息；只读消息头即可确认时间戳和 `livox_frame`，
同时避免向终端输出大量二进制数组。

这些命令只读取数据。此阶段禁止运行 Unitree 运动示例、发布 `/cmd_vel`、调用 `SetVelocity` 或切换 FSM。

## 6. 常见参数覆盖

临时使用另一块网卡：

```bash
G1_NETWORK_INTERFACE=eno1 docker compose run --rm g1-nav bash
```

临时使用另一 ROS domain：

```bash
ROS_DOMAIN_ID=42 docker compose run --rm g1-nav bash
```

只有实机探测证明机器人使用非零 domain 时才修改 `ROS_DOMAIN_ID`。

## 7. 构建与测试 Gate 2/3 代码

在项目根目录执行：

```bash
docker compose run --rm g1-nav bash -lc \
  'colcon build --symlink-install && source install/setup.bash && colcon test --event-handlers console_direct+ && colcon test-result --verbose'
```

这些命令只构建和测试本地代码，不连接或控制机器人。

## 8. 启动只读感知链路

进入容器并构建/source 工作区后：

```bash
ros2 launch g1_nav_bringup sensing.launch.py
```

默认行为：

- 订阅 `/dog_odom`，发布 `odom -> base_footprint -> robot_center`；
- 启动 `pointcloud_to_laserscan`，订阅 `/utlidar/cloud_livox_mid360`，目标输出为 `/scan_raw`；
- **不发布** `livox_frame` 静态 TF，并清楚打印警告。因此外参未提供时转换器无法处理点云，这是预期的安全状态。

不得为了看到扫描数据而填写猜测值。只有父帧和六自由度外参已经由 CAD、厂商资料或受控测量核验后，才可显式启动，例如以下占位形式（尖括号必须替换为核验值）：

```bash
ros2 launch g1_nav_bringup sensing.launch.py \
  publish_sensor_tf:=true \
  sensor_parent_frame:=<verified_parent_frame> \
  sensor_x:=<verified_x_m> sensor_y:=<verified_y_m> sensor_z:=<verified_z_m> \
  sensor_roll:=<verified_roll_rad> sensor_pitch:=<verified_pitch_rad> \
  sensor_yaw:=<verified_yaw_rad>
```

启用开关但漏填任一值时，启动会失败并列出缺失参数。初始点云切片参数位于 `src/g1_nav_bringup/config/pointcloud_to_laserscan.yaml`，它们只是诊断初值；在外参核验后检查地面、机器人自身回波、量程和时间同步，再调整参数。

只读验证命令：

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo base_footprint robot_center
ros2 topic hz /tf
ros2 topic hz /scan_raw
ros2 topic echo /scan_raw --once
```

此阶段仍禁止发布 `/cmd_vel`、调用运动服务、运行 Unitree 运动示例或切换 FSM。

## 9. `/dog_odom` probe 与离线分析

启动前 50 帧诊断、限时 recorder、CSV 字段、analyzer 输出和 startup qualification 行为见：

- [Odometry Characterization](ODOMETRY_CHARACTERIZATION.md)

## 10. 手动 FSM 工具

该工具不属于 sensing bringup，默认只打印 dry-run。模式、风险和显式执行门见：

- [手动 FSM 工具](SAFETY_FSM.md)
