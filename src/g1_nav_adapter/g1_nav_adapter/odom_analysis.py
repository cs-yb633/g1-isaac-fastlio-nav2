"""Analyze CSV files produced by dog_odom_probe without ROS graph access."""

import argparse
import csv
import json
import math

from .odom_validation import DEFAULT_LARGE_JUMP_M


def _float(row, name):
    try:
        return float(row[name])
    except (KeyError, TypeError, ValueError):
        return math.nan


def _bool(row, name):
    return str(row.get(name, "")).lower() == "true"


def _normalise_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def quaternion_to_rpy(quaternion):
    x, y, z, w = quaternion
    norm = math.sqrt(sum(value * value for value in quaternion))
    if not math.isfinite(norm) or norm <= 1.0e-12:
        return math.nan, math.nan, math.nan
    x, y, z, w = (value / norm for value in quaternion)
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    pitch_sine = max(-1.0, min(1.0, 2.0 * (w * y - z * x)))
    pitch = math.asin(pitch_sine)
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return roll, pitch, yaw


def analyze_rows(rows, large_jump_m=DEFAULT_LARGE_JUMP_M):
    if not rows:
        raise ValueError("input contains no odometry samples")
    positions = [
        (_float(row, "position_x"), _float(row, "position_y"), _float(row, "position_z"))
        for row in rows
    ]
    stamps = [int(row["header_stamp_ns"]) for row in rows]
    rpy = [
        quaternion_to_rpy(
            tuple(
                _float(row, field)
                for field in (
                    "orientation_x",
                    "orientation_y",
                    "orientation_z",
                    "orientation_w",
                )
            )
        )
        for row in rows
    ]
    dt = [
        (current - previous) / 1_000_000_000.0
        for previous, current in zip(stamps, stamps[1:])
    ]
    valid_mask = [_bool(row, "valid") for row in rows]
    valid_poses = [
        (position, angles)
        for position, angles, valid in zip(positions, rpy, valid_mask)
        if valid
        and all(math.isfinite(value) for value in position)
        and all(math.isfinite(value) for value in angles)
    ]
    jumps = [
        math.sqrt(sum((b - a) ** 2 for a, b in zip(previous, current)))
        for previous, current in zip(positions, positions[1:])
        if all(math.isfinite(value) for value in previous + current)
    ]
    valid_positions = [pose[0] for pose in valid_poses]
    path_length = sum(
        math.hypot(current[0] - previous[0], current[1] - previous[1])
        for previous, current in zip(valid_positions, valid_positions[1:])
    )
    duration = (stamps[-1] - stamps[0]) / 1_000_000_000.0
    invalid_count = sum(not valid for valid in valid_mask)
    result = {
        "duration_sec": duration,
        "sample_count": len(rows),
        "mean_rate_hz": ((len(rows) - 1) / duration if duration > 0.0 else None),
        "min_dt_sec": min(dt) if dt else None,
        "max_dt_sec": max(dt) if dt else None,
        "timestamp_regressions": sum(value <= 0.0 for value in dt),
        "invalid_samples": invalid_count,
        "rejected_samples": invalid_count,
        "large_jumps": sum(value > large_jump_m for value in jumps),
        "large_jump_threshold_m": large_jump_m,
        "maximum_jump_m": max(jumps) if jumps else 0.0,
        "path_length_m": path_length,
    }
    if not valid_poses:
        result.update(
            {
                "initial_pose": None,
                "final_pose": None,
                "delta": None,
                "max_abs_roll_rad": None,
                "max_abs_pitch_rad": None,
                "net_displacement_m": None,
                "closure_error_m": None,
                "yaw_closure_error_rad": None,
            }
        )
        return result

    first, first_rpy = valid_poses[0]
    last, last_rpy = valid_poses[-1]
    delta = tuple(end - start for start, end in zip(first, last))
    yaw_delta = _normalise_angle(last_rpy[2] - first_rpy[2])
    result.update(
        {
            "initial_pose": {
                "x": first[0],
                "y": first[1],
                "z": first[2],
                "yaw": first_rpy[2],
            },
            "final_pose": {
                "x": last[0],
                "y": last[1],
                "z": last[2],
                "yaw": last_rpy[2],
            },
            "delta": {
                "x": delta[0],
                "y": delta[1],
                "z": delta[2],
                "yaw": yaw_delta,
            },
            "max_abs_roll_rad": max(abs(value[0]) for _, value in valid_poses),
            "max_abs_pitch_rad": max(abs(value[1]) for _, value in valid_poses),
            "net_displacement_m": math.hypot(delta[0], delta[1]),
            "closure_error_m": math.hypot(delta[0], delta[1]),
            "yaw_closure_error_rad": yaw_delta,
        }
    )
    return result


def analyze_csv(path, large_jump_m=DEFAULT_LARGE_JUMP_M):
    with open(path, newline="", encoding="utf-8") as stream:
        return analyze_rows(list(csv.DictReader(stream)), large_jump_m)


def main(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="dog_odom_probe CSV path")
    parser.add_argument("--large-jump-m", type=float, default=DEFAULT_LARGE_JUMP_M)
    parsed = parser.parse_args(args)
    if not math.isfinite(parsed.large_jump_m) or parsed.large_jump_m <= 0.0:
        parser.error("--large-jump-m must be finite and positive")
    print(json.dumps(analyze_csv(parsed.input, parsed.large_jump_m), indent=2, sort_keys=True))
