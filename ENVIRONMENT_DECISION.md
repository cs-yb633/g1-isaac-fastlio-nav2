# Ubuntu 24.04 上 ROS 2 Humble 环境决策

**日期：** 2026-08-22  
**范围：** Unitree G1 实机 LiDAR SLAM + Nav2 导航  
**当前状态：** 仅完成调查；未安装 ROS、未安装 Docker 镜像、未启动容器、未修改系统网络或 GPU 配置。

## 结论

推荐采用：

> **Ubuntu 24.04 宿主机 + Docker Engine + ROS 2 Humble/Jammy 容器**

容器使用官方 Humble 的 Ubuntu 22.04 Jammy 基线，在容器内安装 Nav2、slam_toolbox、RViz2、pointcloud_to_laserscan 和所需的 ROS middleware。G1 项目源码、地图、参数和 rosbag 保留在宿主机，通过 bind mount 使用。实机通信阶段使用 host network，以便 DDS/Unitree UDP 流量直接到达宿主机网卡；默认不使用 `--privileged`，也不在 Phase 1 启用运动控制。

推荐理由是：

1. Humble 的官方目标平台是 Ubuntu 22.04，而不是 Ubuntu 24.04；Docker 可以保留官方匹配的 Jammy 用户态。
2. Unitree 官方 Python SDK 固定依赖 `cyclonedds==0.10.2`。Jammy/Humble 的 Python 3.10 与该版本的 cp310 wheel 路径更合适；宿主机 Ubuntu 24.04 的 Python 3.12 和 RoboStack 当前 Python 3.12 构建都需要额外验证或源码编译。
3. Nav2、slam_toolbox、RViz2 和 pointcloud_to_laserscan 可以使用匹配 Humble 的二进制包，不需要在 Ubuntu 24.04 上从头移植整个 ROS 发行版。
4. NVIDIA GPU 不是当前 Nav2 + slam_toolbox + pointcloud_to_laserscan 主链路的必要条件。后续若 FAST-LIO2 或其他 CUDA 节点确实需要 GPU，再单独加入 NVIDIA Container Toolkit 和 GPU 透传。

这不是立即安装授权。本文档完成后暂停，等待确认再进入 Phase 1。

## 当前机器约束

来自现有重装审计：

- Ubuntu 24.04.4 LTS，Python 3.12.3。
- RTX 5060 Ti，NVIDIA 驱动 580.173.02；`nvidia-smi` 可用，但未发现 `nvcc`。
- `wlp5s0` 当前有地址；`enp6s0` 存在但当前为 `DOWN/NO-CARRIER`。实机通信前仍需确认网线、地址和路由。
- 当前没有 ROS 2、conda、micromamba、pip3，也没有现成的 G1/Unitree SDK 工作区。
- 主机资源足以运行容器、RViz2 和本地编译。

## 三种方案总览

