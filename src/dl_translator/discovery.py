from __future__ import annotations

import glob
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".md",
    ".markdown",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
}


def has_glob_pattern(path: str) -> bool:
    return "*" in path or "?" in path or "[" in path


def discover_files(paths: list[str], recursive: bool) -> list[Path]:
    """Return sorted unique files under supported extensions."""
    found: list[Path] = []
    for raw in paths:
        raw = raw.strip()
        if not raw:
            continue
        if has_glob_pattern(raw):
            matches = glob.glob(raw, recursive=True)
            for m in matches:
                p = Path(m)
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    found.append(p)
            continue
        p = Path(raw)
        if p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                found.append(p)
            continue
        if p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            for f in it:
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                    found.append(f)
    return sorted(set(found))
