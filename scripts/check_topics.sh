#!/usr/bin/env bash
set -euo pipefail

TOPICS=(
  "/g1/cmd_vel"
  "/g1/odom"
  "/g1/lidar_points"
  "/g1/imu"
  "/cmd_vel"
  "/chassis/odom"
  "/front_3d_lidar/lidar_points"
  "/chassis/imu"
)

echo "== ROS 2 topic list check =="
ros2 topic list -t | grep -E "(/g1/|/cmd_vel|/chassis/odom|/front_3d_lidar/lidar_points|/chassis/imu)" || true

echo
for topic in "${TOPICS[@]}"; do
  if ros2 topic list | grep -qx "$topic"; then
    echo "[OK] $topic"
  else
    echo "[MISS] $topic"
  fi
done

echo
echo "== Frequency quick check =="
for topic in "/g1/lidar_points" "/g1/imu" "/g1/odom"; do
  if ros2 topic list | grep -qx "$topic"; then
    echo
    echo "--- $topic ---"
    timeout 5 ros2 topic hz "$topic" || true
  fi
done
