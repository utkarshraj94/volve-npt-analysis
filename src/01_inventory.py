import os
import csv
import mimetypes
from datetime import datetime

RAW_ROOT = os.path.join("data", "raw")
OUTPUT_CSV = os.path.join("docs", "file_inventory.csv")


def guess_content_type(filename):
    ctype, _ = mimetypes.guess_type(filename)
    return ctype or "unknown"


def build_inventory():
    rows = []
    for dirpath, _, filenames in os.walk(RAW_ROOT):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            stat = os.stat(full_path)
            rows.append({
                "path": os.path.relpath(full_path, RAW_ROOT),
                "filename": filename,
                "extension": os.path.splitext(filename)[1].lower(),
                "size_bytes": stat.st_size,
                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "guessed_content_type": guess_content_type(filename),
            })
    return rows


if __name__ == "__main__":
    rows = build_inventory()
    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "path", "filename", "extension", "size_bytes",
            "modified_date", "guessed_content_type",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")