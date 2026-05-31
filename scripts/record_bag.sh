#!/usr/bin/env bash
set -euo pipefail

NAME="${1:-g1_mapping_$(date +%Y%m%d_%H%M%S)}"

mkdir -p bags

echo "Recording bag: bags/${NAME}"
ros2 bag record \
  -o "bags/${NAME}" \
  /g1/lidar_points \
  /g1/imu \
  /g1/odom \
  /g1/cmd_vel \
  /tf \
  /tf_static \
  /clock
