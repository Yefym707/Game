# ... предыдущий код класса Quest

    def check_complete(self, campaign):
        # ... предыдущие условия
        if "kill_enemy" in self.condition:
            killed = campaign.progress.get("enemies_killed", 0)
            return killed >= self.condition["kill_enemy"]["count"]
        # ...