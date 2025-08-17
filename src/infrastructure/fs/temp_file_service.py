from typing import List
import os

class TempFileService:
    def cleanup(self, paths: List[str]) -> None:
        for p in paths:
            if p:
                try:
                    if os.path.isdir(p):
                        # Only clean files; skip directories silently
                        continue
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    # Best-effort cleanup; ignore errors
                    pass
