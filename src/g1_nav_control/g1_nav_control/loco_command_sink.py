"""Guarded Unitree LocoClient integration for velocity commands."""

from typing import Callable, Optional

from .velocity_safety import Velocity


# The pinned G1 LocoClient defines 500 as the locomotion-ready FSM.
LOCOMOTION_FSM_ID = 500


class UnitreeLocoBackend:
    """Thin SDK adapter whose imports and initialization are deliberately lazy."""

    def __init__(self) -> None:
        self._client = None

    def connect(self, network_interface: str) -> None:
        if not network_interface:
            raise ValueError("network_interface must not be empty")

        # Keeping these imports inside connect is a safety property: creating a
        # dry-run command sink never imports or initializes the Unitree SDK.
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize
        from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

        ChannelFactoryInitialize(0, network_interface)
        client = LocoClient()
        client.Init()
        self._client = client

    def _connected_client(self):
        if self._client is None:
            raise RuntimeError("Unitree LocoClient is not initialized")
        return self._client

    def get_fsm_id(self) -> int:
        code, fsm_id = self._connected_client().GetFsmId()
        if code != 0 or fsm_id is None:
            raise RuntimeError(f"GetFsmId failed: code={code} fsm_id={fsm_id}")
        return int(fsm_id)

    def set_velocity(self, velocity: Velocity, duration: float) -> None:
        code = self._connected_client().SetVelocity(
            velocity.vx, velocity.vy, velocity.wz, duration
        )
        if code != 0:
            raise RuntimeError(f"SetVelocity failed: code={code}")


class LocoCommandSink:
    """Apply the dry-run, motion-enable, and FSM gates in one place."""

    def __init__(
        self,
        *,
        dry_run: bool,
        enable_motion: bool,
        network_interface: str,
        command_duration: float,
        backend_factory: Callable[[], UnitreeLocoBackend] = UnitreeLocoBackend,
    ) -> None:
        self.dry_run = bool(dry_run)
        self.enable_motion = bool(enable_motion)
        self.command_duration = float(command_duration)
        self.current_fsm_id: Optional[int] = None
        self._backend = None

        if self.dry_run:
            return

        self._backend = backend_factory()
        self._backend.connect(network_interface)
        # Startup in non-dry-run mode is read-only until a velocity command
        # passes both the explicit enable flag and a fresh FSM check.
        self.current_fsm_id = self._backend.get_fsm_id()

    def apply(self, velocity: Velocity) -> str:
        """Apply a safe velocity if every gate passes; return the gate result."""

        if self.dry_run:
            return "dry_run"
        if not self.enable_motion:
            return "motion_disabled"

        # Re-read FSM for every potential write so a startup observation cannot
        # become a stale authorization after an external FSM transition.
        self.current_fsm_id = self._backend.get_fsm_id()
        if self.current_fsm_id != LOCOMOTION_FSM_ID:
            return "fsm_rejected"

        self._backend.set_velocity(velocity, self.command_duration)
        return "sent"