| 维度 | micromamba / RoboStack Humble | Docker ROS Humble | Ubuntu 24.04 原生 Humble |
|---|---|---|---|
| Nav2 | RoboStack Humble channel 中有 `navigation2`、`nav2-bringup` 等 Linux 预构建包；需在 Phase 1 做一次完整 solver 验证 | 官方 Humble/Jammy 二进制路径，兼容边界最清晰 | 官方 Humble 文档的 Tier 1 不是 Noble；原生 apt 组合不应视为受支持方案 |
| slam_toolbox | 有 Linux 预构建包，当前元数据为 2.6.10 | 可使用匹配 Humble 的二进制包 | 可从源码尝试，但会把整个 ROS 依赖链带入 Noble 兼容性问题 |
| RViz2 GUI | 在宿主显示会话中运行，通常最直接；仍依赖宿主 Qt/OpenGL | 可用，但要处理 X11/Wayland、显示变量和容器权限；纯 SSH 无显示时不能凭空提供 GUI | 宿主 GUI 最直接，但不能抵消发行版不匹配风险 |
| CycloneDDS / FastDDS | 两个 ROS RMW 包都有；RoboStack 的 CycloneDDS 版本与 Unitree 固定 0.10.2 需隔离/验证 | ROS 默认 Fast DDS；Unitree SDK 使用自己的 CycloneDDS 0.10.2，边界清楚；可保留 RMW 切换开关 | 可源码构建两者，但版本、Python 3.12 ABI 和系统库组合最难维护 |
| Unitree SDK Python | 官方 SDK 要求 Python >=3.8，但固定 0.10.2；当前 Python 3.12 没有该版本的 cp312 wheel，可能触发源码构建 | Humble/Jammy 用户态以 Python 3.10 为基线，最接近官方 SDK 的 cp310 wheel 路径 | Python 3.12 + 0.10.2 是未经验证的组合，风险最高 |
| pointcloud_to_laserscan | 有预构建包，避免编译；缺包时仍需在环境内编译 | 有匹配 Humble 的二进制包；用户自己的 ROS 包只需针对容器编译 | 单包源码不算复杂，但全套 ROS/Humble 依赖先要在 Noble 上成立 |
| NVIDIA GPU | 宿主 OpenGL 最简单；CUDA 与 ROS 环境相互独立 | 当前可不透传 GPU；需要时可用 NVIDIA Container Toolkit 和 `--gpus` | GPU/GUI 直连最简单，但 Humble 用户态不受支持 |
| 实机 DDS 网络 | 直接使用宿主网络，简单 | 运行时采用 host network；容器隔离性降低，但适合先验证 UDP/DDS | 直接使用宿主网络 |
| 可复现性与维护 | 环境隔离好，包是社区重打包；需要锁定 channel/环境 | 镜像、包源和 Python 基线可固定，最容易重建和回滚 | 系统级依赖会污染宿主机，后续升级和排错成本最高 |

## 1. micromamba / RoboStack Humble

### 能力

RoboStack 提供独立环境内的 ROS 包，不需要把 ROS apt 包安装到 Ubuntu 24.04 宿主机。对本项目的关键包，当前只做了只读的 channel 元数据检查，已看到 Linux 64 位构建：

- `ros-humble-navigation2` / `ros-humble-nav2-bringup`：1.1.20。
- `ros-humble-slam-toolbox`：2.6.10。
- `ros-humble-rviz2`：11.2.26。
- `ros-humble-pointcloud-to-laserscan`：2.0.1。
- `ros-humble-rmw-cyclonedds-cpp`：1.3.4。
- `ros-humble-rmw-fastrtps-cpp`：6.2.10。

因此，RoboStack 并不是“没有 Humble 包”。它很适合作为宿主 GUI 开发、离线调参或 Docker 不可用时的备选。但上述检查只证明包元数据和单包构建存在，尚未执行 solver，也没有证明 ROS、Unitree SDK、Python 和两个 DDS 实现能在同一个环境内稳定共存。

### 主要风险：Unitree SDK 的 Python/DDS 固定版本

Unitree 官方 `unitree_sdk2_python` 的安装依赖固定为：

```text
cyclonedds==0.10.2
```

官方 PyPI 页面上的 0.10.2 wheel 覆盖到 cp310；没有可直接使用的 cp311/cp312 wheel。RoboStack 当前关键包常见的是 Python 3.11/3.12 构建，且 channel 中的 ROS CycloneDDS 包是另一个版本。若 ROS bridge 在同一 Python 进程中同时 import `rclpy` 和 Unitree SDK，动态库、Python ABI 和 CycloneDDS 版本必须实际验证，不能仅凭“Python >=3.8”判断兼容。

理论上可以单独创建 Python 3.10 环境，或把 Unitree DDS bridge 拆成独立进程再用 socket/ROS topic 连接；但这会增加项目架构和排错面。对当前要恢复的实机系统，不把这条未经验证的路径作为第一选择。

### GUI、网络和 GPU

