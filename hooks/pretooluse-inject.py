#!/usr/bin/env python3
"""PreToolUse hook: inject eww/sway skills based on pathPatterns and bashPatterns.

Reads tool input from stdin, matches against SKILL.md frontmatter patterns,
returns the best matching skill as additionalContext. Deduplicates per session.
"""

import fnmatch
import json
import os
import re
import sys

MAX_SKILLS = 2
PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(PLUGIN_ROOT, "skills")


def parse_frontmatter(filepath):
    """Extract YAML frontmatter fields from a SKILL.md file."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    result = {"_body": text[end + 3:].strip(), "_path": filepath}
    # Simple YAML parser for our flat structure
    current_key = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[0] != " " and ":" in stripped:
            key, _, val = stripped.partition(":")
            current_key = key.strip()
            val = val.strip()
            if val:
                if val.startswith("[") and val.endswith("]"):
                    # Parse JSON array
                    try:
                        result[current_key] = json.loads(val)
                    except json.JSONDecodeError:
                        result[current_key] = val
                else:
                    result[current_key] = val.strip('"').strip("'")
        elif current_key == "metadata" and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                try:
                    result[f"metadata.{key}"] = json.loads(val)
                except json.JSONDecodeError:
                    result[f"metadata.{key}"] = val
            elif val.isdigit():
                result[f"metadata.{key}"] = int(val)
            else:
                result[f"metadata.{key}"] = val.strip('"').strip("'")
    return result


def load_skills():
    """Load all skills with their patterns."""
    skills = []
    if not os.path.isdir(SKILLS_DIR):
        return skills
    for name in os.listdir(SKILLS_DIR):
        skill_md = os.path.join(SKILLS_DIR, name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        fm = parse_frontmatter(skill_md)
        skills.append({
            "name": fm.get("name", name),
            "priority": fm.get("metadata.priority", 5),
            "pathPatterns": fm.get("metadata.pathPatterns", []),
            "bashPatterns": fm.get("metadata.bashPatterns", []),
            "body": fm.get("_body", ""),
            "path": fm.get("_path", ""),
        })
    return skills


def get_seen_skills(session_id):
    """Read already-injected skills for this session."""
    seen_file = f"/tmp/skill-inject-{session_id}.txt"
    if os.path.exists(seen_file):
        with open(seen_file, "r") as f:
            return set(f.read().strip().split(",")) - {""}
    return set()


def mark_seen(session_id, skill_name):
    """Record that a skill was injected."""
    seen_file = f"/tmp/skill-inject-{session_id}.txt"
    seen = get_seen_skills(session_id)
    seen.add(skill_name)
    with open(seen_file, "w") as f:
        f.write(",".join(seen))


def match_path(patterns, file_path):
    """Match file_path against glob patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
        # Also try basename
        if fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True
    return False


def match_bash(patterns, command):
    """Match bash command against regex patterns."""
    for pattern in patterns:
        try:
            if re.search(pattern, command):
                return True
        except re.error:
            continue
    return False


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        print("{}")
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    session_id = data.get("session_id", "default")

    # Determine target to match
    if tool_name in ("Read", "Edit", "Write"):
        target = tool_input.get("file_path", "")
        match_type = "path"
    elif tool_name == "Bash":
        target = tool_input.get("command", "")
        match_type = "bash"
    else:
        print("{}")
        return

    if not target:
        print("{}")
        return

    skills = load_skills()
    seen = get_seen_skills(session_id)

    # Find matching skills
    matches = []
    for skill in skills:
        if skill["name"] in seen:
            continue
        if match_type == "path" and match_path(skill["pathPatterns"], target):
            matches.append(skill)
        elif match_type == "bash" and match_bash(skill["bashPatterns"], target):
            matches.append(skill)

    if not matches:
        print("{}")
        return

    # Sort by priority descending, take top N
    matches.sort(key=lambda s: s["priority"], reverse=True)
    selected = matches[:MAX_SKILLS]

    # Build context and mark as seen
    context_parts = []
    for skill in selected:
        mark_seen(session_id, skill["name"])
        context_parts.append(f"# Skill: {skill['name']}\n\n{skill['body']}")

    context = "\n\n---\n\n".join(context_parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
