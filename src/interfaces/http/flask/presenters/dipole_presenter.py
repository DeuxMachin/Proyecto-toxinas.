from typing import Dict, Any


class DipolePresenter:
    @staticmethod
    def present(result: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "meta": meta,
            "result": result,
        }
