# 07 Real G1 Wired DDS Read-only Checklist

This document records the v0.2 real-robot transition plan.

The current goal is **not** to make G1 walk. The current goal is to reliably receive sensor / SLAM data on the lab workstation and record reusable bags.

## 1. Machine split

| Machine | Role |
|---|---|
| RTX 3090 workstation | Isaac Sim, FAST-LIO/Nav2 simulation, offline map processing |
| 5060Ti lab workstation | Connect to real G1, receive DDS/ROS2 data, record bags, visualize point cloud/map |
| G1 onboard computer | Unitree SDK2 / official robot-side software |

Known local paths from the current project stage:

```text
5060Ti workstation:
  ~/G1_SLAM
  g1_slam
  wired NIC example: enp6s0

G1 onboard computer:
  ~/unitree_sdk2-main
  ~/unitree_sdk2_python
```

## 2. Network policy

WiFi can be useful for `ping` and `ssh`, but DDS point cloud reception was observed as unstable / zero in the current stage. Therefore the default real-robot data route is:

```text
G1 onboard computer
        ↓ wired Ethernet / DDS
5060Ti lab workstation
        ↓ ROS2 topic receive / bag record / visualization
```

## 3. Safety boundary

Do **not** run movement-related commands during this phase.

Avoid:

```bash
g1_loco_client move
set_velocity
official navigation that moves the robot
Nav2 /cmd_vel connected to real locomotion
```

Allowed in this phase:

```bash
ping
ssh
ip addr
ros2 topic list
ros2 topic echo --once
ros2 topic hz
ros2 bag record
rviz2 visualization
```

## 4. Read-only check

From the repository root:

```bash
bash scripts/real_g1_network_readonly_check.sh
```

If the G1 IP is known:

```bash
G1_IP=<replace_with_g1_ip> bash scripts/real_g1_network_readonly_check.sh
```

## 5. Topic discovery

Because topic names depend on the Unitree/SLAM software version and launch mode, first list topics:

```bash
ros2 topic list
```

Then check likely sensor topics:

```bash
ros2 topic hz <pointcloud_topic>
ros2 topic hz <imu_topic>
ros2 topic echo <imu_topic> --once
```

Record actual topic names into `docs/progress_log.md`.
