from __future__ import annotations

import time

from master.registry import LobbyInfo, MasterRegistry


def make_info(mode: str = "survival", region: str = "eu", build: str = "1.0") -> LobbyInfo:
    return LobbyInfo(
        host="127.0.0.1",
        port=1234,
        name="Srv",
        mode=mode,
        max_players=4,
        cur_players=0,
        region=region,
        build=build,
        protocol=1,
    )


def test_register_and_list() -> None:
    reg = MasterRegistry(timeout=1.0, time_func=time.time)
    sid = reg.register(make_info())
    entries = reg.list()
    assert entries[0]["server_id"] == sid
    assert entries[0]["name"] == "Srv"


def test_heartbeat_and_expire() -> None:
    fake_time = [0.0]

    def _now() -> float:
        return fake_time[0]

    reg = MasterRegistry(timeout=10.0, time_func=_now)
    sid = reg.register(make_info())
    fake_time[0] += 5
    reg.heartbeat(sid, 2)
    assert reg.list()[0]["cur_players"] == 2
    fake_time[0] += 11
    # listing should purge stale entry
    assert reg.list() == []


def test_list_filters() -> None:
    reg = MasterRegistry(timeout=100.0, time_func=time.time)
    reg.register(make_info(mode="m1", region="eu"))
    reg.register(make_info(mode="m2", region="us"))
    assert len(reg.list()) == 2
    assert len(reg.list(mode="m1")) == 1
    assert len(reg.list(region="us")) == 1
    assert len(reg.list(mode="m2", region="eu")) == 0
