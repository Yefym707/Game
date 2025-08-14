from src.achievement_tracker import (
    AchievementTracker,
    FIRST_BLOOD,
    ZOMBIE_SLAYER,
    SURVIVOR,
)


def test_first_blood_and_zombie_slayer():
    tracker = AchievementTracker()
    tracker.on_zombie_kill()
    assert tracker.is_unlocked(FIRST_BLOOD)
    assert not tracker.is_unlocked(ZOMBIE_SLAYER)

    for _ in range(49):
        tracker.on_zombie_kill()
    assert tracker.is_unlocked(ZOMBIE_SLAYER)


def test_survivor_unlocked_when_no_deaths():
    tracker = AchievementTracker()
    tracker.on_scenario_win()
    assert tracker.is_unlocked(SURVIVOR)


def test_survivor_not_unlocked_when_player_dies():
    tracker = AchievementTracker()
    tracker.on_player_death()
    tracker.on_scenario_win()
    assert not tracker.is_unlocked(SURVIVOR)
