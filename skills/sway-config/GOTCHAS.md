# Non-Obvious Sway Behaviors

Ten gotchas discovered from real debugging. Each one has caused silent failures or confusing symptoms.

---

### 1. dirname "$0" Returns "." in Sway Exec Context

**Symptom:** A script that works fine from the terminal silently fails when launched by sway's exec or exec_always. Paths to sibling files (filters, helpers, configs) resolve to the current directory instead of the script's directory.

**Root cause:** Sway launches exec commands as `sh -c '<command>'`. Inside this shell, `$0` is literally `sh` — not the script's path. `dirname "sh"` returns `.` (the current directory), so any path built from it points to the wrong location.

```sh
# BROKEN — $0 is "sh", SCRIPT_DIR becomes "."
SCRIPT_DIR="$(dirname "$0")"
FILTER="$SCRIPT_DIR/clipboard-filter.py"
# Resolves to: ./clipboard-filter.py
# File not found, daemon silently not started
```

```sh
# CORRECT — use $HOME-relative or absolute paths
FILTER="$HOME/.config/sway/scripts/clipboard-filter.py"
# Or:
FILTER="/home/milo/.config/sway/scripts/clipboard-filter.py"
```

**Fix:** Never use `dirname "$0"` in scripts launched by sway. Use `$HOME`-relative paths or hardcoded absolute paths for all file references.

---

### 2. exec_always {} Blocks Are Unreliable for Daemons

**Symptom:** Daemons defined as sway variables fail to start when placed inside an `exec_always {}` block. No error appears. The daemon simply is not running after reload.

**Root cause:** When an `exec_always {}` block contains variables that expand to compound shell commands (commands with `;`, `&&`, or brace groups), sway's block-to-line translation can cause the shell process to not properly wait for or attach the blocking daemon subprocess.

```sway
# BROKEN — daemons may silently not start inside block
exec_always {
    $cliphist_store
    $cliphist_watch
}
```

```sway
# CORRECT — standalone exec_always lines
exec_always $cliphist_store
exec_always $cliphist_watch
```

**Fix:** Move every daemon-launching `exec_always` to its own standalone line outside any block. Block syntax is fine for simple, quick-exit commands, but unreliable for long-running processes.

---

### 3. pkill -f Self-Matching: Compound Commands Kill Themselves

**Symptom:** A daemon never starts after `swaymsg reload`. Adding debug logging shows the script runs, pkill runs, but the daemon command after pkill never executes.

**Root cause:** When sway runs `exec_always $var`, it calls `sh -c '<expanded value>'`. The sh process's argv[2] contains the entire expanded command string — including the daemon command that appears later in the compound. Without a `^` anchor, `pkill -f` searches all argv strings and can match the running sh process itself, killing it before the daemon command ever executes.

```sway
set $cliphist_store 'pkill -f "wl-paste.*clipboard-filter" 2>/dev/null; wl-paste --watch ~/.config/sway/scripts/clipboard-filter.py'
```

When sway runs this, the sh process has `wl-paste --watch .../clipboard-filter.py` in its argv. `pkill -f "wl-paste.*clipboard-filter"` matches it and kills the sh process that was about to run wl-paste.

```sh
# BROKEN — no anchor, matches the sh process itself
pkill -f "wl-paste.*clipboard-filter"

# CORRECT — ^ anchors to start of command line
# sh process starts with "sh", not "wl-paste", so it is safe
pkill -f "^wl-paste --watch.*clipboard-filter"
```

**Fix:** Always anchor pkill patterns with `^` when killing a daemon by name inside a compound command. Even better: extract the logic to a dedicated script — the script's argv is just `sh /path/to/script.sh`, which never matches `^wl-paste`.

---

### 4. PATH Does Not Include User Directories

**Symptom:** A command in an exec_always variable fails with "command not found" or silently does nothing, even though the command works fine from the terminal.

**Root cause:** Sway's exec environment has a restricted PATH. The following directories are NOT present by default:
- `~/.local/bin`
- `~/.cargo/bin`
- `~/bin`

Tools installed with pip, pipx, cargo, npm global, or custom scripts in `~/.scripts` are all invisible to sway's exec context.

```sway
# BROKEN — waybar-signal lives in ~/.local/bin, not in sway's PATH
set $cliphist_watch 'wl-paste --watch waybar-signal clipboard'
```

```sway
# CORRECT — absolute path
set $cliphist_watch 'wl-paste --watch /home/milo/.local/bin/waybar-signal clipboard'
```

