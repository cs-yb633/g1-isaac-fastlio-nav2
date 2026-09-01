# 重装后主机审计

审计日期：2026-08-31

## 已确认

| 项目 | 当前值 |
|---|---|
| 操作系统 | Ubuntu 24.04.4 LTS (Noble), x86_64 |
| 内核 | 7.0.0-30-generic |
| Python | 3.12.3 |
| Docker | 29.1.3，daemon 可用，overlayfs，cgroup v2 |
| Docker Compose | 2.40.3，安装为当前用户 CLI 插件 |
| GPU | NVIDIA GeForce RTX 5060 Ti，驱动 580.173.02 |
| 有线网卡 | `enp6s0`，当前 `NO-CARRIER`，无 IP |
| 无线网卡 | `wlp5s0`，当前已联网 |
| 宿主 ROS 2 | 未安装，符合容器隔离方案 |

## 结论

- Docker 运行条件已经满足，不需要在 Noble 宿主机安装 ROS 2 Humble。
- 当前没有连接 G1 的网线，无法验证历史地址、DDS 话题或机器人软件版本。
- GPU 不是 SLAM Toolbox + Nav2 恢复链路的前置依赖，当前容器不透传 GPU。
- 接机后的第一阶段只允许配置有线地址和读取数据，不允许发送运动命令。
