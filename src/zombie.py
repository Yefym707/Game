from entity import Entity


class Zombie(Entity):
    """Basic zombie that only tracks position and health."""

    def __init__(self, x: int = 0, y: int = 0, health: int = 3):
        super().__init__(x, y, health)
