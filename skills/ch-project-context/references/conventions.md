# Context Management Conventions

## Frontmatter Format

Every document file uses YAML frontmatter for structured metadata. This is consumed by hooks (programmatic parsing), not by agents reading files directly.

### Required Fields

```yaml
---
title: Short descriptive title
description: One-line summary (what + why)
status: active | completed | superseded-by <ID> | draft
date: YYYY-MM-DD
---
```

### Optional Fields

```yaml
related: [D001, D012]           # Cross-references to other docs
related-plan: feature-xyz       # Link to exec-plan
severity: P0 | P1 | P2         # For known-issues
produces: [D012]                # For research docs that led to decisions
```

## File Naming

- **Decisions**: `D001-short-description.md` (sequential numbering)
- **Known Issues**: `I001-short-description.md` (sequential numbering)
- **Research**: `descriptive-topic-name.md` (no numbering)
- **Exec Plans**: `docs/exec-plans/active/<feature-name>/plan.md`

## Document Templates

### Decision Record

```markdown
---
title: <Decision Title>
description: <One-line: chose X because Y>
status: active
date: YYYY-MM-DD
related: []
---

# <Decision Title>

## Context

What situation prompted this decision?

## Decision

What was decided?

## Alternatives Considered

- **Option A**: ...
- **Option B**: ...

## Consequences

What are the implications?
```

### Known Issue

```markdown
---
title: <Issue Title>
description: <One-line summary of the problem>
status: active
severity: P1
related-plan: <plan-name>
date: YYYY-MM-DD
---

# <Issue Title>

## Symptoms

What does the user/developer see?

## Root Cause

What causes this? (if known)

## Workaround

Any current mitigation?

## Resolution Path

What needs to happen to fix this?
```

### Exec Plan

```markdown
---
title: <Feature/Task Name>
description: <One-line goal>
status: in-progress
date: YYYY-MM-DD
---

# <Feature/Task Name>

## Goal

<What we're building and why>

## Phases

### Phase 1: <name>
- [ ] Task 1
- [ ] Task 2

### Phase 2: <name>
- [ ] Task 3

## Handoff Notes

<Updated when handing off to another agent or session>
```

## Retrieval Model

Two paths for agents to find information:

**Path A (Automatic)**: Session-start hook parses frontmatter, assembles a `<session-context>` block with active plans, known issues, and workflow rules. Agent receives this automatically.

**Path B (Manual)**: Agent globs file names in `docs/decisions/`, `docs/research/`, etc., reads relevant files on demand. File names are self-descriptive for this purpose.

## Lifecycle Rules

- **Exec plans**: `active/` while in progress, move to `completed/` when done
- **Known issues**: Top-level while active, move to `resolved/` when fixed
- **Decisions**: Stay in `decisions/` permanently. If superseded, update `status: superseded-by <new-ID>`
- **Research**: Stays in `research/` permanently
- **Archive**: One-time project artifacts (PRD, specs) that won't be updated
