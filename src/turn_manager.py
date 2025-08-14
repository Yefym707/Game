class TurnManager:
    """
    Управление фазами хода и очками действий (AP) — делает игру ближе к настольной.
    Фазы: Event -> Action -> Enemy -> Cleanup
    """
    PHASES = ["event", "action", "enemy", "cleanup"]

    def __init__(self, ap_per_turn: int = 3):
        self.current_phase_index = 0
        self.ap_per_turn = ap_per_turn
        self.remaining_ap = ap_per_turn
        self.turn_number = 0

    @property
    def current_phase(self) -> str:
        return self.PHASES[self.current_phase_index]

    def start_turn(self):
        self.turn_number += 1
        self.current_phase_index = 0
        self.remaining_ap = self.ap_per_turn
        return self.current_phase

    def next_phase(self):
        if self.current_phase_index < len(self.PHASES) - 1:
            self.current_phase_index += 1
        else:
            self.start_turn()
        return self.current_phase

    def use_ap(self, amount: int = 1) -> bool:
        if self.remaining_ap >= amount:
            self.remaining_ap -= amount
            return True
        return False

    def has_ap(self) -> bool:
        return self.remaining_ap > 0

    def set_ap(self, value: int):
        self.remaining_ap = value

    def __str__(self):
        return f"Turn {self.turn_number} | Phase: {self.current_phase} | AP: {self.remaining_ap}/{self.ap_per_turn}"