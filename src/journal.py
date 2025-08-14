import json
from datetime import datetime
from typing import List, Dict, Any

class Journal:
    """
    Простой журнал (лог) для записей действий в партии.
    Записи — словари: {time, turn, message}
    """
    def __init__(self, entries: List[Dict[str, Any]] = None):
        self.entries = entries or []

    def log(self, message: str, turn: int = None):
        entry = {
            "time": datetime.utcnow().isoformat() + "Z",
            "turn": turn,
            "message": message
        }
        self.entries.append(entry)
        print(f"[LOG] {entry['time']} | T{turn} | {message}")

    def last(self, n: int = 10):
        return self.entries[-n:]

    def to_dict(self):
        return {"entries": list(self.entries)}

    @staticmethod
    def from_dict(d):
        return Journal(entries=d.get("entries", []))

    def save(self, filename: str = "journal.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(filename: str = "journal.json") -> 'Journal':
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Journal.from_dict(data)
        except Exception:
            return Journal()