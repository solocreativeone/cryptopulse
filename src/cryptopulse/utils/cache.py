import json
from pathlib import Path
from typing import Any, Optional

class JSONCache:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file

    def save(self, data: Any):
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(data))
        except Exception:
            pass

    def load(self) -> Optional[Any]:
        if not self.cache_file.exists():
            return None
        try:
            return json.loads(self.cache_file.read_text())
        except (json.JSONDecodeError, Exception):
            return None
