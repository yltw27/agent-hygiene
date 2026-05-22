---
name: agent-hygiene
description: Explicit-only audit of local coding-agent setup, installed skills, MCP servers, plugins, and recent usage signals. Use only when the user explicitly invokes $agent-hygiene.
---

# Agent Hygiene

## Invocation Policy

This skill must stay explicit-only. Keep `agents/openai.yaml` with `policy.allow_implicit_invocation: false` so the skill is not injected into normal sessions by default.

Do not edit, disable, unlink, uninstall, or remove anything during the audit unless the user explicitly asks for a follow-up cleanup step.

## Scope

Audit the user's local coding-agent setup and recommend how to reduce context noise and tool-selection ambiguity.

Focus on:

- Installed skills across Codex and common shared skill directories
- Codex plugins and MCP servers
- Duplicate or overlapping skills
- Skills installed globally that should be project-local
- Broad mandatory skills that may trigger too often
- Explicit skill mentions and tool-call signals in recent Codex sessions
- Skills with no visible recent use

Treat usage data as a signal, not proof. Implicit skill triggering may not be visible in logs, and old sessions may be compacted or absent.

## Workflow

1. Ask a clarifying question only if the user wants a non-default scope. Default to the last 30 days and the current machine.
2. Run the bundled audit script from the skill directory:

```sh
python3 /path/to/agent-hygiene/scripts/audit_agent_hygiene.py --days 30
```

3. Inspect the script output. Read specific `SKILL.md` files only when needed to verify broad descriptions, overlap, or agent-specific instructions.
4. Produce recommendations. Do not run uninstall commands.

## Recommendation Rubric

Use these categories:

- `Keep`: recently used, narrow trigger, high-value workflow, or installed as part of an enabled plugin the user actively uses.
- `Move project-local`: useful only in one repo or team context.
- `Make explicit-only`: rare, broad, expensive, or potentially disruptive but still useful on demand.
- `Rewrite`: useful skill with vague, overlapping, or "always/mandatory" trigger wording.
- `Remove`: duplicate, stale, wrong-agent install, broken path, or no credible recent use.
- `Investigate`: usage evidence is too thin to recommend confidently.

Prefer pruning global auto-triggerable skills before plugin or system skills. For plugin-provided skills, recommend disabling/removing the plugin only when the whole plugin appears unused.

## Output

Return a concise audit:

- `Summary`: counts and main risk.
- `Recommendations`: grouped by action, with evidence.
- `Notes`: limitations of the usage evidence.
- `Next command`: one safe command to inspect or verify, not a destructive cleanup command.

Be direct. The goal is a smaller, higher-signal agent setup, not a complete inventory dump.
