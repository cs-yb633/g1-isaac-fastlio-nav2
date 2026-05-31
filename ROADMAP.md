# Roadmap

## V0.1 Current Release

- Organize project documentation.
- Provide `g1_proxy_bridge` ROS 2 package.
- Provide FAST-LIO and Nav2 configuration templates.
- Provide troubleshooting and reproducibility scripts.

## V0.2 FAST-LIO Localization Bridge

Planned:

- Add node to convert FAST-LIO odometry output into Nav2-compatible TF.
- Clarify frame responsibility:

```text
map → odom → g1_base_link
```

- Add launch file for FAST-LIO + G1 proxy bridge.

## V0.3 Minimal Nav2 Demo

Planned:

- Add minimal Nav2 launch/config.
- Use FAST-LIO localization instead of AMCL.
- Send RViz 2D Nav Goal and drive `/g1/cmd_vel`.

## V0.4 Real G1 Migration Notes

Planned:

- Replace Carter proxy with Unitree G1 real robot interface.
- Map `/g1/cmd_vel`, `/g1/odom`, `/g1/lidar_points`, `/g1/imu` to real sensor/control topics.
- Record real-world bags and compare with Isaac Sim.
