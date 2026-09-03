"""Tests for the SDK initialization and motion gates."""

from g1_nav_control.loco_command_sink import LocoCommandSink
from g1_nav_control.velocity_safety import Velocity


class FakeBackend:
    def __init__(self, fsm_id=500):
        self.fsm_id = fsm_id
        self.connected_interfaces = []
        self.set_velocity_calls = []

    def connect(self, network_interface):
        self.connected_interfaces.append(network_interface)

    def get_fsm_id(self):
        return self.fsm_id

    def set_velocity(self, velocity, duration):
        self.set_velocity_calls.append((velocity, duration))


def test_dry_run_never_constructs_or_initializes_sdk_backend():
    def forbidden_backend_factory():
        raise AssertionError("SDK backend must not be constructed in dry-run")

    sink = LocoCommandSink(
        dry_run=True,
        enable_motion=True,
        network_interface="enp6s0",
        command_duration=0.3,
        backend_factory=forbidden_backend_factory,
    )

    assert sink.apply(Velocity(0.1, 0.0, 0.2)) == "dry_run"
    assert sink.current_fsm_id is None


def test_motion_disabled_reads_fsm_but_never_sets_velocity():
    backend = FakeBackend(fsm_id=500)
    sink = LocoCommandSink(
        dry_run=False,
        enable_motion=False,
        network_interface="enp6s0",
        command_duration=0.3,
        backend_factory=lambda: backend,
    )

    result = sink.apply(Velocity(0.1, 0.0, 0.2))

    assert backend.connected_interfaces == ["enp6s0"]
    assert sink.current_fsm_id == 500
    assert result == "motion_disabled"
    assert backend.set_velocity_calls == []
