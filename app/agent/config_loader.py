from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings


class FieldConfig:
    def __init__(
        self,
        name: str,
        description: str,
        prompt: str,
        allowed_status: list[str],
        allowed_terms: list[str],
        example_context: str | None = None,
    ):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.allowed_status = allowed_status
        self.allowed_terms = allowed_terms
        self.example_context = example_context


class ConfigLoader:
    def __init__(self, path: Path):
        self.path = path
        self.system_prompt: str = ""
        self.fields: dict[str, FieldConfig] = {}
        self.field_mapping: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.system_prompt = data.get("system_prompt", "")
        self.field_mapping = data.get("field_mapping", {})
        for item in data.get("fields", []):
            cfg = FieldConfig(
                name=item["name"],
                description=item.get("description", ""),
                prompt=item.get("prompt", ""),
                allowed_status=item.get("allowed_status", ["success", "objection"]),
                allowed_terms=item.get("allowed_terms", []),
                example_context=item.get("example_context"),
            )
            self.fields[cfg.name] = cfg

    def get_field(self, field_type: str) -> FieldConfig | None:
        return self.fields.get(field_type)

    def build_messages(self, field_type: str, value: str, context: str | None = None) -> list[Any]:
        field = self.get_field(field_type)
        if not field:
            return []
        payload = {
            "field_type": field_type,
            "value": value,
            "context": context or "",
            "rules": field.prompt,
            "allowed_status": field.allowed_status,
            "allowed_terms": field.allowed_terms,
        }
        return [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=json.dumps(payload)),
        ]


# Singleton loader
CONFIG_PATH = Path(settings.base_dir) / "config" / "fields.json"
config_loader = ConfigLoader(CONFIG_PATH)


