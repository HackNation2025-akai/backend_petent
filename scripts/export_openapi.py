"""
Generate OpenAPI spec to openapi.json.
Run from repo root: python scripts/export_openapi.py
"""
from __future__ import annotations

import json
from pathlib import Path

from app.main import app


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "openapi.json"
    schema = app.openapi()
    output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
    print(f"Zapisano {output_path}")


if __name__ == "__main__":
    main()