Alternatively, export PATH at the top of the called script:

```sh
#!/bin/sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
# Now user-installed tools are available
exec my-tool --args
```

**Fix:** Use absolute paths for any binary in user-local directories when calling from sway exec context. Or set PATH explicitly in a wrapper script.

---

### 5. Tilde ~ Expansion in Variable Values

**Symptom:** Paths using `~` work in some places but behave unexpectedly in others. Confusion about whether `~` is safe in sway config.

**Root cause:** `~` does expand inside sway variable values when those variables are used with exec/exec_always, because sway passes the value to `sh -c` and sh performs tilde expansion. However, `~` does NOT expand in all contexts — it depends on whether the value passes through a shell.

In config commands that do not invoke sh (like `include`), `~` still works because sway uses `wordexp(3)` which handles tilde expansion.

```sway
# ~ works here — wordexp handles it
include ~/.config/sway/config.d/*

# ~ works here — passed to sh -c which expands it
exec_always ~/.config/sway/scripts/my-daemon.sh
```

**Fix:** Prefer `$HOME` over `~` in sway variable values for explicitness and reliability. `$HOME` is an environment variable that is always set; `~` depends on context.

```sway
# Explicit — use $HOME
set $daemon '$HOME/.config/sway/scripts/my-daemon.sh'
```

---

### 6. pgrep/pkill ERE Alternation: | Not \|

**Symptom:** A pgrep command used for debugging always returns "no match" even when the process is clearly running (verified by ps). The pattern looks correct.

**Root cause:** pgrep and pkill use Extended Regular Expressions (ERE) by default. In ERE, alternation is `|` (bare pipe). The BRE syntax `\|` is not alternation in ERE — it is a literal backslash followed by a pipe character.

```bash
# BROKEN — \| in ERE is not alternation, pattern never matches
pgrep -a -f "clipboard-filter\|waybar-signal"

# CORRECT — ERE alternation uses bare |
pgrep -a -f "clipboard-filter|waybar-signal"
```

This matters when debugging: a broken pgrep pattern always reports "no match" even when the daemon is running, making it look like the daemon failed to start when it actually started fine.

**Fix:** Use bare `|` for alternation in pgrep/pkill patterns. If you need to match a literal pipe, escape it: `\|`.

---

### 7. set $var Quoting Rules

**Symptom:** A sway variable containing shell operators (`;`, `&&`) behaves differently than expected, or parts of the value are interpreted as separate sway commands.

**Root cause:** In sway config, `;` is a command separator at the top level. But when you quote the value in `set $var 'value'`, the single-quoted string is stored verbatim. The semicolons inside the quotes are NOT treated as sway command separators. They are passed as-is to sh when the variable is used in exec_always.

```sway
# CORRECT — single quotes preserve everything literally
set $cliphist_store 'pkill -f "^cliphist" 2>/dev/null; exec cliphist store'

# When used:
exec_always $cliphist_store
# sway calls: sh -c 'pkill -f "^cliphist" 2>/dev/null; exec cliphist store'
# sh sees the ; as a command separator — works correctly
```

Shell constructs that work inside quoted set values:
- `;` — works (passed to sh)
- `&&`, `||` — work
- `$()` — works (sh evaluates command substitution)
- `>>`, `|` — work
- `{ cmd1; cmd2; }` — work syntactically

**Fix:** Use single quotes for variable values that contain shell operators. The value is stored verbatim and sh interprets the operators when executing.

---

### 8. Config Include Order Is Alphabetical

**Symptom:** A variable used in `99-autostart.conf` is undefined or has the wrong value. The variable is defined in another file in the same `config.d/` directory.

**Root cause:** `include ~/.config/sway/config.d/*` processes files in alphabetical (lexicographic) order. If a file defining a variable sorts after the file using it, the variable is undefined when first referenced.

```
config.d/
├── 50-definitions.conf   # defines $daemon_var
└── 20-autostart.conf     # uses $daemon_var  <-- loaded BEFORE 50-definitions.conf
                          # $daemon_var is undefined here!
```

```
config.d/
├── 01-definitions.conf   # defines $daemon_var  <-- loaded first
└── 99-autostart.conf     # uses $daemon_var     <-- loaded after, variable is defined
```

**Fix:** Use numeric prefixes to enforce load order. Variables and definitions should use a low prefix (`01-`, `05-`). Files that consume those variables should use a higher prefix (`90-`, `99-`).

