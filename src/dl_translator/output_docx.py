from __future__ import annotations

from pathlib import Path


def markdown_to_docx(
    md_text: str,
    output_path: Path,
    resource_parent: Path | None = None,
    author: str | None = None,
) -> None:
    """Write DOCX from Markdown using Pandoc (pypandoc)."""
    import pypandoc

    extra_args: list[str] = []
    if resource_parent is not None and resource_parent.is_dir():
        extra_args.append(f"--resource-path={resource_parent}")
    if author:
        extra_args.extend(["--metadata", f"author={author}"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        pypandoc.convert_text(
            md_text,
            "docx",
            format="md",
            outputfile=str(output_path),
            extra_args=extra_args,
        )
    except (OSError, RuntimeError) as e:
        raise RuntimeError(
            "DOCX export requires Pandoc installed and on PATH. "
            "See https://pandoc.org/installing.html (Windows: winget install pandoc)."
        ) from e
