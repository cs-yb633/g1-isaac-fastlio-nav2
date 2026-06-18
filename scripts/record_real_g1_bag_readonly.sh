#!/usr/bin/env bash
set -euo pipefail

# Read-only rosbag recording template for real G1 data.
# It only records topics and never publishes motion commands.

BAG_NAME="${BAG_NAME:-g1_real_readonly_$(date +%Y%m%d_%H%M%S)}"
TOPICS="${TOPICS:-/g1/lidar_points /g1/imu /g1/odom /tf /tf_static}"

printf '\nRecording bag: %s\n' "$BAG_NAME"
printf 'Topics: %s\n\n' "$TOPICS"
echo "Reminder: verify actual real G1 topic names with 'ros2 topic list' before recording."
echo "This script is read-only and does not command robot motion."

ros2 bag record -o "$BAG_NAME" $TOPICS
