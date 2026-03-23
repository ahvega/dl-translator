from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm
from rich.prompt import Prompt

from dl_translator.discovery import discover_files, has_glob_pattern
from dl_translator.extractors.common import ExtractResult
from dl_translator.extractors.docx import extract_docx
from dl_translator.extractors.image import extract_image
from dl_translator.extractors.md import extract_markdown_file
from dl_translator.extractors.pdf import extract_pdf
from dl_translator.md_translate import translate_full_markdown
from dl_translator.ocr_cleanup import clean_ocr_markdown
from dl_translator.output_docx import markdown_to_docx
from dl_translator.translate import (
    detect_source_lang,
    get_translator,
    normalize_target_for_deepl,
    translate_text_chunks,
)

console = Console(stderr=True)


def _configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


def _suffix_for_target(lang: str) -> str:
    u = lang.upper()
    if u.startswith("EN"):
        return "en"
    if u.startswith("ES"):
        return "es"
    return "en"


def _target_from_detected_source(source_lang: str) -> str:
    u = source_lang.upper()
    if u.startswith("ES"):
        return "EN-US"
    return "ES"


def _extract_to_markdown(path: Path, force_ocr: bool, gpu: bool) -> ExtractResult:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_pdf(path, force_ocr=force_ocr, gpu=gpu)
    if ext == ".docx":
        return extract_docx(path)
    if ext in (".md", ".markdown"):
        return extract_markdown_file(path)
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"):
        return extract_image(path, gpu=gpu)
    raise typer.BadParameter(f"Unsupported file type: {path}")


def _resolve_output_format(fmt: Optional[str]) -> str:
    if fmt is not None:
        f = fmt.strip().lower()
        if f not in ("md", "docx"):
            raise typer.BadParameter(f"Format must be md or docx, got {fmt!r}")
        return f
    if sys.stdin.isatty():
        return Prompt.ask(
            "Output format",
            choices=["md", "docx"],
            default="md",
        )
    return "md"


def _convert_markdown_outputs_to_docx(
    translated_md_outputs: list[tuple[Path, Path]],
) -> int:
    docx_failures = 0
    for md_path, resource_parent in translated_md_outputs:
        docx_path = md_path.with_suffix(".docx")
        try:
            markdown_to_docx(
                md_path.read_text(encoding="utf-8"),
                docx_path,
                resource_parent=resource_parent,
            )
            console.print(f"[green]OK[/green] {md_path} -> {docx_path}")
        except Exception as e:
            docx_failures += 1
            console.print(f"[red]Error[/red] {md_path}: {e}")
    return docx_failures


def run(
    paths: list[str] = typer.Argument(
        ...,
        help="Files, directories, and/or glob patterns (e.g. *.pdf, docs/**/*.docx).",
    ),
    output_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help=(
            "Output: md or docx. If omitted in an"
            " interactive terminal, you will be prompted."
        ),
    ),
    no_recursive: bool = typer.Option(
        False,
        "--no-recursive",
        help="When a path is a directory, include only that folder (not subfolders).",
    ),
    target_lang: Optional[str] = typer.Option(
        None,
        "--target-lang",
        help="Force target language: EN or ES (English maps to EN-US for DeepL).",
    ),
    force_ocr: bool = typer.Option(
        False,
        "--force-ocr",
        help="Force OCR for every PDF page (skip text layer).",
    ),
    gpu: bool = typer.Option(
        False,
        "--gpu",
        help="Use GPU for EasyOCR if available.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="List files and show planned work without calling DeepL.",
    ),
    continue_on_error: bool = typer.Option(
        False,
        "--continue-on-error",
        help="Process remaining files if one fails.",
    ),
    extract_only: bool = typer.Option(
        False,
        "--extract-only",
        help=(
            "Convert to Markdown only (no translation)."
            " Writes *_extract.md next to source."
        ),
    ),
) -> None:
    """Translate documents between English and Spanish using the DeepL API."""
    _configure_stdio()
    load_dotenv()

    recursive = not no_recursive
    files = discover_files(paths, recursive=recursive)
    if not files:
        console.print("[red]No matching files found.[/red]")
        raise typer.Exit(code=1)

    if any(
        Path(p).expanduser().is_dir()
        for p in paths
        if p.strip() and not has_glob_pattern(p)
    ):
        console.print(
            "[yellow]Note:[/yellow] Recursive folder discovery"
            " is [bold]on[/bold] by default (subfolders"
            " included). Use [bold]--no-recursive[/bold]"
            " to limit to a single folder."
        )

    fmt = _resolve_output_format(output_format)

    if dry_run:
        console.print(f"[cyan]Dry run[/cyan] — {len(files)} file(s), format: {fmt}")
        for f in files:
            console.print(f"  {f}")
        raise typer.Exit(code=0)

    translator = None
    if not extract_only:
        translator = get_translator()

    failures = 0
    translated_md_outputs: list[tuple[Path, Path]] = []
    for path in files:
        try:
            md = _extract_to_markdown(path, force_ocr=force_ocr, gpu=gpu)
            if extract_only:
                out = path.parent / f"{path.stem}_extract.md"
                out.write_text(md.markdown, encoding="utf-8")
                console.print(f"[green]OK[/green] {path} -> {out}")
                continue

            assert translator is not None
            need_detection = not target_lang or md.used_ocr
            source = (
                detect_source_lang(translator, md.markdown) if need_detection else None
            )
            if target_lang:
                target = normalize_target_for_deepl(target_lang)
            else:
                target = _target_from_detected_source(source or "EN")
            source_markdown = md.markdown

            if md.used_ocr:
                source_suf = _suffix_for_target(source)
                source_md_path = path.parent / f"{path.stem}_{source_suf}.md"
                source_markdown = clean_ocr_markdown(source_markdown, source or "EN")
                source_md_path.write_text(source_markdown, encoding="utf-8")
                console.print(
                    f"[green]OK[/green] {path} -> {source_md_path} (OCR source)"
                )

            def chunk_fn(s: str) -> str:
                return translate_text_chunks(translator, s, target_lang=target)

            translated = translate_full_markdown(source_markdown, chunk_fn)
            if md.used_ocr:
                translated = clean_ocr_markdown(translated, target)
            suf = _suffix_for_target(target)
            base = path.parent / f"{path.stem}_{suf}"

            if fmt == "md":
                out_path = base.with_suffix(".md")
                out_path.write_text(translated, encoding="utf-8")
                console.print(f"[green]OK[/green] {path} -> {out_path}")
                translated_md_outputs.append((out_path, path.parent))
            else:
                docx_path = base.with_suffix(".docx")
                markdown_to_docx(translated, docx_path, resource_parent=path.parent)
                console.print(f"[green]OK[/green] {path} -> {docx_path}")

        except Exception as e:
            failures += 1
            console.print(f"[red]Error[/red] {path}: {e}")
            if not continue_on_error:
                raise typer.Exit(code=1)

    if failures:
        console.print(f"[yellow]Completed with {failures} error(s).[/yellow]")
        raise typer.Exit(code=1)

    if fmt == "md" and translated_md_outputs and sys.stdin.isatty():
        if Confirm.ask(
            "Create DOCX copy/copies from the translated Markdown output?", default=False
        ):
            docx_failures = _convert_markdown_outputs_to_docx(translated_md_outputs)
            if docx_failures:
                console.print(
                    f"[yellow]Completed with {docx_failures} DOCX conversion error(s).[/yellow]"
                )
                raise typer.Exit(code=1)


def main() -> None:
    typer.run(run)


if __name__ == "__main__":
    main()
