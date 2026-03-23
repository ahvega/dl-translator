from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ExtractResult:
    """Markdown content plus optional asset paths (images) next to source."""

    markdown: str
    assets_dir: Path | None = None
    asset_paths: list[Path] = field(default_factory=list)
    used_ocr: bool = False
