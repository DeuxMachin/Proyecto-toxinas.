from typing import Dict


class ExportPresenter:
    @staticmethod
    def present_excel_meta(meta: Dict, filename: str, size_bytes: int) -> Dict:
        return {
            "meta": meta,
            "file": {
                "filename": filename,
                "size_bytes": size_bytes,
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        }
