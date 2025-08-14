import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from inventory import Inventory
from player import Player
from trader import Trader


def test_trader_buy_and_sell_cycle():
    # Trader initially sells apples and is willing to buy gems
    stock = {
        "apple": (5, 3),  # price 5 coins, 3 in stock
        "gem": (7, 0),    # willing to buy gems for 7 coins
    }
    trader = Trader("Bob", stock, coins=10)

    # Player starts with some money and a single gem
    player_inv = Inventory(items={"gem": 1}, coins=15)
    player = Player(inventory=player_inv)

    # Player buys two apples for 10 coins in total
    assert trader.buy("apple", 2, player)
    assert player.inventory.has_item("apple", 2)
    assert player.inventory.coins == 5
    assert trader.inventory.has_item("apple", 1)
    assert trader.inventory.coins == 20

    # Player sells the gem back to the trader for 7 coins
    assert trader.sell("gem", 1, player)
    assert not player.inventory.has_item("gem")
    assert player.inventory.coins == 12
    assert trader.inventory.has_item("gem", 1)
    assert trader.inventory.coins == 13

    # Trader no longer has enough apples to sell two more
    assert not trader.buy("apple", 5, player)

