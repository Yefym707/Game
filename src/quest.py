# ... previous Quest class code

    def check_complete(self, campaign):
        # ... previous conditions
        if "kill_enemy" in self.condition:
            killed = campaign.progress.get("enemies_killed", 0)
            return killed >= self.condition["kill_enemy"]["count"]
        # ...