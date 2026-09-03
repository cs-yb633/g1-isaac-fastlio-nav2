"""Unit tests for the guarded one-shot G1 FSM tool."""

import json

import pytest

from g1_nav_control import g1_fsm_tool


ACK = g1_fsm_tool.RISK_ACKNOWLEDGEMENT


def test_standup_is_fsm_4():
    assert g1_fsm_tool.FSM_TARGETS["standup"].fsm_id == 4


def test_standup_defaults_to_offline_dry_run(monkeypatch, capsys):
    def unexpected_connect(*_args, **_kwargs):
        pytest.fail("dry-run must not initialize DDS")

    monkeypatch.setattr(g1_fsm_tool, "_connect", unexpected_connect)

    assert g1_fsm_tool.main(["standup", "--network-interface", "enp6s0"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "standup"
    assert result["target_fsm_id"] == 4
    assert result["dry_run"] is True
    assert result["dds_initialized"] is False
    assert result["request_sent"] is False


def test_standup_requires_confirm_target_id_4():
    with pytest.raises(SystemExit) as error:
        g1_fsm_tool.main(
            [
                "standup",
                "--execute",
                "--expect-current-id",
                "3",
                "--confirm-target-id",
                "500",
                "--acknowledge-risk",
                ACK,
            ]
        )

    assert error.value.code == 2


def test_standup_sends_exactly_one_fsm_4_request(monkeypatch, capsys):
    class FakeClient:
        def __init__(self):
            self.readbacks = iter((3, 4))
            self.requests = []

        def GetFsmId(self):
            return 0, next(self.readbacks)

        def SetFsmId(self, fsm_id):
            self.requests.append(fsm_id)
            return 0

    client = FakeClient()
    monkeypatch.setattr(g1_fsm_tool, "_connect", lambda *_args: client)
    monkeypatch.setattr(g1_fsm_tool.time, "sleep", lambda _seconds: None)

    result = g1_fsm_tool.main(
        [
            "standup",
            "--network-interface",
            "enp6s0",
            "--execute",
            "--expect-current-id",
            "3",
            "--confirm-target-id",
            "4",
            "--acknowledge-risk",
            ACK,
        ]
    )

    assert result == 0
    assert client.requests == [4]
    assert 500 not in client.requests
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "changed": True,
        "previous_fsm_id": 3,
        "fsm_id": 4,
        "verified": True,
    }