- RViz2 直接运行在宿主显示会话中，少一层 X11/Wayland 转发。
- Unitree UDP/DDS 直接使用宿主网卡；仍必须在实机连接后验证接口、路由、DDS domain 和 CycloneDDS 配置。
- 当前主链路主要是 CPU 工作负载。RoboStack 不会自动解决 CUDA 依赖；如果后续算法需要 CUDA，仍需单独管理驱动和 toolkit。

### 适用位置

可作为 Docker 方案的开发备选，尤其适合只做 ROS 图形化调试、不加载 Unitree SDK，或需要不触碰系统 apt 的场景。若 Phase 1 中 Docker 的 SDK/GUI 路径遇到阻塞，再对 RoboStack 做一个独立的 Python 3.10 与多进程 bridge 实验。

## 2. Docker ROS Humble

### 兼容性

官方 ROS 镜像将 Humble 建立在 Ubuntu Jammy 上，和 Humble 官方支持基线一致。建议后续构建一个项目专用、固定 digest 的镜像，明确包含：

- `navigation2` / `nav2-bringup`。
- `slam_toolbox`。
- `rviz2` 及其默认插件。
- `pointcloud_to_laserscan`。
- `rmw_fastrtps_cpp`，以及需要时的 `rmw_cyclonedds_cpp`。
- Python 3.10 下的 Unitree SDK 及其固定 CycloneDDS 依赖。

官方 `ros:humble` 基础镜像偏向 ros-base；如果需要完整桌面工具，可使用 OSRF 的 Humble desktop 变体，或在项目镜像中显式加入 RViz2。无论采用哪种方式，都应在 Phase 1 固定镜像 digest，避免 `latest` 或可变 tag 导致实验结果漂移。

### DDS 设计

建议初始设计保持两个明确边界：

```text
Unitree SDK / CycloneDDS 0.10.2
          │  Python bridge
          ▼
ROS 2 graph / Fast DDS（先使用 Humble 默认 RMW）
          │
          ├── Nav2
          ├── slam_toolbox
          └── RViz2
```

ROS 2 Humble 默认 RMW 是 Fast DDS，也支持通过 `RMW_IMPLEMENTATION` 切换到 CycloneDDS。不要假设 ROS RMW 能直接订阅 Unitree 原始 DDS topic；bridge 应负责协议边界和消息转换。Phase 1 只在 loopback 或只读传感器数据上验证 Fast DDS，并保留切换到 `rmw_cyclonedds_cpp` 的测试开关。

实机通信时采用 host network，减少容器 bridge/NAT 对 DDS discovery 和 UDP 端口的影响。该模式牺牲一部分网络隔离，但不等于必须使用 `--privileged`；除非之后明确需要访问特殊设备，默认不授予全部容器能力。

### RViz2 GUI

Docker 可以运行 RViz2，但需要把容器连接到宿主显示会话，具体涉及 X11 或 Wayland 的显示变量、socket 和权限。当前机器有图形会话迹象，但 SSH 会话是否能访问该显示会话要在 Phase 1 单独验证。GUI 转发失败不应阻塞无 GUI 的节点、rosbag 和 topic 检查。

### NVIDIA GPU

当前阶段不需要把 RTX 5060 Ti 暴露给容器。若后续节点确实使用 CUDA，再安装/配置 NVIDIA Container Toolkit 并使用 GPU 透传。Ubuntu 24.04 主机在 NVIDIA Container Toolkit 的支持范围内，但这属于后续额外变更，不在本次调查或 Phase 1 之前执行。

### 代价

- 需要维护 Dockerfile、镜像 digest、bind mount 和显示配置。
- host network 会降低网络隔离，需要明确容器中哪些节点可以访问实机。
- 容器内构建的工作区和 rosbag 必须使用持久化挂载，否则容器删除后内容会消失。
- Docker 只解决用户态匹配，不会替代网卡配置、DDS domain、Unitree SDK API 验证或实机安全策略。

