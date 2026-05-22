# Agent Hygiene Skill

Audit local coding-agent skills, tool setup, and recent usage signals so users can keep only the agent capabilities that are useful.

## Install

```sh
npx --yes skills@latest add <your-github-user>/agent-hygiene-skill \
  --global \
  --agent '*' \
  --skill agent-hygiene
```

For Codex only:

```sh
npx --yes skills@latest add <your-github-user>/agent-hygiene-skill \
  --global \
  --agent codex \
  --skill agent-hygiene
```

## Use

```text
Use $agent-hygiene to audit my local agent setup and recommend what to keep, move, or remove.
```

The skill is explicit-only for Codex, so it should not be injected into ordinary sessions.

## Privacy

The bundled audit script runs locally. It inspects common local skill directories, Codex session files, and optional Codex plugin/MCP command output. It does not upload data.

## Licence

MIT. See [LICENSE](LICENSE).
