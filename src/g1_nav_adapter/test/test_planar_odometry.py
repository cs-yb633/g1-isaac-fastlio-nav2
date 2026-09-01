import math
import random

import pytest

from g1_nav_adapter.planar_odometry import planar_odometry_transforms


EPSILON = 1.0e-11


def _quaternion_from_rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def _multiply_quaternions(left, right):
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    return (
        lw * rx + lx * rw + ly * rz - lz * ry,
        lw * ry - lx * rz + ly * rw + lz * rx,
        lw * rz + lx * ry - ly * rx + lz * rw,
        lw * rw - lx * rx - ly * ry - lz * rz,
    )


def _rotate_vector(quaternion, vector):
    conjugate = (-quaternion[0], -quaternion[1], -quaternion[2], quaternion[3])
    rotated = _multiply_quaternions(
        _multiply_quaternions(quaternion, (*vector, 0.0)), conjugate
    )
    return rotated[:3]


def _compose(left, right):
    rotated = _rotate_vector(left.rotation, right.translation)
    translation = tuple(a + b for a, b in zip(left.translation, rotated))
    rotation = _multiply_quaternions(left.rotation, right.rotation)
    return translation, rotation


def _quaternion_error(actual, expected):
    direct = math.sqrt(sum((a - b) ** 2 for a, b in zip(actual, expected)))
    antipodal = math.sqrt(sum((a + b) ** 2 for a, b in zip(actual, expected)))
    return min(direct, antipodal)


def _assert_decomposition(position, rpy):
    original_quaternion = _quaternion_from_rpy(*rpy)
    odom_to_base, base_to_robot = planar_odometry_transforms(
        position, original_quaternion
    )
    reconstructed_position, reconstructed_quaternion = _compose(
        odom_to_base, base_to_robot
    )
    assert reconstructed_position == pytest.approx(position, abs=EPSILON)
    assert _quaternion_error(reconstructed_quaternion, original_quaternion) < EPSILON
    assert odom_to_base.translation[2] == 0.0
    assert odom_to_base.rotation[0] == 0.0
    assert odom_to_base.rotation[1] == 0.0


def test_case_a_all_pose_components_nonzero():
    _assert_decomposition((2.0, -3.0, 0.42), (0.2, -0.3, 0.7))


def test_case_b_yaw_only():
    _assert_decomposition((0.0, 0.0, 0.0), (0.0, 0.0, 1.2))


def test_case_c_visible_humanoid_roll_pitch():
    _assert_decomposition((0.4, 0.8, 0.73), (0.45, -0.35, -1.1))


@pytest.mark.parametrize("yaw", [math.pi - 1.0e-9, -math.pi + 1.0e-9])
def test_case_d_yaw_near_pi(yaw):
    _assert_decomposition((-1.0, 2.0, 0.7), (0.1, -0.2, yaw))


def test_case_e_seeded_random_valid_poses():
    generator = random.Random(20260901)
    for _ in range(250):
        position = tuple(generator.uniform(-20.0, 20.0) for _ in range(3))
        rpy = (
            generator.uniform(-0.7, 0.7),
            generator.uniform(-0.7, 0.7),
            generator.uniform(-math.pi, math.pi),
        )
        _assert_decomposition(position, rpy)


def test_huge_but_finite_position_is_rejected():
    with pytest.raises(ValueError, match="position_absolute_limit"):
        planar_odometry_transforms(
            (4.009699584e24, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
