# Agent Hygiene Skill

[![skills.sh](https://skills.sh/b/yltw27/agent-hygiene)](https://skills.sh/yltw27/agent-hygiene)

Local-first hygiene checks for coding-agent setups.

`agent-hygiene` audits installed skills, Codex plugin/MCP setup, duplicate or broad triggers, and recent usage signals so users can reduce context noise and keep agent workflows focused.

## Install

```sh
npx --yes skills@latest add yltw27/agent-hygiene \
  --global \
  --agent '*' \
  --skill agent-hygiene
```

For Codex only:

```sh
npx --yes skills@latest add yltw27/agent-hygiene \
  --global \
  --agent codex \
  --skill agent-hygiene
```

## Use

```text
Use $agent-hygiene to audit my local agent setup and recommend what to keep, move, or remove.
```

The skill is explicit-only for Codex, so it should not be injected into ordinary sessions.

## Example Output

```text
# Agent hygiene audit

- Skills discovered: 20
- Duplicate skill names: 0
- Broad-trigger candidates: 0
- Explicit-only skills: 6

## Recommendations

### Rewrite or make explicit-only
- `example-skill` (global): trigger words: always, mandatory

### Low visible recent use
- `old-workflow` (global) at `~/.agents/skills/old-workflow`
```

## Privacy

The bundled audit script runs locally. It inspects common local skill directories, Codex session files, and optional Codex plugin/MCP command output. It does not upload data, and recommendations are based on local signals that may be incomplete.

## Licence

MIT. See [LICENSE](LICENSE).
