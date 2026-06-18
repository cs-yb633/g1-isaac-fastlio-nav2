# Roadmap

## v0.1: Isaac Sim G1 proxy workflow

- [x] Import Unitree G1 URDF into Isaac Sim
- [x] Attach G1 visual model to Nova Carter motion proxy
- [x] Hide Carter visual elements and keep its motion/sensor capability
- [x] Publish G1-style `/g1/*` ROS 2 interface
- [x] Use 3D LiDAR + IMU topics for FAST-LIO mapping tests

## v0.2: Real G1 read-only data pipeline

- [x] Split workstation roles: 3090 for simulation, 5060Ti for real robot connection
- [x] Prefer wired DDS over WiFi for real point cloud reception
- [x] Add read-only network / topic check scripts
- [x] Add read-only rosbag recording templates
- [x] Add safety notes forbidding real movement commands during data stage
- [ ] Confirm actual real G1 PointCloud2, IMU, odom/pose topic names
- [ ] Record first stable real G1 sensor bag
- [ ] Replay real bag offline on 3090/5060Ti
- [ ] Run FAST-LIO or official SLAM pipeline on recorded data
- [ ] Export 3D map and generate 2D `pgm/yaml`

## v0.3: Localization and Nav2 in simulation

- [ ] Convert FAST-LIO/SLAM output to stable odom / map interface
- [ ] Align TF tree: `map -> odom -> g1_base_link -> sensors`
- [ ] Configure Nav2 costmaps with generated 2D map
- [ ] Send RViz goal and verify A → B navigation in Isaac Sim
- [ ] Add velocity safety layer for future real-robot execution

## v0.4: Real G1 navigation preparation

- [ ] Keep Nav2 output disconnected from real locomotion by default
- [ ] Add command gate / deadman switch / max velocity limiter
- [ ] Test planning output with logs only
- [ ] Connect to G1 LocoClient only after safety review
- [ ] Replace Carter proxy with real execution layer gradually
