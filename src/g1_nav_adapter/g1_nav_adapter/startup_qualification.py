"""Pure state machine controlling when valid odometry may first publish TF."""

from dataclasses import dataclass


DEFAULT_STARTUP_VALID_SAMPLES = 5


@dataclass
class QualificationStatistics:
    received_count: int = 0
    valid_count: int = 0
    rejected_count: int = 0
    startup_valid_streak: int = 0
    qualified: bool = False


class StartupQualification:
    def __init__(self, required_valid_samples=DEFAULT_STARTUP_VALID_SAMPLES):
        if not isinstance(required_valid_samples, int) or required_valid_samples < 1:
            raise ValueError("required_valid_samples must be an integer >= 1")
        self.required_valid_samples = required_valid_samples
        self.statistics = QualificationStatistics()

    def observe(self, valid):
        """Return ``(publish_allowed, just_qualified)`` for this sample."""
        stats = self.statistics
        stats.received_count += 1
        if not valid:
            stats.rejected_count += 1
            if not stats.qualified:
                stats.startup_valid_streak = 0
            return False, False

        stats.valid_count += 1
        if stats.qualified:
            return True, False

        stats.startup_valid_streak += 1
        if stats.startup_valid_streak >= self.required_valid_samples:
            stats.qualified = True
            return True, True
        return False, False