---

### 9. Debugging exec_always: Verify What Actually Ran

**Symptom:** After `swaymsg reload`, a daemon does not appear to be running. Unclear whether the script was called at all, or whether it ran but failed internally.

**Root cause:** exec_always failures are silent. There is no output to a terminal. The only feedback is swaynag for config parse errors — runtime failures produce nothing visible.

**Fix:** Add temporary debug logging to distinguish "script was never called" from "script ran but daemon failed to start":

```sway
# Add temporarily to 99-autostart.conf to confirm exec_always fires
exec_always sh -c "echo 'autostart reached at $(date)' >> /tmp/sway-debug.log"
```

```sh
#!/bin/sh
# Add to top of daemon script to confirm it was called
echo "script ran at $(date), HOME=$HOME, PATH=$PATH" >> /tmp/sway-debug.log

# After daemon starts, verify it is actually running:
# pgrep -a -f "^daemon-binary-name"
```

```bash
# Check if daemon is running (use correct ERE syntax)
pgrep -a -f "^wl-paste --watch"

# View sway's own log for exec errors
journalctl --user -u sway -n 50
```

**Fix:** Log to `/tmp/sway-debug.log` from both the sway config and the script. Check `$HOME` and `$PATH` in the log — they reveal context issues immediately.

---

### 10. General Rules for Sway Daemon Management

**Symptom:** Various daemon management approaches work sometimes but fail on reload or produce duplicate processes.

**Root cause:** Managing daemons from `exec_always` requires careful handling of: process cleanup before restart, avoiding self-matching pkill, using absolute paths, and choosing standalone exec_always over blocks.

**The pattern that works:**

```sh
#!/bin/sh
# ~/.config/sway/scripts/daemon-name.sh
#
# Rules:
# 1. Use $HOME paths — never dirname "$0" ($0 is "sh" in sway exec context)
# 2. Anchor pkill with ^ to avoid matching this sh process
# 3. exec at the end to replace shell with daemon (clean process tree)

pkill -f "^daemon-binary-name" 2>/dev/null
exec daemon-binary-name --config "$HOME/.config/daemon/config"
```

```sway
# In definitions file:
set $daemon_name '/home/milo/.config/sway/scripts/daemon-name.sh'

# In autostart file — standalone, NOT inside exec_always {} block:
exec_always $daemon_name
```

```
# Broken patterns to avoid:
```

| Anti-pattern | Problem | Fix |
|---|---|---|
| `dirname "$0"` in script | `$0` is `sh`, paths resolve wrong | Use `$HOME` or absolute paths |
| Daemon in `exec_always {}` block | Unreliable for blocking commands | Standalone `exec_always` line |
| `pkill -f "pattern"` without `^` | May kill the running sh process | Add `^` anchor |
| Bare binary names from `~/.local/bin` | Not in sway's PATH | Use absolute path |
| `~` in complex variable values | Context-dependent expansion | Use `$HOME` |
| `pgrep -f "a\|b"` | `\|` is not ERE alternation | Use bare `\|` |

---

## Summary Table

| Issue | Symptom | Root cause | Fix |
|-------|---------|------------|-----|
| `dirname "$0"` | Script silently fails, paths wrong | `$0` is `sh` in sway exec context | Use `$HOME/...` paths |
| `exec_always {}` block | Daemon not starting | Complex blocking commands unreliable in block | Use standalone `exec_always` lines |
| pkill self-match | Compound command kills itself | pkill -f without `^` matches sh's full argv | Anchor with `^` OR use a dedicated script |
| PATH missing user dirs | `command: not found` | sway exec PATH lacks `~/.local/bin` etc. | Use absolute path |
| `~` expansion | Inconsistent path resolution | Context-dependent, not always shell-expanded | Prefer `$HOME` |
| pgrep `\|` alternation | pgrep finds nothing (false negative) | `\|` is not alternation in ERE | Use bare `\|` |
| Variable quoting | Operators misinterpreted | Confusion about when sway vs sh parses | Single-quote complex values |
| Include order | Variable undefined | Alphabetical load order, file sorts wrong | Use numeric prefixes `01-`, `99-` |
| Silent exec failures | Daemon missing, no error output | exec_always failures produce no output | Add `>> /tmp/sway-debug.log` temporarily |
| Duplicate daemons | Old + new instance both running | exec_always re-runs without killing old | pkill before exec in script |
