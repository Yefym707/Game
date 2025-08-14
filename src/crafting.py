import json
from typing import Dict, List

class Recipe:
    def __init__(self, name: str, ingredients: Dict[str, int], result: str, result_qty: int = 1):
        self.name = name
        self.ingredients = ingredients  # {item: qty}
        self.result = result
        self.result_qty = result_qty

    @staticmethod
    def from_dict(d):
        return Recipe(
            name=d["name"],
            ingredients=d["ingredients"],
            result=d["result"],
            result_qty=d.get("result_qty", 1)
        )

def load_recipes(filename: str = "src/recipes.json") -> List[Recipe]:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [Recipe.from_dict(r) for r in data]