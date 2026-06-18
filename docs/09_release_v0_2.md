# 09 Release Notes: v0.2

## Summary

v0.2 turns the repository from a simulation-only workflow into a simulation-to-real transition workflow.

## Added

- Real G1 wired DDS read-only checklist
- Real robot data pipeline notes
- Explicit safety boundary for real-robot work
- 3090 simulation workstation vs 5060Ti real-robot workstation split
- Read-only network check script
- Read-only rosbag recording script
- FAST-LIO real Mid360-style template
- Unitree DDS wired environment template
- `enable_cmd_vel_forwarding` parameter in `g1_proxy_bridge`
- `g1_topic_monitor` read-only ROS2 executable

## Changed

- README now separates v0.1 simulation progress from v0.2 real-robot transition progress.
- Roadmap now prioritizes safe data acquisition before Nav2 real-robot execution.
- Launch file exposes safety toggles.

## Not included

- No real G1 locomotion control code
- No official Unitree SDK source copy
- No Isaac Sim proprietary assets
- No third-party FAST-LIO source copy
- No large bags or maps

## Version meaning

```text
v0.1 = Isaac Sim G1 proxy + FAST-LIO mapping workflow
v0.2 = Real G1 wired DDS read-only data pipeline + safety-first migration notes
```
