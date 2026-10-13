"""Load persona definitions from YAML files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml

DEFAULT_PERSONAS_DIR = Path(__file__).resolve().parent / "personas"


@dataclass(frozen=True)
class PersonaDefinition:
    id: str
    label: str
    system_prompt: str
    schema_name: str
    max_bullets: int = 5


def _coerce_persona(raw: Dict[str, Any], path: Path) -> PersonaDefinition:
    missing = [k for k in ("id", "label", "system_prompt", "schema") if k not in raw]
    if missing:
        raise ValueError(f"{path}: missing required keys: {', '.join(missing)}")
    return PersonaDefinition(
        id=str(raw["id"]),
        label=str(raw["label"]),
        system_prompt=str(raw["system_prompt"]).strip(),
        schema_name=str(raw["schema"]),
        max_bullets=int(raw.get("max_bullets", 5)),
    )


def load_personas(directory: Path | None = None) -> Dict[str, PersonaDefinition]:
    """Load all ``*.yaml`` persona files from ``personas/`` (or ``directory``)."""
    root = directory or DEFAULT_PERSONAS_DIR
    if not root.is_dir():
        raise FileNotFoundError(f"Personas directory not found: {root}")

    personas: Dict[str, PersonaDefinition] = {}
    for path in sorted(root.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a YAML mapping at top level")
        persona = _coerce_persona(data, path)
        personas[persona.id] = persona
    if not personas:
        raise ValueError(f"No persona YAML files in {root}")
    return personas


def list_persona_ids(directory: Path | None = None) -> List[str]:
    return sorted(load_personas(directory).keys())
