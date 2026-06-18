# 08 Real Robot Data Pipeline

v0.2 adds a safe real-robot data pipeline. The pipeline is intentionally read-only at first.

## 1. Current pipeline target

```text
Real G1 sensor / official SLAM data
        ↓
DDS / ROS2 receive on 5060Ti workstation
        ↓
rosbag record
        ↓
RViz point cloud / map visualization
        ↓
3D map or official map output
        ↓
2D pgm/yaml map generation
        ↓ later
Nav2 map loading and planning
        ↓ later, after safety isolation
G1 locomotion execution
```

## 2. What to record

The exact topic names must be verified on the real robot. Common categories to record:

- PointCloud2 from 3D LiDAR
- IMU
- Odometry or pose if available
- `/tf`
- `/tf_static`
- official SLAM map / path / pose topics if available

Use the script template:

```bash
bash scripts/record_real_g1_bag_readonly.sh
```

Override topics when needed:

```bash
TOPICS="/actual_cloud_topic /actual_imu_topic /actual_odom_topic /tf /tf_static" \
  BAG_NAME="g1_real_readonly_01" \
  bash scripts/record_real_g1_bag_readonly.sh
```

## 3. Official SLAM route

For the current stage, the practical route is:

```text
official SLAM / sensor data
        ↓
record bag
        ↓
convert or export map
        ↓
2D pgm/yaml
        ↓
Nav2 planning test
        ↓
/cmd_vel execution layer only after safety checks
```

The official `1102` navigation route is treated as a backup/reference route, not the main open-source pipeline.

## 4. Relation to FAST-LIO

FAST-LIO remains the preferred 3D LiDAR + IMU route for the project, especially for simulation and offline experiments. On the real robot, the first requirement is to record stable sensor bags. After that, the same bag can be used to test FAST-LIO offline before any online control is attempted.

## 5. Data not included in this repository

Do not commit large generated files:

```text
*.db3
*.mcap
*.bag
*.pcd
*.ply
*.pgm
```

Instead, document how they were generated and optionally publish them through a release asset or external storage if the license and size allow it.
