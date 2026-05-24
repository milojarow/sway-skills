# Sway Configuration


Sway reads a configuration file at startup and executes each line as a sway command. The config is not a shell script — it is a list of sway commands with their own syntax, quoting rules, and variable system. Understanding how sway parses its config is essential before writing or debugging it, because mistakes silently do nothing or cause daemons to not start.

---

## Command Syntax

### One command per line
Each line is one command. Lines are extended across multiple physical lines with a trailing backslash:

```sway
bindsym Shift+XF86AudioRaiseVolume exec \
    pactl set-sink-volume @DEFAULT_SINK@ +1%
```

### Arguments and quoting
Commands split on spaces. Use quotes to include spaces in a single argument:

```sway
# Single or double quotes work
set $term 'foot --title Terminal'
set $term "foot --title Terminal"
```

### Command separators: `,` vs `;`
Two separators exist and behave differently:

| Separator | Criteria behavior | Use case |
|-----------|-------------------|----------|
| `,` | Retained across commands | Chain commands on same window |
| `;` | Reset (new criteria allowed) | Independent sequential commands |

```sway
# , keeps criteria: move the focused floating window to workspace 2
[floating] move to workspace 2, focus
# ; resets: two independent commands
bindsym $mod+Return exec foot; focus
```

### Block syntax
A block prepends everything before `{` to each line inside it:

```sway
output eDP-1 {
    background ~/wallpaper.png fill
    resolution 1920x1080
}
# Identical to:
output eDP-1 background ~/wallpaper.png fill
output eDP-1 resolution 1920x1080
```

Block syntax is convenient for `output`, `input`, `bar`, and `mode` definitions. However, **do not use blocks for exec_always with daemons** — see this document.

### Special characters in documentation
In sway man pages: `|` separates mutually exclusive options, `[...]` marks optional arguments, `<...>` marks values you supply.

---

## Variables

### Defining variables
```sway
set $name value
set $name 'value with spaces'
set $name "value with spaces"
```

Variables are substituted by name at config-parse time everywhere they appear in subsequent commands.

### Variable naming
Variables must start with `$`. By convention, use lowercase with underscores:
```sway
set $mod Mod4
set $term foot
set $browser firefox
set $scripts_dir '/home/milo/.config/sway/scripts'
```

### Variable expansion
Variables expand literally — the stored string is substituted wherever `$name` appears:

```sway
set $mod Mod4
bindsym $mod+Return exec foot
# Becomes: bindsym Mod4+Return exec foot
```

### Escaping variables (deferred expansion)
Double `$$` defers expansion to runtime instead of config-parse time:

```sway
set $ws1 "1"
# $$ws1 is replaced at runtime, not at parse time
workspace $$ws1
```

This matters for commands that need to evaluate the value at the moment they run, not when the config loads.

### Shell constructs that work inside variable values
Sway passes variable values to `sh -c` when used with exec/exec_always. These constructs work:

| Construct | Example | Notes |
|-----------|---------|-------|
| Semicolons `;` | `'cmd1; cmd2'` | sway does not treat `;` as separator inside a quoted value |
| `&&` and `\|\|` | `'cmd1 && cmd2'` | Works |
| `$()` substitution | `'cmd $(date)'` | Passed literally to sh |
| Redirections `>>` `\|` | `'cmd >> /tmp/log'` | Works |
| Brace groups | `'{ cmd1; cmd2; }'` | Syntactically valid |

**However:** complex compound commands that launch blocking daemons are unreliable inside `exec_always {}` blocks. See this document.

### What does NOT work in variable values
- `dirname "$0"` to find a script's own location — `$0` is `sh` in sway's exec context
- Relying on `~/.local/bin` or `~/.cargo/bin` being in PATH — they are not
- `~` tilde expansion is supported but `$HOME` is more explicit and reliable

---

## Config File Structure

### Default locations (checked in order)
1. `$XDG_CONFIG_HOME/sway/config` (usually `~/.config/sway/config`)
2. `~/.sway/config`
3. `$XDG_CONFIG_DIRS/sway/config`
4. `/etc/sway/config`

An example config is at `/etc/sway/config` — worth reading.

### The `include` directive
```sway
include <paths...>
```

- Paths may be absolute, relative to the parent config, or glob patterns
- Uses `wordexp(3)` for expansion — shell glob patterns work
- The **same file can only be included once**; subsequent includes of the same path are silently ignored

```sway
# Include all .conf files in config.d, in alphabetical order
include ~/.config/sway/config.d/*

# Include a specific file
include ~/.config/sway/themes/catppuccin
```

### Include order: alphabetical
When using a glob like `config.d/*`, files are included in alphabetical (lexicographic) order. Use numeric prefixes to control load order:

