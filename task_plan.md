# Task Plan: Create `translate-file` Claude Code Skill

## Goal
Create a Claude Code skill called `translate-file` based on the dl-translator CLI tool.

## Phases

### Phase 1: Research Claude Code Skills [complete]
- [x] Understand skill structure, required files, and conventions
- [x] Review skill-creator skill for best practices
- [x] Check existing example skills for patterns
- [x] Understand global vs workspace skill installation

### Phase 2: Design Skill Architecture [complete]
- [x] Decide: same repo vs separate repo -> SAME REPO
- [x] Design folder structure
- [x] Define skill trigger conditions
- [x] Plan what the skill prompt should contain

### Phase 3: Implement the Skill [complete]
- [x] Create folder structure at .claude/skills/translate-file/
- [x] Write SKILL.md with frontmatter and instructions
- [x] Create wrapper script scripts/translate.py
- [x] Create references/supported-formats.md
- [x] Create README.md with installation instructions

### Phase 4: Integration & Documentation [complete]
- [x] Verify skill structure (4 files, correct hierarchy)
- [x] Update CLAUDE.md with skill reference
- [x] Write installation instructions (workspace, global, separate repo)
- [x] Save memory

## Decisions Log
| Decision | Rationale | Date |
|----------|-----------|------|
| Same repo | Skill is tightly coupled to CLI; simpler maintenance | 2026-03-23 |
| Workspace + copy-for-global | .claude/skills/ in repo = auto; copy to ~/.claude/skills/ for global | 2026-03-23 |
| Wrapper script pattern | Follow optimize-image pattern: Python script that invokes dl-translate | 2026-03-23 |
