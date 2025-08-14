class Entity:
    """Base entity with position and health."""

    def __init__(self, x: int = 0, y: int = 0, health: int = 1) -> None:
        self.x = x
        self.y = y
        self.health = health

    # position helpers -------------------------------------------------
    def get_position(self) -> tuple[int, int]:
        """Return the ``(x, y)`` position of the entity."""
        return self.x, self.y

    def set_position(self, x: int, y: int) -> None:
        """Update the entity's position."""
        self.x = x
        self.y = y

    # health helpers ---------------------------------------------------
    def get_health(self) -> int:
        """Return current health."""
        return self.health

    def set_health(self, health: int) -> None:
        """Set health to ``health``."""
        self.health = health

    def is_alive(self) -> bool:
        """Return ``True`` if the entity has more than zero health."""
        return self.health > 0
