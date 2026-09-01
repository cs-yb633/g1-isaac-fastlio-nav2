"""One-shot, guarded G1 FSM inspection and switching tool."""

import argparse
from dataclasses import dataclass
import json
import os
import sys
import time


RISK_ACKNOWLEDGEMENT = "I_UNDERSTAND_G1_MAY_MOVE_OR_FALL"


@dataclass(frozen=True)
class FsmTarget:
    fsm_id: int
    warning: str


# IDs below come from the pinned official unitree_sdk2_python G1 LocoClient.
FSM_TARGETS = {
    "zero_torque": FsmTarget(0, "Torque may be removed and the robot may collapse."),
    "damp": FsmTarget(1, "The robot may lose posture and fall into damping mode."),
    "sit": FsmTarget(3, "The robot may execute a sitting transition."),
    "start": FsmTarget(500, "The robot may stand or enter locomotion-ready control."),
}


def _parser():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or make one explicitly confirmed G1 FSM transition. "
            "Modes default to dry-run and never send velocity commands."
        )
    )
    parser.add_argument("mode", choices=("status", *FSM_TARGETS))
    parser.add_argument(
        "--network-interface",
        default=os.environ.get("G1_NETWORK_INTERFACE", ""),
        help="G1 wired interface; defaults to G1_NETWORK_INTERFACE",
    )
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--verify-timeout-sec", type=float, default=5.0)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually call SetFsmId; omitted means offline dry-run",
    )
    parser.add_argument(
        "--expect-current-id",
        type=int,
        help="Required for execution; transition is refused if live FSM differs",
    )
    parser.add_argument(
        "--confirm-target-id",
        type=int,
        help="Required for execution and must equal the selected target ID",
    )
    parser.add_argument(
        "--acknowledge-risk",
        default="",
        help=f"Required for execution: {RISK_ACKNOWLEDGEMENT}",
    )
    return parser


def _load_sdk():
    try:
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize
        from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
    except ImportError as error:
        raise RuntimeError(
            "unitree_sdk2py is unavailable; rebuild the g1-nav Docker image"
        ) from error
    return ChannelFactoryInitialize, LocoClient


def _connect(network_interface, timeout_sec):
    if not network_interface:
        raise RuntimeError(
            "network interface is required via --network-interface or "
            "G1_NETWORK_INTERFACE"
        )
    channel_factory_initialize, client_type = _load_sdk()
    channel_factory_initialize(0, network_interface)
    client = client_type()
    client.SetTimeout(timeout_sec)
    client.Init()
    return client


def _get_fsm_id(client):
    code, fsm_id = client.GetFsmId()
    if code != 0 or fsm_id is None:
        raise RuntimeError(f"GetFsmId failed: code={code} fsm_id={fsm_id}")
    return int(fsm_id)


def _dry_run(mode, target, network_interface):
    print(
        json.dumps(
            {
                "dry_run": True,
                "mode": mode,
                "target_fsm_id": target.fsm_id,
                "network_interface": network_interface or None,
                "warning": target.warning,
                "dds_initialized": False,
                "request_sent": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


def main(args=None):
    parser = _parser()
    options = parser.parse_args(args)
    if options.timeout_sec <= 0.0 or options.verify_timeout_sec <= 0.0:
        parser.error("timeouts must be positive")

    if options.mode == "status":
        if options.execute:
            parser.error("status is read-only and does not accept --execute")
        try:
            current = _get_fsm_id(
                _connect(options.network_interface, options.timeout_sec)
            )
        except Exception as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        print(json.dumps({"fsm_id": current, "read_only": True}, indent=2))
        return 0

    target = FSM_TARGETS[options.mode]
    if not options.execute:
        _dry_run(options.mode, target, options.network_interface)
        return 0

    if options.expect_current_id is None:
        parser.error("--expect-current-id is required with --execute")
    if options.confirm_target_id != target.fsm_id:
        parser.error(
            f"--confirm-target-id must equal selected target {target.fsm_id}"
        )
    if options.acknowledge_risk != RISK_ACKNOWLEDGEMENT:
        parser.error(
            "--acknowledge-risk must exactly match " + RISK_ACKNOWLEDGEMENT
        )

    print(f"WARNING: {target.warning}", file=sys.stderr)
    try:
        client = _connect(options.network_interface, options.timeout_sec)
        current = _get_fsm_id(client)
        if current != options.expect_current_id:
            raise RuntimeError(
                f"current FSM {current} does not match expected "
                f"{options.expect_current_id}; no request sent"
            )
        if current == target.fsm_id:
            print(
                json.dumps(
                    {
                        "changed": False,
                        "fsm_id": current,
                        "reason": "already_at_target",
                    },
                    indent=2,
                )
            )
            return 0

        code = client.SetFsmId(target.fsm_id)
        if code != 0:
            raise RuntimeError(f"SetFsmId({target.fsm_id}) failed: code={code}")

        deadline = time.monotonic() + options.verify_timeout_sec
        observed = None
        while time.monotonic() < deadline:
            observed = _get_fsm_id(client)
            if observed == target.fsm_id:
                print(
                    json.dumps(
                        {
                            "changed": True,
                            "previous_fsm_id": current,
                            "fsm_id": observed,
                            "verified": True,
                        },
                        indent=2,
                    )
                )
                return 0
            time.sleep(0.2)
        raise RuntimeError(
            f"SetFsmId returned success but readback remained {observed}; "
            "no fallback transition was attempted"
        )
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
