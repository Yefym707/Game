class Player:
    def __init__(self, health: int = 5, max_health: int = 5):
        self.health = health
        self.max_health = max_health

    def heal(self, amount: int):
        self.health = min(self.max_health, self.health + amount)

    def damage(self, amount: int):
        self.health = max(0, self.health - amount)

    def is_alive(self) -> bool:
        return self.health > 0

    def to_dict(self):
        return {"health": self.health, "max_health": self.max_health}

    @staticmethod
    def from_dict(d):
        return Player(health=d.get("health", 5), max_health=d.get("max_health", 5))