from typing import Dict, Tuple, Optional, Any

class Trader:
    """
    Торговец с поддержкой репутации и редких товаров.
    goods может быть в двух форматах:
      - старый: { "еда": (sell_price, buy_price), ... }
      - новый:  { "еда": {"sell":5,"buy":2, "min_rep": 0}, "редкий": {"sell":50,"buy":20,"min_rep":3} }
    Репутация влияет на цены и доступность товаров.
    """
    def __init__(self, name: str, goods: Dict[str, Any]):
        self.name = name
        self.goods = {}
        # нормализуем входные товары в формат item -> {"sell":..., "buy":..., "min_rep":...}
        for item, data in goods.items():
            if isinstance(data, tuple) or isinstance(data, list):
                sell, buy = data[0], data[1] if len(data) > 1 else 0
                self.goods[item] = {"sell": int(sell), "buy": int(buy), "min_rep": 0}
            elif isinstance(data, dict):
                self.goods[item] = {
                    "sell": int(data.get("sell", 1)),
                    "buy": int(data.get("buy", 0)),
                    "min_rep": int(data.get("min_rep", 0))
                }
            else:
                # fallback
                self.goods[item] = {"sell": 1, "buy": 0, "min_rep": 0}

    def _price_multiplier(self, campaign) -> float:
        try:
            rep = campaign.progress.get("reputation", {}).get(self.name, 0)
        except Exception:
            rep = 0
        if rep >= 5:
            return 0.80
        if rep >= 2:
            return 0.92
        if rep <= -5:
            return 1.30
        if rep <= -2:
            return 1.12
        return 1.0

    def list_goods(self, campaign=None) -> str:
        lines = [f"Торговец {self.name} — товары:"]
        mult = self._price_multiplier(campaign) if campaign is not None else 1.0
        rep = 0
        if campaign:
            rep = campaign.progress.get("reputation", {}).get(self.name, 0)
        for item, meta in self.goods.items():
            min_rep = meta.get("min_rep", 0)
            if rep < min_rep:
                lines.append(f" - {item}: (закрыт, нужно репутации {min_rep})")
                continue
            sell_price = max(1, int(meta["sell"] * mult))
            # buy_price — что торговец даст игроку за предмет (зависит от мультипликатора обратным образом)
            buy_price = max(0, int(meta["buy"] * (2 - mult)))
            lines.append(f" - {item}: купить за {sell_price} монет | продать за {buy_price} монет (min_rep={min_rep})")
        return "\n".join(lines)

    def sell_to_player(self, item: str, inventory, qty: int = 1, campaign=None) -> str:
        if item not in self.goods:
            return "У торговца нет такого товара."
        meta = self.goods[item]
        rep = 0
        if campaign:
            rep = campaign.progress.get("reputation", {}).get(self.name, 0)
        min_rep = meta.get("min_rep", 0)
        if rep < min_rep:
            return f"Торговец не доверяет вам достаточно (нужна репутация {min_rep})."
        mult = self._price_multiplier(campaign) if campaign is not None else 1.0
        total = max(1, int(meta["sell"] * mult)) * qty
        if not inventory.spend_coins(total):
            return "У вас недостаточно монет."
        inventory.add_item(item, qty)
        if campaign:
            rep_map = campaign.progress.setdefault("reputation", {})
            rep_map[self.name] = rep_map.get(self.name, 0) + 1
        return f"Вы купили {qty} x {item} за {total} монет."

    def buy_from_player(self, item: str, inventory, qty: int = 1, campaign=None) -> str:
        if item not in self.goods:
            return "Торговец не заинтересован в этом предмете."
        meta = self.goods[item]
        mult = self._price_multiplier(campaign) if campaign is not None else 1.0
        total = max(0, int(meta["buy"] * (2 - mult))) * qty
        if not inventory.has_item(item, qty):
            return "У вас нет такого количества предмета."
        inventory.remove_item(item, qty)
        inventory.add_coins(total)
        if campaign:
            rep_map = campaign.progress.setdefault("reputation", {})
            rep_map[self.name] = rep_map.get(self.name, 0) - 1
        return f"Вы продали {qty} x {item} за {total} монет."

    def to_dict(self):
        return {"name": self.name, "goods": self.goods}

    @staticmethod
    def from_dict(d):
        return Trader(d["name"], d["goods"])