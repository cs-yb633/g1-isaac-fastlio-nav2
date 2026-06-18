#!/usr/bin/env bash
set -euo pipefail

# Read-only check for the real G1 data stage.
# This script never publishes velocity or locomotion commands.

IFACE="${G1_WIRED_IFACE:-enp6s0}"
G1_IP="${G1_IP:-}"

printf '\n[1/5] Wired interface check: %s\n' "$IFACE"
if ip addr show "$IFACE" >/dev/null 2>&1; then
  ip addr show "$IFACE"
else
  echo "WARN: interface $IFACE not found. Set G1_WIRED_IFACE=<your_iface> if needed."
  ip -brief addr || true
fi

printf '\n[2/5] Optional ping check\n'
if [[ -n "$G1_IP" ]]; then
  ping -c 3 "$G1_IP" || true
else
  echo "G1_IP is not set. Skip ping. Example: G1_IP=192.168.xxx.xxx bash scripts/real_g1_network_readonly_check.sh"
fi

printf '\n[3/5] ROS environment\n'
printenv | grep -E 'ROS_DOMAIN_ID|RMW_IMPLEMENTATION|CYCLONEDDS_URI|FASTRTPS_DEFAULT_PROFILES_FILE' || true

printf '\n[4/5] ROS2 topic list\n'
ros2 topic list || {
  echo "ERROR: ros2 topic list failed. Source ROS2/workspace first."
  exit 1
}

printf '\n[5/5] Safe reminder\n'
echo "This was a read-only check. Do not run movement commands in v0.2 real-robot stage."
