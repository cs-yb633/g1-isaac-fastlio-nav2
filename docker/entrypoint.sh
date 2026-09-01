#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /opt/unitree_ros2/cyclonedds_ws/install/setup.bash

if [[ -n "${G1_NETWORK_INTERFACE:-}" ]]; then
  export CYCLONEDDS_URI="<CycloneDDS><Domain><General><Interfaces><NetworkInterface name=\"${G1_NETWORK_INTERFACE}\" priority=\"default\" multicast=\"default\" /></Interfaces></General></Domain></CycloneDDS>"
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

if [[ -f /workspace/install/setup.bash ]]; then
  source /workspace/install/setup.bash
fi

set -u

exec "$@"