这些代价是可见且可回滚的，整体低于在 Noble 上移植整套 Humble 的风险。

## 3. Ubuntu 24.04 原生安装 Humble

### 官方支持边界

ROS Humble 官方 release 文档把 Ubuntu 22.04 Jammy amd64/arm64 列为 Tier 1；Ubuntu 24.04 Noble 是 Jazzy 的官方目标平台。当前 ROS 软件档案目录虽然可见 `ros-humble-noble` 的索引文件，但本次只读检查中，该 Noble Packages 列表没有找到本项目所需的 `ros-humble-navigation2`、`ros-humble-slam-toolbox`、`ros-humble-rviz2` 或 `ros-humble-pointcloud-to-laserscan` 条目；对应 Humble pool 文件仍显示为 Jammy 构建。因此不能把该索引名称当作“Ubuntu 24.04 原生 Humble 已受支持”的证据。

### 如果强行源码构建

Nav2、slam_toolbox、RViz2 和 pointcloud_to_laserscan 本身都有 ROS 2 Humble 源码，但这不等于可以在 Noble 上只编译几个包。实际需要同时处理：

- ROS 2 核心、消息包、Python 绑定、ament/colcon 和系统依赖。
- Qt/OpenGL/RViz 与 Noble 的 GUI 库。
- Fast DDS、CycloneDDS、RMW 插件及其动态库搜索路径。
- Python 3.12 ABI 与 Unitree 固定的 CycloneDDS 0.10.2。
- Ceres、Eigen、SuiteSparse、PCL、tf2 等 slam/Nav2 依赖的版本组合。

pointcloud_to_laserscan 单包属于标准 C++ ament 包，源码编译难度本身不高；真正困难的是它所依赖的整套 Humble/Noble 环境。历史上 Humble 源码构建中也出现过 tf2_sensor_msgs target 缺失等依赖问题。原生方案的优点只是网络和 GUI 最直接，不能抵消发行版支持与维护风险。

## 按项目需求的最终判断

### Nav2

Nav2 在 Humble 上是成熟、已发布的包集，包含 AMCL、map server、costmap、planner、controller、behavior tree 和 bringup 等组件。Docker 的 Jammy/Humble 二进制链路最接近官方发布验证；RoboStack 有相应预构建包，但需要额外做环境 solver 和运行时验证；原生 Noble 只能走未受支持的组合。

### slam_toolbox

slam_toolbox 是 Humble 上常用的 ROS 2 SLAM 库，依赖 `/scan`、里程计和 TF，并可向 Nav2 提供地图。三种方案在“源码是否存在”层面都可行，但只有 Docker 直接落在官方 Humble/Jammy 基线。RoboStack 可避免编译，原生 Noble 需承担整套依赖移植。

### RViz2

Docker 和 RoboStack 都可以运行 RViz2；差别是 Docker 要处理显示转发，RoboStack/原生直接使用宿主 GUI。由于本项目还需要实机 DDS 和 Unitree SDK，不能仅凭 RViz2 在宿主显示成功就判定环境适合实机运行。

### CycloneDDS / FastDDS

ROS 2 Humble 默认使用 Fast DDS，也提供 CycloneDDS RMW。Unitree SDK 自己固定使用 CycloneDDS 0.10.2。推荐在 bridge 中把“Unitree 原始 DDS”和“ROS 2 graph RMW”视为两个可独立配置的层：先用 ROS 默认 Fast DDS，必要时再做 ROS CycloneDDS 对照测试。这样不强迫 RoboStack 的 CycloneDDS 版本直接满足 Unitree 的 Python pin。

### Unitree SDK Python

