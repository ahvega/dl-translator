# Findings: translate-file Skill Research

## Skill Structure
- Only `SKILL.md` is required (in a named folder)
- YAML frontmatter: name, description, allowed-tools, etc.
- Optional: scripts/, references/, templates/
- Personal skills: `~/.claude/skills/<skill-name>/SKILL.md`
- Project skills: `.claude/skills/<skill-name>/SKILL.md`

## Trigger Conditions
- `description` field in frontmatter drives auto-invocation
- Pattern: "Use when the user says /skill-name, asks to translate, convert..."
- `$ARGUMENTS` placeholder captures user input
- `disable-model-invocation: true` = manual only

## Installation Mechanics
- Skills auto-discovered by location - no registry needed
- Global: copy folder to `~/.claude/skills/`
- Workspace: copy folder to `.claude/skills/` in project root
- No build step, just file placement

## Key Design Decisions

### Same repo vs separate repo?
**Recommendation: Include in this repo as `.claude/skills/translate-file/`**

Rationale:
1. The skill is tightly coupled to the dl-translator CLI tool
2. Skill scripts need the dl-translator package installed
3. Users who clone the repo get both the CLI and the skill
4. For global install, users just copy the skill folder to `~/.claude/skills/`
5. Simpler maintenance - one repo, one set of changes
6. Existing skills like ftp-deploy and optimize-image follow this "self-contained folder" pattern

The skill will:
- Live at `.claude/skills/translate-file/` in the repo (workspace skill)
- Include instructions to copy to `~/.claude/skills/translate-file/` for global use
- Reference the dl-translate CLI (which must be pip-installed)

### What the skill should do
- Accept file paths/globs as arguments
- Support --format, --target-lang, --extract-only flags
- Run dl-translate CLI under the hood
- Provide clear output and error handling
- Work as long as the venv with dl-translator is accessible
