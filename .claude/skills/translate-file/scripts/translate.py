#!/usr/bin/env python3
"""Wrapper script for dl-translate CLI.

This script provides a standalone entry point for the translate-file
Claude Code skill. It handles venv activation, prerequisite checks,
and delegates to the dl-translate CLI.

Usage:
    python translate.py [dl-translate arguments...]

Examples:
    python translate.py --format md report.pdf
    python translate.py --format docx --target-lang ES docs/
    python translate.py --extract-only scan.pdf
    python translate.py --dry-run --format md "incoming/*.pdf"
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_venv() -> Path | None:
    """Locate the dl-translator venv by checking common locations."""
    candidates = [
        Path(__file__).resolve().parents[3] / ".venv",  # repo root
        Path("E:/MyDevTools/dl-translator/.venv"),
        Path.cwd() / ".venv",
    ]
    for venv in candidates:
        python = venv / "Scripts" / "python.exe"
        if not python.exists():
            python = venv / "bin" / "python"
        if python.exists():
            return venv
    return None


def check_installed(python: str) -> bool:
    """Check if dl_translator is importable."""
    result = subprocess.run(
        [python, "-c", "import dl_translator"],
        capture_output=True,
    )
    return result.returncode == 0


def check_api_key(python: str) -> bool:
    """Check if DEEPL_AUTH_KEY is configured."""
    result = subprocess.run(
        [
            python,
            "-c",
            (
                "from dotenv import load_dotenv; load_dotenv(); "
                "import os; "
                "key = os.environ.get('DEEPL_AUTH_KEY', ''); "
                "exit(0 if key.strip() else 1)"
            ),
        ],
        capture_output=True,
    )
    return result.returncode == 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python translate.py [dl-translate args...]")
        print("Example: python translate.py --format md report.pdf")
        return 1

    venv = find_venv()
    if venv is None:
        print("ERROR: Could not find dl-translator virtual environment.")
        print("Install dl-translator first:")
        print("  cd E:/MyDevTools/dl-translator")
        print('  python -m venv .venv && pip install -e ".[dev]"')
        return 1

    python = str(venv / "Scripts" / "python.exe")
    if not Path(python).exists():
        python = str(venv / "bin" / "python")

    if not check_installed(python):
        print("ERROR: dl-translator is not installed in the venv.")
        print(f"  Venv: {venv}")
        print('  Fix: pip install -e ".[dev]"')
        return 1

    if not check_api_key(python):
        print("WARNING: DEEPL_AUTH_KEY may not be set.")
        print("  Set it in .env or as an environment variable.")

    cmd = [python, "-m", "dl_translator.cli"] + args
    result = subprocess.run(cmd, env={**os.environ})
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
