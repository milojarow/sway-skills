---
name: sway-config
description: Core sway configuration syntax, file structure, variable system, and include directives. Use when writing or editing sway config, understanding config file structure, using the set command for variables, organizing config with include, understanding command conventions, working with exec/exec_always, or troubleshooting config reload issues.
---
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

Block syntax is convenient for `output`, `input`, `bar`, and `mode` definitions. However, **do not use blocks for exec_always with daemons** — see EXEC_DAEMON.md.

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

**However:** complex compound commands that launch blocking daemons are unreliable inside `exec_always {}` blocks. See EXEC_DAEMON.md.

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

See EXEC_DAEMON.md for the complete reliable daemon management pattern.

### Reload workflow
```bash
# Edit config
vim ~/.config/sway/config.d/20-keybindings.conf

# Reload without restarting sway
swaymsg reload

# Check for errors — swaynag will display them if any
```

---

## Reference Files

- **EXEC_DAEMON.md** — detailed coverage of exec vs exec_always semantics, how sway spawns processes, why exec_always blocks are unreliable for daemons, and the complete reliable daemon management pattern with script template
- **GOTCHAS.md** — 10 non-obvious runtime behaviors discovered from real debugging: dirname $0, pkill self-matching, PATH restrictions, tilde expansion, pgrep ERE syntax, variable quoting, include order, and more
