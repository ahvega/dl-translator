# translate-file - Claude Code Skill

Translate documents (PDF, DOCX, Markdown, images) between English and Spanish using the DeepL API.

## Prerequisites

1. **Python 3.10+** with dl-translator installed:
   ```powershell
   cd E:\MyDevTools\dl-translator
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -e ".[dev]"
   ```

2. **DeepL API key** in `.env`:
   ```env
   DEEPL_AUTH_KEY=your_key_here:fx
   ```

3. **Pandoc** (optional, only for DOCX output):
   ```powershell
   winget install --id JohnMacFarlane.Pandoc
   ```

## Installation

### Option A: Workspace skill (this repo only)

If you cloned this repo, the skill is already available. Claude Code auto-discovers skills in `.claude/skills/` when you work in this project directory.

```
dl-translator/
  .claude/skills/translate-file/   <-- skill is here
  src/dl_translator/               <-- CLI source
```

Just open Claude Code in the repo root and use `/translate-file`.

### Option B: Global skill (all projects)

Copy the skill folder to your personal skills directory:

```powershell
# Windows
Copy-Item -Recurse ".claude\skills\translate-file" "$env:USERPROFILE\.claude\skills\translate-file"
```

```bash
# Linux/macOS
cp -r .claude/skills/translate-file ~/.claude/skills/translate-file
```

The skill is now available in all Claude Code sessions via `/translate-file`.

**Note:** The `dl-translate` CLI must still be installed and accessible. If you use it globally, make sure the venv path in `scripts/translate.py` points to your installation, or install dl-translator into your system Python.

### Option C: Separate repo

If you prefer to maintain the skill independently:

1. Create a new repo with just the skill folder contents:
   ```
   translate-file/
     SKILL.md
     README.md
     scripts/translate.py
     references/supported-formats.md
   ```
2. Copy to `~/.claude/skills/translate-file/`
3. Update the venv path in `scripts/translate.py` to match your dl-translator installation

This approach is recommended only if you want to share the skill separately from the tool, or version them independently.

## Usage

In Claude Code:

```
/translate-file report.pdf
/translate-file report.pdf --format docx --target-lang ES
/translate-file documents/*.docx --format md
/translate-file scan.pdf --force-ocr
/translate-file ./incoming/ --format md
/translate-file report.pdf --extract-only
```

Or just ask Claude naturally:
- "Translate this PDF to English"
- "Convert document.docx to Spanish markdown"
- "Extract the text from scan.pdf"

## Recommendation: Same Repo vs Separate Repo

**We recommend keeping the skill in this repo** for the following reasons:

| Factor | Same Repo | Separate Repo |
|--------|-----------|---------------|
| Maintenance | Single place to update | Must sync changes across repos |
| Versioning | Skill and CLI always match | Can drift out of sync |
| Installation | Clone once, get both | Must clone/install both |
| Discoverability | Workspace skill works automatically | Requires manual copy |
| Sharing | Share whole repo | Can share skill independently |

The only reason to separate would be if you want to distribute the skill to users who don't need the CLI source code, or if you want to publish the skill to a marketplace independently.