```
~/.config/sway/config.d/
├── 01-definitions.conf    # Variables, set commands — loaded first
├── 10-appearance.conf     # Colors, borders, fonts
├── 20-keybindings.conf    # bindsym, bindcode
├── 30-workspaces.conf     # workspace rules
├── 50-input.conf          # input device config
├── 60-output.conf         # monitor config
└── 99-autostart.conf      # exec, exec_always — loaded last
```

Variables defined in `01-definitions.conf` are available to all files loaded after it because sway processes includes sequentially.

### Typical modular layout

```
~/.config/sway/
├── config                  # Main file: sets mod key, includes config.d/*
├── config.d/
│   ├── 01-definitions.conf # set $var commands
│   ├── 20-keybindings.conf
│   ├── 50-input.conf
│   └── 99-autostart.conf   # exec / exec_always
└── scripts/
    ├── my-daemon.sh
    └── another-script.sh
```

The main `config` file should be minimal:
```sway
# Main sway config
set $mod Mod4

# Load modular config
include ~/.config/sway/config.d/*
```

---

## Config vs Runtime Commands

Some commands only work in the config file. Others work both in config and via `swaymsg` at runtime.

| Command | Config only | Runtime | Notes |
|---------|-------------|---------|-------|
| `include` | Yes | No | Config parse time only |
| `set` | Yes (mostly) | No | Variables resolved at parse time |
| `default_orientation` | Yes | No | |
| `workspace_layout` | Yes | No | |
| `xwayland` | Yes | No | |
| `swaybg_command` | Yes | No | |
| `swaynag_command` | Yes | No | |
| `exec` | Yes | No (use `swaymsg exec`) | |
| `exec_always` | Yes | No | |
| `bindsym` | Yes | Yes | |
| `output` | Yes | Yes | |
| `input` | Yes | Yes | |
| `mode` (define) | Yes | No | |
| `mode` (switch) | Yes | Yes | |
| `for_window` | Yes | Yes | |
| `assign` | Yes | Yes | |
| `gaps` | Yes | Yes | |
| `focus_follows_mouse` | Yes | Yes | |

Use `swaymsg <command>` to run runtime commands from scripts or keybindings.

---

## Reloading

```bash
swaymsg reload
```

### What reload does
- Re-reads and re-parses the config file
- Re-applies keybindings, output config, input config, window rules
- Re-runs all `exec_always` commands
- Does **not** re-run `exec` commands

### What reload does NOT reset
- Running applications and windows — they are untouched
- Existing workspace layout
- Window positions

### exec_always on reload
Every `exec_always` line runs again on reload. For daemons, this means the old instance must be killed before the new one starts. The standard pattern:

```sh
#!/bin/sh
# Kill existing instance, then start fresh
pkill -f "^my-daemon" 2>/dev/null
exec my-daemon --args
```

See this document for the complete reliable daemon management pattern.

### Reload workflow
```bash
# Edit config
vim ~/.config/sway/config.d/20-keybindings.conf

# Reload without restarting sway
swaymsg reload

# Check for errors — swaynag will display them if any
```

---

---

# exec and exec_always — Daemon Management

---

## exec vs exec_always

Both commands execute a shell command at sway startup. The difference is what happens on `swaymsg reload`:

| Command | At startup | On `swaymsg reload` |
|---------|-----------|---------------------|
| `exec` | Runs once | Does NOT run again |
| `exec_always` | Runs | Runs again every reload |

```sway
# Runs once when sway starts — will NOT re-run on reload
exec /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1

# Runs at startup AND every time you do swaymsg reload
exec_always $my_daemon
```

Use `exec` for things that should start once and keep running untouched (authentication agents, one-time environment setup).

Use `exec_always` for daemons that need to pick up config changes on reload (clipboard managers, notification daemons, bar processes, kanshi for output profiles).

---

## How sway spawns processes

Sway does not exec the command directly. It calls:

```sh
/bin/sh -c '<your command>'
```

This has two important consequences:

**1. Shell expansion happens.** `~`, `$HOME`, `&&`, `;`, `|`, `$()` are all interpreted by sh before your program receives them. This is a feature — it means you can use shell constructs in exec commands.

**2. Inside a launched script, `$0` is `sh`, not the script path.**

When sway runs `exec_always /path/to/script.sh`, the actual process is:
```
sh -c '/path/to/script.sh'
```

The shell that runs the script has `$0 = sh`. This is standard POSIX behavior for `sh -c`. Any attempt to find the script's own directory using `$0` will fail silently:

```sh
# BROKEN — $0 is "sh", dirname "sh" returns "."
SCRIPT_DIR="$(dirname "$0")"
FILTER="$SCRIPT_DIR/clipboard-filter.py"   # resolves to ./clipboard-filter.py
```

```sh
# CORRECT — use $HOME-relative or absolute paths
FILTER="$HOME/.config/sway/scripts/clipboard-filter.py"
```

**Rule:** Never use `dirname "$0"` or `$0`-relative paths in any script launched by sway's exec or exec_always.

---

## exec_always block vs standalone

Sway supports a block syntax that prepends a command to every line inside the block:

