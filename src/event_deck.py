    def apply(self, campaign):
        eff = self.effect
        # ... предыдущие
        if "status" in eff:
            from enemies import StatusEffect
            st = eff["status"]
            campaign.apply_status(StatusEffect(st["effect_type"], st["duration"]))
            print(f"Получен эффект: {st['effect_type'].upper()} на {st['duration']} ходов")