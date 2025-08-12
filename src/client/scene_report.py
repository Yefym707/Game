"""Minimal stub UI for submitting player reports."""
from __future__ import annotations

from typing import Dict


class SceneReport:
    def __init__(self, client) -> None:
        self.client = client

    async def submit(self, player: str, reason: str, comment: str) -> Dict[str, str]:
        report = {"player": player, "reason": reason, "comment": comment}
        await self.client.send({"t": "REPORT", "p": report})
        return report
