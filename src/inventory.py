from dataclasses import dataclass, field
from typing import Dict, Any

from crafting import Recipe


@dataclass
class Inventory:
    """Simple container tracking a player's items and coins."""

    items: Dict[str, int] = field(default_factory=dict)
    coins: int = 0

    def add_item(self, item_name: str, quantity: int = 1) -> None:
        """Add ``quantity`` of ``item_name`` to the inventory."""

        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.items[item_name] = self.items.get(item_name, 0) + quantity

    def remove_item(self, item_name: str, quantity: int = 1) -> None:
        """Remove ``quantity`` of ``item_name`` from the inventory."""

        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.items.get(item_name, 0) < quantity:
            raise ValueError("not enough items to remove")

        new_qty = self.items[item_name] - quantity
        if new_qty:
            self.items[item_name] = new_qty
        else:
            del self.items[item_name]

    def has_item(self, item_name: str, quantity: int = 1) -> bool:
        """Return ``True`` if ``quantity`` of ``item_name`` is available."""

        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return self.items.get(item_name, 0) >= quantity

    def add_coins(self, amount: int) -> None:
        """Increase the amount of coins held."""

        self.coins += amount

    def spend_coins(self, amount: int) -> bool:
        """Attempt to spend ``amount`` coins and return ``True`` on success."""

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
        """Use an item from the inventory and apply its effect to ``campaign``."""

        if not self.has_item(item_name):
            return "Нет такого предмета в инвентаре."

        if item_name == "аптечка":
            if campaign.player.health < campaign.player.max_health:
                campaign.player.heal(3)
                self.remove_item(item_name, 1)
                return "Вы использовали аптечку и восстановили 3 здоровья."
            return "У вас и так максимум здоровья."

        if item_name == "еда":
            before = len(campaign.status_effects)
            campaign.status_effects = [
                e for e in campaign.status_effects if e.effect_type != "hunger"
            ]
            self.remove_item(item_name, 1)
            if len(campaign.status_effects) < before:
                return "Вы поели и утолили голод."
            return "Вы перекусили, но особых изменений не почувствовали."

        if item_name == "вода":
            campaign.status_effects = [
                e for e in campaign.status_effects if e.effect_type != "thirst"
            ]
            self.remove_item(item_name, 1)
            return "Вы утолили жажду."

        if item_name == "противоядие":
            removed = False
            for e in list(campaign.status_effects):
                if e.effect_type == "poison":
                    campaign.status_effects.remove(e)
                    removed = True
            if removed:
                self.remove_item(item_name, 1)
                return "Вы приняли противоядие и избавились от яда."
            return "Противоядие не требуется."

        return "Этот предмет нельзя использовать напрямую."

    def to_dict(self) -> Dict[str, Any]:
        return {"items": dict(self.items), "coins": self.coins}

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return Inventory(items=dict(data.get("items", {})), coins=int(data.get("coins", 0)))

    def __str__(self) -> str:
        if not self.items and self.coins == 0:
            return "Инвентарь пуст. Монет: 0"
        parts = []
        if self.items:
            parts += [f"{item}: {qty}" for item, qty in self.items.items()]
        parts.append(f"Монет: {self.coins}")
        return "\n".join(parts)

