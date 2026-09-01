"""Shared, ROS-independent validation rules for G1 odometry."""

from dataclasses import dataclass
import math
from typing import Optional, Sequence, Tuple


DEFAULT_ODOM_FRAME = "odom"
DEFAULT_CHILD_FRAME = "robot_center"
DEFAULT_QUATERNION_NORM_TOLERANCE = 1.0e-3
DEFAULT_MAX_ABS_POSITION_M = 1000.0
DEFAULT_LARGE_JUMP_M = 0.5


@dataclass(frozen=True)
class ValidationRules:
    odom_frame: str = DEFAULT_ODOM_FRAME
    child_frame: str = DEFAULT_CHILD_FRAME
    quaternion_norm_tolerance: float = DEFAULT_QUATERNION_NORM_TOLERANCE
    max_abs_position_m: float = DEFAULT_MAX_ABS_POSITION_M

    def __post_init__(self):
        for name, frame in (
            ("odom_frame", self.odom_frame),
            ("child_frame", self.child_frame),
        ):
            if not isinstance(frame, str) or not frame or frame.startswith("/"):
                raise ValueError(
                    f"{name} must be a non-empty TF frame without a leading '/'"
                )
        if (
            not math.isfinite(self.quaternion_norm_tolerance)
            or self.quaternion_norm_tolerance < 0.0
        ):
            raise ValueError(
                "quaternion_norm_tolerance must be finite and non-negative"
            )
        if (
            not math.isfinite(self.max_abs_position_m)
            or self.max_abs_position_m <= 0.0
        ):
            raise ValueError("max_abs_position_m must be finite and positive")


@dataclass(frozen=True)
class ValidationResult:
    errors: Tuple[str, ...]
    quaternion_norm: float
    position_magnitude: float

    @property
    def valid(self):
        return not self.errors


def _finite(values: Sequence[float]) -> bool:
    return all(math.isfinite(value) for value in values)


def quaternion_norm(quaternion: Sequence[float]) -> float:
    if len(quaternion) != 4:
        return math.nan
    try:
        return math.sqrt(sum(component * component for component in quaternion))
    except (TypeError, ValueError, OverflowError):
        return math.nan


def normalise_quaternion(
    quaternion: Sequence[float], norm_tolerance: float
) -> Tuple[float, float, float, float]:
    norm = quaternion_norm(quaternion)
    if not _finite(quaternion) or not math.isfinite(norm):
        raise ValueError("quaternion components must be finite")
    if norm <= 1.0e-12:
        raise ValueError("quaternion norm is zero")
    if abs(norm - 1.0) > norm_tolerance:
        raise ValueError(
            f"quaternion norm {norm:.9g} differs from one by more than "
            f"{norm_tolerance:.9g}"
        )
    return tuple(component / norm for component in quaternion)


def validate_pose_components(position, quaternion, rules: ValidationRules):
    errors = []
    if len(position) != 3 or not _finite(position):
        errors.append("position_nonfinite")
        position_magnitude = math.nan
    else:
        position_magnitude = math.sqrt(sum(value * value for value in position))
        if any(abs(value) > rules.max_abs_position_m for value in position):
            errors.append("position_absolute_limit")

    norm = quaternion_norm(quaternion)
    if len(quaternion) != 4 or not _finite(quaternion) or not math.isfinite(norm):
        errors.append("quaternion_nonfinite")
    elif norm <= 1.0e-12:
        errors.append("quaternion_zero_norm")
    elif abs(norm - 1.0) > rules.quaternion_norm_tolerance:
        errors.append("quaternion_norm")
    return ValidationResult(tuple(errors), norm, position_magnitude)


def validate_odometry_fields(
    *,
    frame_id: str,
    child_frame_id: str,
    stamp_ns: int,
    position,
    quaternion,
    linear_velocity,
    angular_velocity,
    rules: ValidationRules,
    previous_valid_stamp_ns: Optional[int] = None,
):
    pose_result = validate_pose_components(position, quaternion, rules)
    errors = list(pose_result.errors)
    if frame_id != rules.odom_frame:
        errors.append("frame_id")
    if child_frame_id != rules.child_frame:
        errors.append("child_frame_id")
    if not isinstance(stamp_ns, int) or stamp_ns <= 0:
        errors.append("timestamp")
    elif previous_valid_stamp_ns is not None and stamp_ns <= previous_valid_stamp_ns:
        errors.append("timestamp_nonmonotonic")
    if len(linear_velocity) != 3 or not _finite(linear_velocity):
        errors.append("linear_velocity_nonfinite")
    if len(angular_velocity) != 3 or not _finite(angular_velocity):
        errors.append("angular_velocity_nonfinite")
    return ValidationResult(
        tuple(errors), pose_result.quaternion_norm, pose_result.position_magnitude
    )
