#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path


SKILL_DIRS = [
    ".codex/skills",
    ".agents/skills",
    ".claude/skills",
    ".cursor/skills",
    ".config/agents/skills",
]

BROAD_TRIGGER_WORDS = {
    "always",
    "any",
    "before any",
    "do not skip",
    "every",
    "mandatory",
    "must",
    "whenever",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Audit local agent skills and recent Codex usage.")
    parser.add_argument("--days", type=int, default=30, help="How many recent days of Codex sessions to scan.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    parser.add_argument("--root", default=os.getcwd(), help="Project root to inspect for project-local skills.")
    parser.add_argument("--skip-commands", action="store_true", help="Skip codex plugin/mcp command probes.")
    return parser.parse_args()


def parse_frontmatter(path):
    try:
        text = path.read_text(errors="replace")
    except OSError as exc:
        return {}, f"read failed: {exc}"

    if not text.startswith("---\n"):
        return {}, "missing frontmatter"

    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}, "invalid frontmatter"

    data = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data, None


def read_openai_policy(skill_dir):
    config = skill_dir / "agents" / "openai.yaml"
    if not config.exists():
        return {}
    try:
        text = config.read_text(errors="replace")
    except OSError:
        return {}
    return {
        "allow_implicit_invocation": "allow_implicit_invocation: false" not in text,
        "has_openai_yaml": True,
    }


def is_under(path, parent):
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def candidate_skill_roots(home, project_root):
    roots = []
    for rel in SKILL_DIRS:
        roots.append((home / rel, "global"))

    current = project_root.resolve()
    for folder in [current, *current.parents]:
        root = folder / ".agents" / "skills"
        roots.append((root, "project"))
        if (folder / ".git").exists():
            break
    return roots


def find_skills(home, project_root):
    skills = []
    seen_paths = set()

    for root, scope in candidate_skill_roots(home, project_root):
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue
            resolved = child.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)

            frontmatter, error = parse_frontmatter(skill_md)
            policy = read_openai_policy(child)
            description = frontmatter.get("description", "")
            name = frontmatter.get("name") or child.name
            broad_hits = sorted(word for word in BROAD_TRIGGER_WORDS if word in description.lower())
            skills.append(
                {
                    "name": name,
                    "path": str(child),
                    "resolved_path": str(resolved),
                    "scope": scope,
                    "source_root": str(root),
                    "is_symlink": child.is_symlink(),
                    "symlink_target": os.readlink(child) if child.is_symlink() else None,
                    "description_chars": len(description),
                    "broad_trigger_words": broad_hits,
                    "explicit_only": policy.get("has_openai_yaml") and not policy.get("allow_implicit_invocation", True),
                    "frontmatter_error": error,
                }
            )
    return skills


