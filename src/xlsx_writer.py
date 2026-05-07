from pathlib import Path

from openpyxl import Workbook


def dict_to_xlsx(data: dict, path: Path):
    wb = Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in data.items():
        ws = wb.create_sheet(title=str(sheet_name)[:31] or "Sheet1")
        if not rows:
            continue
        headers = []
        seen = set()
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.add(k)
                    headers.append(k)
        ws.append(headers)
        for r in rows:
            ws.append([r.get(k) for k in headers])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
