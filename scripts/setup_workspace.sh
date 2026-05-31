#!/usr/bin/env bash
set -euo pipefail

WS="${1:-$HOME/mayibo/ws_g1}"

echo "Workspace: $WS"
mkdir -p "$WS/src"

if [ ! -f /opt/ros/humble/setup.bash ]; then
  echo "ERROR: /opt/ros/humble/setup.bash not found. Please install ROS 2 Humble first."
  exit 1
fi

source /opt/ros/humble/setup.bash
cd "$WS"
colcon build --symlink-install --packages-select g1_proxy_bridge

echo
echo "Done. Run:"
echo "  source $WS/install/setup.bash"
echo "  ros2 launch g1_proxy_bridge g1_proxy_bridge.launch.py"
