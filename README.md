# Agent Hygiene Skill

[![skills.sh](https://skills.sh/b/yltw27/agent-hygiene)](https://skills.sh/yltw27/agent-hygiene)

> Skills accumulate. Most don't get cleaned up.

`agent-hygiene` is a local-first audit skill for coding-agent setups. It inspects your installed skills, MCP/plugin configuration, and recent usage signals to surface what's causing context noise — stale skills, broad triggers, duplicates — and tells you what to keep, tighten, or remove.

Unlike runtime hygiene tools that manage token budgets mid-session, `agent-hygiene` operates at installation time: it's a one-shot audit you run when your agent setup starts feeling bloated or unfocused.

## How it works

When invoked, the skill runs a local Python script that:

1. Scans common skill directories (`~/.claude/skills`, `~/.agents/skills`, and others)
2. Checks for duplicate skill names across global and project scopes
3. Flags skills with broad or mandatory trigger words that inject into every session
4. Reads Codex session files (if present) to identify skills with low recent use
5. Optionally queries your Codex plugin/MCP setup for installed tool metadata

All analysis runs locally. Nothing is uploaded.

## Install

**All agents:**

```sh
npx --yes skills@latest add yltw27/agent-hygiene \
  --global \
  --agent '*' \
  --skill agent-hygiene
```

**Codex only:**

```sh
npx --yes skills@latest add yltw27/agent-hygiene \
  --global \
  --agent codex \
  --skill agent-hygiene
```

> The skill is marked `explicit-only` for Codex, so it will not be injected into ordinary sessions.

## Use

```
Use $agent-hygiene to audit my local agent setup and recommend what to keep, move, or remove.
```

Run this periodically — after installing several new skills, after switching agents, or whenever sessions feel slower than expected.

## Example output

```
# Agent hygiene audit

- Skills discovered: 20
- Duplicate skill names: 0
- Broad-trigger candidates: 2
- Explicit-only skills: 6

## Recommendations

### Rewrite or make explicit-only
- `example-skill` (global): trigger words: always, mandatory

### Low visible recent use
- `old-workflow` (global) at ~/.agents/skills/old-workflow
```

## Privacy

The bundled audit script runs entirely on your machine. It inspects local skill directories, Codex session files, and optional plugin/MCP command output. It does not send data anywhere. Recommendations are based on local signals and may be incomplete depending on your agent setup.

## License

MIT. See [LICENSE](./LICENSE).