def extract_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(extract_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(extract_text(item) for item in value.values())
    return ""


def walk_tool_names(value):
    if isinstance(value, dict):
        for key in ("recipient_name", "tool_name"):
            found = value.get(key)
            if isinstance(found, str):
                yield found
        event_type = value.get("type")
        if isinstance(event_type, str) and event_type in {"function_call", "tool_call"} and isinstance(value.get("name"), str):
            yield value["name"]
        for item in value.values():
            yield from walk_tool_names(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_tool_names(item)


def scan_sessions(home, skills, days):
    sessions_dir = home / ".codex" / "sessions"
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    skill_names = sorted({skill["name"] for skill in skills})
    explicit_patterns = {name: re.compile(rf"(?<![\w-])(?:\$|/){re.escape(name)}(?![\w-])") for name in skill_names}
    mention_counts = Counter()
    tool_counts = Counter()
    scanned_files = 0
    scanned_lines = 0

    if not sessions_dir.exists():
        return {
            "sessions_dir": str(sessions_dir),
            "scanned_files": 0,
            "scanned_lines": 0,
            "skill_mentions": {},
            "tool_calls": {},
        }

    for path in sessions_dir.rglob("*.jsonl"):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        except OSError:
            continue
        if mtime < cutoff:
            continue
        scanned_files += 1
        try:
            handle = path.open(errors="replace")
        except OSError:
            continue
        file_mentions = set()
        with handle:
            for line in handle:
                scanned_lines += 1
                for name, pattern in explicit_patterns.items():
                    if pattern.search(line):
                        file_mentions.add(name)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                for tool_name in walk_tool_names(event):
                    tool_counts[tool_name] += 1
        for name in file_mentions:
            mention_counts[name] += 1

    return {
        "sessions_dir": str(sessions_dir),
        "scanned_files": scanned_files,
        "scanned_lines": scanned_lines,
        "skill_mentions": dict(sorted(mention_counts.items())),
        "tool_calls": dict(tool_counts.most_common(40)),
    }


def run_command(command):
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "ok": False, "output": str(exc)}
    output = (result.stdout or result.stderr).strip()
    return {"command": command, "ok": result.returncode == 0, "output": output}


def codex_command():
    found = shutil.which("codex")
    if found:
        return found
    app_path = Path("/Applications/Codex.app/Contents/Resources/codex")
    if app_path.exists():
        return str(app_path)
    return None


def command_inventory(skip):
    if skip:
        return {}
    codex = codex_command()
    if not codex:
        return {"codex": "not found"}
    return {
        "plugin_list": run_command([codex, "plugin", "list"]),
        "mcp_list": run_command([codex, "mcp", "list"]),
    }


def build_report(data):
    skills = data["skills"]
    usage = data["usage"]
    by_name = defaultdict(list)
    for skill in skills:
        by_name[skill["name"]].append(skill)

    duplicates = {name: items for name, items in by_name.items() if len(items) > 1}
    broad = [skill for skill in skills if skill["broad_trigger_words"] or skill["description_chars"] > 700]
    unused = [
        skill
        for skill in skills
        if usage["skill_mentions"].get(skill["name"], 0) == 0
        and not skill["name"].startswith(".")
    ]
    explicit_only = [skill for skill in skills if skill["explicit_only"]]

    lines = [
        "# Agent hygiene audit",
        "",
        f"- Skills discovered: {len(skills)}",
        f"- Duplicate skill names: {len(duplicates)}",
        f"- Broad-trigger candidates: {len(broad)}",
        f"- Explicit-only skills: {len(explicit_only)}",
        f"- Codex session files scanned: {usage['scanned_files']} ({usage['scanned_lines']} lines)",
        "",
        "## Recommendations",
        "",
    ]

    if duplicates:
        lines.append("### Investigate duplicates")
        for name, items in sorted(duplicates.items()):
            paths = ", ".join(item["path"] for item in items)
            lines.append(f"- `{name}` appears in multiple locations: {paths}")
        lines.append("")

    if broad:
        lines.append("### Rewrite or make explicit-only")
        for skill in sorted(broad, key=lambda item: item["name"]):
            evidence = []
            if skill["broad_trigger_words"]:
                evidence.append("trigger words: " + ", ".join(skill["broad_trigger_words"]))
            if skill["description_chars"] > 700:
                evidence.append(f"description {skill['description_chars']} chars")
            lines.append(f"- `{skill['name']}` ({skill['scope']}): {'; '.join(evidence)}")
        lines.append("")

    if unused:
        lines.append("### Low visible recent use")
        for skill in sorted(unused, key=lambda item: (item["scope"], item["name"]))[:30]:
            suffix = " explicit-only" if skill["explicit_only"] else ""
            lines.append(f"- `{skill['name']}` ({skill['scope']}{suffix}) at `{skill['path']}`")
        if len(unused) > 30:
            lines.append(f"- ...and {len(unused) - 30} more")
        lines.append("")

    if usage["tool_calls"]:
        lines.append("## Top tool-call signals")
        for tool, count in list(usage["tool_calls"].items())[:15]:
            lines.append(f"- `{tool}`: {count}")
        lines.append("")

    lines.append("## Limits")
    lines.append("")
    lines.append("- Skill mention counts are session-file counts for explicit `$skill` or `/skill` references.")
    lines.append("- Implicit skill use, compacted context, and non-Codex agent histories may be invisible.")
    lines.append("- Treat recommendations as a pruning shortlist, not proof that a skill is useless.")
    return "\n".join(lines)


def main():
    args = parse_args()
    home = Path.home()
    project_root = Path(args.root)
    skills = find_skills(home, project_root)
    usage = scan_sessions(home, skills, args.days)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": args.days,
        "project_root": str(project_root.resolve()),
        "skills": skills,
        "usage": usage,
        "commands": command_inventory(args.skip_commands),
    }
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(build_report(data))


if __name__ == "__main__":
    main()