```sway
# Block syntax — looks clean but is UNRELIABLE for daemons
exec_always {
    $cliphist_store
    $cliphist_watch
    $kanshi
}
```

```sway
# Standalone syntax — RELIABLE for daemons
exec_always $cliphist_store
exec_always $cliphist_watch
exec_always $kanshi
```

### Why blocks are unreliable for daemons

Inside an `exec_always {}` block, sway translates each inner line to `exec_always <line>` and runs them. For long-running daemon variables, this translation breaks down when the variable's expanded value is a complex compound command (one containing `;`, `&&`, or brace groups `{ ... }`).

The shell process spawned for each line inside the block may not wait for blocking subprocesses, causing daemons to silently not start.

What works fine inside `exec_always {}` blocks:
- Simple one-liner commands
- Variables that expand to a single executable path
- Quick commands that exit immediately

What is unreliable inside `exec_always {}` blocks:
- Variables whose value is a compound command with `;` or `&&`
- Variables that launch blocking/long-running processes (daemons)

```sway
# Example showing the problem
set $cliphist_store 'wl-paste --watch cliphist store'
set $cliphist_watch 'wl-paste --type text --watch /home/milo/.local/bin/waybar-signal clipboard'

# UNRELIABLE — daemons may silently not start
exec_always {
    $cliphist_store
    $cliphist_watch
}

# RELIABLE — use standalone lines
exec_always $cliphist_store
exec_always $cliphist_watch
```

**Practical rule:** Move every daemon-launching `exec_always` out of blocks and onto its own standalone line.

---

## Reliable daemon management pattern

The full three-step pattern for daemons that must restart on `swaymsg reload`:

### Step 1 — Create a dedicated script

```sh
#!/bin/sh
# ~/.config/sway/scripts/my-daemon.sh
#
# Restarts my-daemon cleanly on sway reload.
# Use $HOME paths — never dirname "$0" (sway sets $0 to "sh").

# Kill any existing instance.
# Use ^ anchor to avoid matching this sh process itself.
pkill -f "^my-daemon" 2>/dev/null

# exec replaces this shell with the daemon.
# The daemon becomes a direct child of sway (cleaner process tree).
exec my-daemon --config "$HOME/.config/my-daemon/config.toml"
```

Why `exec` at the end? `exec cmd` replaces the current shell process with `cmd` instead of forking a child. The daemon becomes a direct child of sway rather than a grandchild through a lingering sh process. This gives a cleaner process tree and ensures sway correctly tracks the daemon's lifetime.

### Step 2 — Set a variable with the absolute script path

```sway
# In 01-definitions.conf or equivalent
set $my_daemon '/home/milo/.config/sway/scripts/my-daemon.sh'
```

Use single quotes and an absolute path. Do not use `~` (prefer the explicit path or `$HOME` inside the script itself).

### Step 3 — Launch with standalone exec_always

```sway
# In 99-autostart.conf
exec_always $my_daemon
```

Not inside a block. One line per daemon.

### Complete script template

```sh
#!/bin/sh
# ~/.config/sway/scripts/daemon-template.sh
#
# Template for a sway-managed daemon.
# Called by: exec_always $daemon_var  (standalone, not in block)
#
# IMPORTANT: $0 is "sh" in sway exec context. Never use dirname "$0".
# Always use $HOME or absolute paths for file references.

# Kill any previous instance.
# The ^ anchor prevents pkill from matching this sh -c '...' process,
# whose argv includes the daemon name as a substring.
pkill -f "^daemon-binary-name" 2>/dev/null

# Optional: wait briefly for the old instance to die
# (only needed if the daemon holds exclusive resources)
# until ! pgrep -f "^daemon-binary-name" >/dev/null; do sleep 0.1; done

# Replace this shell with the daemon process.
exec daemon-binary-name \
    --config "$HOME/.config/daemon/config.toml" \
    --log-file "/tmp/daemon.log"
```

---

## exec flags

### --no-startup-id

```sway
exec --no-startup-id firefox
exec_always --no-startup-id $my_daemon
```

By default, sway sends a startup notification sequence when launching applications. This causes a loading cursor to appear. Applications that support the startup notification protocol send a message back when they are ready, clearing the cursor.

Applications that do NOT support startup notifications (most daemons, command-line tools, and some GUI apps) never send the "ready" signal, leaving the loading cursor visible until it times out.

`--no-startup-id` suppresses the startup notification entirely, preventing the cursor from showing at all.

**Use `--no-startup-id` for:**
- Background daemons (clipboard managers, notification daemons, kanshi, etc.)
- Command-line tools
- Applications known not to support startup notification

**Omit it for:**
- GUI applications that do support startup notification (most GTK/Qt apps)

```sway
# Daemon — suppress startup notification
exec_always --no-startup-id $cliphist_store
exec_always --no-startup-id $kanshi

# GUI app — let startup notification work
exec firefox
exec foot
```

---

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
