"""Unit tests for cmd_vel validation, limiting, and watchdog behavior."""

import math

import pytest

from g1_nav_control.velocity_safety import safe_velocity, STOPPED, VelocityWatchdog


LIMITS = {"max_vx": 0.20, "max_vy": 0.0, "max_wz": 0.40}


def test_normal_velocity_is_unchanged():
    velocity = safe_velocity(0.03, 0.0, 0.05, **LIMITS)

    assert velocity is not None
    assert (velocity.vx, velocity.vy, velocity.wz) == (0.03, 0.0, 0.05)


def test_out_of_range_velocity_is_clamped():
    velocity = safe_velocity(1.0, 0.0, -1.0, **LIMITS)

    assert velocity is not None
    assert (velocity.vx, velocity.vy, velocity.wz) == (0.20, 0.0, -0.40)


def test_lateral_velocity_is_forced_to_zero():
    velocity = safe_velocity(0.0, 1.0, 0.0, **LIMITS)

    assert velocity is not None
    assert velocity.vy == 0.0


@pytest.mark.parametrize(
    "values",
    [
        (math.nan, 0.0, 0.0),
        (0.0, math.inf, 0.0),
        (0.0, 0.0, -math.inf),
    ],
)
def test_non_finite_velocity_is_rejected(values):
    assert safe_velocity(*values, **LIMITS) is None


def test_watchdog_stops_velocity_after_timeout():
    watchdog = VelocityWatchdog(timeout=0.3)
    velocity = safe_velocity(0.03, 0.0, 0.05, **LIMITS)
    assert velocity is not None
    watchdog.accept(velocity, now=10.0)

    assert watchdog.check(now=10.3) is False
    assert watchdog.desired == velocity
    assert watchdog.check(now=10.301) is True
    assert watchdog.desired == STOPPED
    assert watchdog.check(now=11.0) is False
