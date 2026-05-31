#!/usr/bin/env bash
set -euo pipefail

check_tf() {
  local parent="$1"
  local child="$2"
  echo
  echo "== TF: ${parent} -> ${child} =="
  timeout 5 ros2 run tf2_ros tf2_echo "$parent" "$child" || true
}

check_tf odom g1_base_link
check_tf g1_base_link g1_lidar_link
check_tf g1_base_link g1_imu_link
