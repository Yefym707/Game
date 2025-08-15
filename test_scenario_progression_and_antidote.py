from campaign import Campaign
from scenario import Scenario
from game_map import GameMap
from inventory import Inventory
from player import Player
from enemies import EnemyManager


def _dummy_campaign(scenarios):
    gm = GameMap(4, 4, player_pos=(0, 0))
    inv = Inventory()
    player = Player(health=5, max_health=5)
    enemies = EnemyManager([])
    return Campaign(scenarios, game_map=gm, inventory=inv, player=player, enemies=enemies)


def test_campaign_advances_after_survive_condition(capsys):
    sc1 = Scenario("S1", "first", win_condition={"survive_turns": 1})
    sc2 = Scenario("S2", "second", {})
    camp = _dummy_campaign([sc1, sc2])
    camp.start_next_scenario()
    camp.turn_count = 1
    camp.tick_time()
    out = capsys.readouterr().out
    assert "Scenario Complete" in out
    assert camp.progress["current_index"] == 1


def test_rescue_tracking_triggers_completion(capsys):
    sc = Scenario("Rescue", "", win_condition={"rescued": 1})
    camp = _dummy_campaign([sc, Scenario("Dummy", "", {})])
    camp.start_next_scenario()
    camp.rescue_survivor()
    camp.turn_count += 1
    camp.tick_time()
    out = capsys.readouterr().out
    assert "Scenario Complete" in out
    assert camp.progress["current_index"] == 1


def test_antidote_requires_return_to_start(capsys):
    sc = Scenario(
        "Finale",
        "",
        win_condition={"item": "antidote"},
        special_conditions={"item_placement": [(1, 0, "A")]},
    )
    camp = _dummy_campaign([sc])
    camp.start_next_scenario()
    # move to antidote
    camp.game_map.move_player(1, 0)
    camp.turn_count += 1
    camp.tick_time()
    assert camp.inventory.has_item("antidote")
    # not yet complete until back at start
    assert camp.progress["current_index"] == 0
    camp.game_map.move_player(-1, 0)
    camp.turn_count += 1
    camp.tick_time()
    out = capsys.readouterr().out
    assert "Scenario Complete" in out
    assert camp.progress["campaign_complete"]
