"""Pure transform math for projecting 3-D odometry onto a planar base frame."""

from dataclasses import dataclass
import math
from typing import Tuple

from .odom_validation import (
    DEFAULT_MAX_ABS_POSITION_M,
    DEFAULT_QUATERNION_NORM_TOLERANCE,
    ValidationRules,
    normalise_quaternion,
    validate_pose_components,
)


@dataclass(frozen=True)
class Transform:
    translation: Tuple[float, float, float]
    rotation: Tuple[float, float, float, float]  # x, y, z, w


def _multiply_quaternions(left, right):
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return (
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
        lw * rw - lx * rx - ly * ry - lz * rz,
    )


def planar_odometry_transforms(
    position,
    quaternion,
    norm_tolerance=DEFAULT_QUATERNION_NORM_TOLERANCE,
    max_abs_position_m=DEFAULT_MAX_ABS_POSITION_M,
):
    """Return ``odom->base_footprint`` and ``base_footprint->robot_center``.

    The first transform keeps x/y/yaw only. The second is the exact residual
    ``inverse(T_odom_base_footprint) * T_odom_robot_center``. No filtering,
    integration, or time handling occurs in this function.
    """
    rules = ValidationRules(
        quaternion_norm_tolerance=norm_tolerance,
        max_abs_position_m=max_abs_position_m,
    )
    validation = validate_pose_components(position, quaternion, rules)
    if validation.errors:
        raise ValueError(", ".join(validation.errors))

    x, y, z = position
    q_robot = normalise_quaternion(quaternion, norm_tolerance)
    qx, qy, qz, qw = q_robot
    yaw = math.atan2(
        2.0 * (qw * qz + qx * qy),
        1.0 - 2.0 * (qy * qy + qz * qz),
    )
    half_yaw = yaw / 2.0
    q_planar = (0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw))
    q_planar_inverse = (0.0, 0.0, -q_planar[2], q_planar[3])
    q_residual = _multiply_quaternions(q_planar_inverse, q_robot)
    q_residual = normalise_quaternion(q_residual, 1.0e-9)

    return (
        Transform((x, y, 0.0), q_planar),
        Transform((0.0, 0.0, z), q_residual),
    )
