from entity import Entity


class Player(Entity):
    """Simple player with position and health."""

    def __init__(self, x: int = 0, y: int = 0, health: int = 5, max_health: int = 5):
        super().__init__(x, y, health)
        self.max_health = max_health

    def heal(self, amount: int) -> None:
        """Increase health by ``amount`` up to ``max_health``."""
        self.health = min(self.max_health, self.health + amount)

    def damage(self, amount: int) -> None:
        """Reduce health by ``amount`` without going below zero."""
        self.health = max(0, self.health - amount)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "max_health": self.max_health,
        }

    @staticmethod
    def from_dict(d: dict) -> "Player":
        return Player(
            x=d.get("x", 0),
            y=d.get("y", 0),
            health=d.get("health", 5),
            max_health=d.get("max_health", 5),
        )