这是方案选择的决定性因素。宿主机 Python 3.12 不是当前最稳妥的 Unitree SDK 0.10.2 wheel 目标；RoboStack 的 Python 3.12 预构建 ROS 包也不能自动解决这一点。Docker 的 Humble/Jammy Python 3.10 与官方 ROS/SDK 年代匹配，最适合先建立只读传感器 bridge。即使如此，仍需 Phase 1 做 import、网络接收和消息发布验证，不能把 SDK 示例中的运动控制调用带入测试。

### pointcloud_to_laserscan

优先使用 Docker 或 RoboStack 的预构建包。只有在包缺失、需要改源码或要编译项目自有节点时才编译。不要因为这个单包是 C++ 包，就把整个 ROS Humble 迁移到 Noble。

### NVIDIA GPU

当前 G1 LiDAR SLAM + Nav2 主链路主要依赖 CPU、DDS、PCL/TF、Qt/OpenGL 和网络，不要求 CUDA。GPU 透传会增加 Docker 和驱动配置变量，故延后到明确需要 FAST-LIO2 或其他 CUDA 算法时再启用。

## Phase 1（确认后）的验收边界

确认后建议按以下顺序验证，但本文件生成时尚未执行：

1. 固定 Docker 基础镜像 digest 和依赖版本，构建可重现的 Humble/Jammy 项目镜像。
2. 验证 Nav2、slam_toolbox、RViz2、pointcloud_to_laserscan、Fast DDS/CycloneDDS RMW 包能被 ROS 找到。
3. 在 Python 3.10 容器内验证 `rclpy`、Unitree SDK 和 `cyclonedds==0.10.2` 的 import；不运行运动示例。
4. 先做 loopback topic、TF、LaserScan/PointCloud2 转换和 RViz2 GUI 测试，再做只读传感器 DDS 测试。
5. 仅在确认网线、网卡、路由和安全开关后接入 G1；bridge 默认 `enable_motion=false`，不调用 `SetFsmId`、`Start`、`SetVelocity` 或真实 `/cmd_vel`。
6. 若 Docker GUI 或 SDK 兼容性无法通过验收，再单独评估 RoboStack，不把两套环境混用或交叉 source。

## 参考资料

- [ROS 2 Humble release / supported platforms](https://docs.ros.org/en/rolling/Releases/Release-Humble-Hawksbill.html)
- [ROS 2 Jazzy Ubuntu 24.04 binary installation](https://docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Install-Binary.html)
- [Official ROS Docker image metadata](https://github.com/docker-library/official-images/blob/master/library/ros)
- [Docker ROS 2 guide](https://docs.docker.com/guides/ros2/)
- [ROS 2 Humble multiple RMW implementations](https://docs.ros.org/en/humble/How-To-Guides/Working-with-multiple-RMW-implementations.html)
- [RoboStack Humble channel](https://robostack.github.io/humble.html)
- [RoboStack micromamba installation guidance](https://robostack.github.io/micromamba.html)
- [RoboStack navigation2 package metadata](https://prefix.dev/channels/robostack-humble/packages/ros-humble-navigation2)
- [RoboStack slam_toolbox package metadata](https://prefix.dev/channels/robostack-humble/packages/ros-humble-slam-toolbox)
- [RoboStack pointcloud_to_laserscan package metadata](https://prefix.dev/channels/robostack-humble/packages/ros-humble-pointcloud-to-laserscan)
- [Official Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [Unitree SDK2 Python setup.py and dependency pin](https://raw.githubusercontent.com/unitreerobotics/unitree_sdk2_python/master/setup.py)
- [cyclonedds 0.10.2 PyPI wheel history](https://pypi.org/project/cyclonedds/0.10.2/)
- [NVIDIA Container Toolkit supported platforms](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/supported-platforms.html)
- [ROS package archive lists](https://repo.ros2.org/ubuntu/main/lists/)
- [ROS Humble Nav2 pool artifacts](https://repo.ros2.org/ubuntu/main/pool/main/r/ros-humble-nav2-bt-navigator/)

**决策状态：推荐 Docker ROS 2 Humble/Jammy；等待用户确认后再进入 Phase 1。**
