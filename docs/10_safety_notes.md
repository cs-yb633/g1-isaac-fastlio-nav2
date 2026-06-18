# 10 Safety Notes for Real G1 Work

This repository is designed to support a safety-first transition from simulation to real G1.

## 1. Current real-robot rule

During the v0.2 phase, the robot should not be commanded to move.

The allowed work is:

```text
data receive
network check
DDS check
topic echo / hz
rosbag record
RViz visualization
offline SLAM / map conversion
```

The disallowed work is:

```text
running official navigation that moves the robot
sending /cmd_vel to the real locomotion stack
running g1_loco_client move
running set_velocity
connecting Nav2 output directly to real G1 locomotion
```

## 2. Why this rule exists

The project is currently validating the perception and navigation software stack. A wrong DDS domain, frame transform, velocity topic, or controller bridge can cause unexpected movement if connected directly to the real robot.

## 3. Safe migration order

1. Verify wired DDS data reception.
2. Record rosbag without motion commands.
3. Replay bag offline.
4. Run FAST-LIO or official SLAM processing offline.
5. Generate map.
6. Load map into Nav2 without real execution.
7. Simulate `/cmd_vel` output in a sandbox.
8. Add a velocity safety layer.
9. Only then consider real locomotion execution.

## 4. Recommended command habit

Before running any command, classify it as one of:

```text
READ-ONLY: safe for v0.2
MOTION-RELATED: do not run in v0.2
UNKNOWN: inspect before running
```

When in doubt, do not execute it on the real robot.
