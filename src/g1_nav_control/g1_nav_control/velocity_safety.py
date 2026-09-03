"""Pure safety logic for planar velocity commands."""

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class Velocity:
    """A planar velocity after validation and limiting."""

    vx: float
    vy: float
    wz: float


STOPPED = Velocity(0.0, 0.0, 0.0)


def safe_velocity(
    vx: float,
    vy: float,
    wz: float,
    *,
    max_vx: float,
    max_vy: float,
    max_wz: float,
) -> Optional[Velocity]:
    """Validate and clamp a Twist's relevant components.

    ``None`` means that at least one input was NaN or infinite.  Lateral
    motion is deliberately disabled in this first version, regardless of the
    input or configured ``max_vy`` value.
    """

    values = (float(vx), float(vy), float(wz))
    if not all(math.isfinite(value) for value in values):
        return None

    limits = (float(max_vx), float(max_vy), float(max_wz))
    if not all(math.isfinite(limit) and limit >= 0.0 for limit in limits):
        raise ValueError("velocity limits must be finite and non-negative")

    return Velocity(
        vx=max(-limits[0], min(values[0], limits[0])),
        vy=0.0,
        wz=max(-limits[2], min(values[2], limits[2])),
    )


class VelocityWatchdog:
    """Track a desired velocity and stop it after a local-clock timeout."""

    def __init__(self, timeout: float) -> None:
        if not math.isfinite(timeout) or timeout <= 0.0:
            raise ValueError("watchdog timeout must be finite and positive")
        self.timeout = float(timeout)
        self.desired = STOPPED
        self._last_command_time: Optional[float] = None
        self._timed_out = False

    def accept(self, velocity: Velocity, now: float) -> None:
        """Store a validated command and its node-local receipt time."""

        self.desired = velocity
        self._last_command_time = float(now)
        self._timed_out = False

    def check(self, now: float) -> bool:
        """Stop an expired command; return True only on the timeout edge."""

        if self._last_command_time is None or self._timed_out:
            return False
        elapsed = float(now) - self._last_command_time
        if elapsed <= self.timeout or math.isclose(
            elapsed, self.timeout, rel_tol=1e-12, abs_tol=1e-12
        ):
            return False

        self.desired = STOPPED
        self._timed_out = True
        return True
