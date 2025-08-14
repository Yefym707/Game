import json
from typing import Dict, Any, Optional
from crafting import Recipe

class Inventory:
    def __init__(self, items: Dict[str, int] = None, coins: int = 0):
        self.items = items or {}
        self.coins = coins

    def add_item(self, item_name: str, quantity: int = 1):
        self.items[item_name] = self.items.get(item_name, 0) + quantity

    def remove_item(self, item_name: str, quantity: int = 1):
        if item_name in self.items:
            self.items[item_name] -= quantity
            if self.items[item_name] <= 0:
                del self.items[item_name]

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        return self.items.get(item_name, 0) >= quantity

    def add_coins(self, amount: int):
        self.coins += amount

    def spend_coins(self, amount: int) -> bool:
        if self.coins >= amount:
            self.coins -= amount
            return True
        return False

    def can_craft(self, recipe: Recipe) -> bool:
        return all(self.has_item(item, qty) for item, qty in recipe.ingredients.items())

    def craft(self, recipe: Recipe) -> bool:
        if not self.can_craft(recipe):
            return False
        for item, qty in recipe.ingredients.items():
            self.remove_item(item, qty)
        self.add_item(recipe.result, recipe.result_qty)
        return True

    def use_item(self, item_name: str, campaign) -> str:
        if not self.has_item(item_name):
            return "Нет такого предмета в инвентаре."

        # Примеры существующих эффектов
        if item_name == "аптечка":
            if campaign.player.health < campaign.player.max_health:
                campaign.player.heal(3)
                self.remove_item(item_name, 1)
                return "Вы использовали аптечку и восстановили 3 здоровья."
            else:
                return "У вас и так максимум здоровья."
        # ... другие use_item ветки как раньше ...

        return "Этот предмет нельзя использовать напрямую."

    def to_dict(self) -> Dict[str, Any]:
        return {"items": dict(self.items), "coins": self.coins}

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return Inventory(items=dict(data.get("items", {})), coins=int(data.get("coins", 0)))

    def __str__(self):
        if not self.items and self.coins == 0:
            return "Инвентарь пуст. Монет: 0"
        parts = []
        if self.items:
            parts += [f"{item}: {qty}" for item, qty in self.items.items()]
        parts.append(f"Монет: {self.coins}")
        return "\n".join(parts)