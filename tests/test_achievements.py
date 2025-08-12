import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from gamecore import achievements


class FakeSteam:
    def __init__(self):
        self.achievements = set()
        self.stats_calls = 0
        self.cloud_saves = False

    def set_achievement(self, aid):
        self.achievements.add(aid)

    def is_achievement_unlocked(self, aid):
        return aid in self.achievements

    def store_stats(self):
        self.stats_calls += 1


def setup_function(_):
    achievements.init(FakeSteam())


def test_campaign_win_unlocks():
    achievements.on_campaign_win()
    steam = achievements._steam  # type: ignore
    assert achievements.ACH_WIN_CAMPAIGN in steam.achievements
    assert steam.stats_calls == 1


def test_kill_counter():
    for _ in range(100):
        achievements.on_zombie_kill()
    steam = achievements._steam  # type: ignore
    assert achievements.ACH_KILL_100 in steam.achievements


def test_four_players_on_start():
    achievements.on_game_start(4)
    steam = achievements._steam  # type: ignore
    assert achievements.ACH_FOUR_PLAYERS in steam.achievements


def test_no_damage_win():
    achievements.on_campaign_win()
    steam = achievements._steam  # type: ignore
    assert achievements.ACH_WIN_NO_DAMAGE in steam.achievements

    achievements.init(FakeSteam())
    achievements.on_player_damage()
    achievements.on_campaign_win()
    steam = achievements._steam  # type: ignore
    assert achievements.ACH_WIN_NO_DAMAGE not in steam.achievements
