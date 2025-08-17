from typing import Protocol, List

class TempFilePort(Protocol):
    def cleanup(self, paths: List[str]) -> None:
        ...
