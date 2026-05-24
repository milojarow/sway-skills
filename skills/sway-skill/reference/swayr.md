# swayr


Swayr is a window-switcher and MRU (most-recently-used) manager for the sway Wayland compositor. It consists of a daemon (`swayrd`) that tracks window focus history and a client (`swayr`) that exposes commands for switching, moving, tiling, and quitting windows and workspaces. A companion status bar, `swayrbar`, implements the swaybar-protocol for use with sway's built-in bar. Note on terminology: commands use `lru` in their names but this always means most-recently-used (MRU), not least-recently-used — a naming quirk from the project's early days.

---

## Architecture

Swayr uses a daemon/client model over sway's JSON IPC interface:

- **`swayrd`** (daemon): runs continuously, listens to sway IPC events (window/workspace creation, deletion, focus changes), and maintains MRU order. All state lives here.
- **`swayr`** (client): sends subcommands to the daemon, which executes them. The client is stateless — it just issues requests.
- Communication is over the same sway IPC socket that `swaymsg` uses.

Because the daemon tracks focus history, swayr can present windows in true MRU order — something sway itself does not expose.

---

## Setup

### Starting swayrd

**Option 1: systemd user service** (recommended)

A unit file ships with the package at `/usr/lib/systemd/user/swayrd.service` (or `/usr/share/swayr/swayrd.service`). It is `PartOf=sway-session.target` so it starts and stops with sway:

```ini
[Unit]
Description=Window switcher for Sway
PartOf=sway-session.target
After=sway-session.target

[Service]
Type=simple
ExecStart=/usr/bin/swayrd
Restart=on-failure

[Install]
WantedBy=sway-session.target
```

Enable it once:
```sh
systemctl --user enable --now swayrd.service
```

**Option 2: exec in sway config**

```
exec env RUST_BACKTRACE=1 RUST_LOG=swayr=debug swayrd > /tmp/swayrd.log 2>&1
```

The `RUST_LOG` and log redirect are optional but useful for debugging.

### Breaking out of cycling sequences

The LRU order is frozen while a cycling sequence (e.g. repeated `switch-to-urgent-or-lru-window`) is in progress. Two ways to end a sequence:

1. **Key release binding** (requires unreleased sway PR #6920):
   ```
   bindsym --release Super_L exec swayr nop
   ```
2. **`auto_nop_delay`** in config: swayr automatically sends `nop` after the configured milliseconds of inactivity.

---

## Key Commands

### `switch-to-urgent-or-lru-window`
The workhorse Alt+Tab replacement. Cycles through windows in this order:
1. All windows with urgency hints
2. Most-recently-used window at sequence start
3. Back to the origin window

Use with a key that you hold and repeat (e.g. `Mod1+Tab`). The sequence freezes MRU order until a non-cycling command is received.

Flags: `--skip-urgent`, `--skip-lru`, `--skip-origin` to suppress individual steps.

### `switch-window`
Opens the configured menu program (wofi, fuzzel, rofi, etc.) showing all windows sorted by urgency first, then MRU order, with the currently focused window last. Selecting a window focuses it.

### `switch-workspace-or-window`
Menu showing all workspaces and their windows. Selecting a workspace switches to it; selecting a window focuses it. Good for an overview/jump-to shortcut.

### `switch-workspace`
Menu showing all workspaces in MRU order. Selecting one switches to it.

### `switch-to-app-or-urgent-or-lru-window <name>`
Non-menu command: cycles through windows matching `<name>` (matched against `app_id` for Wayland, class/instance for X11), then urgent windows, then the LRU window. Exits non-zero if no matching window exists — useful for "focus or launch" patterns:

```sh
bindsym $mod+e exec \
    swayr switch-to-app-or-urgent-or-lru-window \
          --skip-lru-if-current-doesnt-match emacs \
    || emacs
```

### `move-focused-to-workspace`
Menu showing workspaces; moves the currently focused window or container to the selected one. Non-matching input of the form `#w:<workspace>` creates a new workspace.

### `quit-window`
Menu showing all windows; quits the selected one via sway IPC `kill`. Add `--kill` / `-k` to send `kill -9 <pid>` instead.

### `quit-workspace-windows` / `quit-workspace-or-window`
Menu showing workspaces and windows; can quit all windows of a workspace or a single window.

### `tile-workspace exclude-floating|include-floating`
Re-tiles all windows on the current workspace: moves them to a scratch workspace, sets the current workspace to `splith`, then re-inserts them. Works with `auto_tile` to produce balanced layouts.

### `shuffle-tile-workspace exclude-floating|include-floating`
Like `tile-workspace` but shuffles window order and randomly focuses inserted windows during re-insertion, producing more balanced layouts when used with `auto_tile`.

### Other commands

| Command | Description |
|---|---|
| `switch-to-mark-or-urgent-or-lru-window <mark>` | Non-menu: cycle to window with given sway mark |
| `switch-to-matching-or-urgent-or-lru-window <criteria>` | Non-menu: cycle to windows matching criteria query |
| `steal-window` | Menu: move a window from any workspace into the current one |
| `swap-focused-with` | Menu: swap focused window with selected window |
| `switch-output` | Menu: focus a selected output |
| `next-window / prev-window all-workspaces\|current-workspace` | Cycle windows in tree order |
| `next-tiled-window / prev-tiled-window` | Cycle only tiled windows |
| `next-floating-window / prev-floating-window` | Cycle only floating windows |
| `next-window-of-same-layout / prev-window-of-same-layout` | Cycle windows of same layout type as current |
| `tab-workspace exclude-floating\|include-floating` | Put all workspace windows in a tabbed container |
| `configure-outputs` | Repeatedly issue output configuration commands via menu |
| `execute-swaymsg-command` | Menu: run swaymsg commands without remembering syntax |
| `execute-swayr-command` | Menu: run any swayr command without a keybinding |
| `nop` | Does nothing; used to break out of cycling sequences |
| `get-windows-as-json` | Scripting: output all windows as JSON |
| `for-each-window <criteria> <cmd>` | Scripting: run shell command for each matching window |
| `print-config` | Print current config to stdout |
| `reload-config` | Reload config from disk |

---

## Sway Config Integration

Complete example of recommended keybindings:

```
# Start the daemon
exec env RUST_BACKTRACE=1 RUST_LOG=swayr=debug swayrd > /tmp/swayrd.log 2>&1

# MRU window cycling (Alt+Tab style)
bindsym Mod1+Tab         exec swayr switch-to-urgent-or-lru-window

# Fuzzy window/workspace switchers
bindsym $mod+Space       exec swayr switch-window
bindsym $mod+Shift+Space exec swayr switch-workspace-or-window

# Quit a window via menu
bindsym $mod+Delete      exec swayr quit-window

# Cycle windows in order
bindsym $mod+Next        exec swayr next-window all-workspaces
bindsym $mod+Prior       exec swayr prev-window all-workspaces

# Execute swaymsg/swayr commands via menu (useful for infrequent commands)
bindsym $mod+c           exec swayr execute-swaymsg-command
bindsym $mod+Shift+c     exec swayr execute-swayr-command

# Break out of a cycling sequence on modifier release (requires sway PR #6920)
bindsym --release Super_L exec swayr nop

# Focus-or-launch shortcuts
bindsym $mod+e exec swayr switch-to-app-or-urgent-or-lru-window \
                     --skip-lru-if-current-doesnt-match emacs || emacs
bindsym $mod+b exec swayr switch-to-app-or-urgent-or-lru-window \
                     --skip-lru-if-current-doesnt-match firefoxdeveloperedition \
               || firefox-developer-edition
```

---

## Configuration

Config file: `~/.config/swayr/config.toml` (falls back to `/etc/xdg/swayr/config.toml`).

On first run, swayr creates a default config for wofi. Print the default at any time:
```sh
swayr print-default-config
```

### [menu] section

```toml
[menu]
executable = 'wofi'
args = [
    '--show=dmenu',
    '--define=layer=overlay',
    '--allow-markup',
    '--allow-images',
    '--insensitive',
    '--cache-file=/dev/null',
    '--parse-search',
    '--height=40%',
    '--prompt={prompt}',   # {prompt} is replaced with context-specific text
]
```

Any program that reads items from stdin and writes the selection to stdout works. The `{prompt}` placeholder in args is replaced by a context-sensitive string like "Switch to window".

### [format] section

Controls how windows, workspaces, containers, and outputs appear in the menu. Supports pango markup (for wofi). Key options:

```toml
[format]
window_format = 'img:{app_icon}:text:{indent}<i>{app_name}</i> — {urgency_start}<b>"{title}"</b>{urgency_end} on workspace {workspace_name} <i>{marks}</i>    <span alpha="20000">({id})</span>'
workspace_format = '{indent}<b>Workspace {name} [{layout}]</b>    <span alpha="20000">({id})</span>'
container_format = '{indent}<b>Container [{layout}]</b> on workspace {workspace_name} <i>{marks}</i>    <span alpha="20000">({id})</span>'
output_format = '{indent}<b>Output {name}</b>    <span alpha="20000">({id})</span>'
indent = '    '
urgency_start = '<span background="darkred" foreground="yellow">'
urgency_end = '</span>'
html_escape = true
icon_dirs = [
    '/usr/share/icons/hicolor/scalable/apps',
    '/usr/share/icons/hicolor/64x64/apps',
    '/usr/share/icons/hicolor/48x48/apps',
    '/usr/share/pixmaps',
]
# fallback_icon = '/path/to/fallback.png'
```

- **wofi icons**: `window_format` must start with `img:{app_icon}:text:` for icons to render.
- **rofi icons**: `window_format` must end with `"\u0000icon\u001f{app_icon}"` (use double-quoted TOML string).
- **fuzzel**: same icon syntax as rofi.
- Always include `{id}` in window/container formats to ensure uniqueness.

### [layout] section

```toml
[layout]
auto_tile = false
auto_tile_min_window_width_per_output_width = [
    [1920, 920],   # on a 1920px-wide output, min window width is 920px
    [2560, 1000],
    # ...
]
```

When `auto_tile = true`, swayrd automatically calls `split vertical` or `split horizontal` on windows to prevent them from becoming narrower than the configured minimum. Triggered by new-window, close, move, floating, and focus events.

### [focus] section

```toml
[focus]
lockin_delay = 750   # milliseconds a window must hold focus to update MRU order
```

Prevents brief mouse-over focus changes (with `focus_follows_mouse`) from disrupting MRU order.

### [misc] section

```toml
[misc]
auto_nop_delay = 3000   # ms after last swayr command before automatic nop is sent
seq_inhibit = false      # if true, inhibit MRU updates during cycling sequences
```

- `auto_nop_delay`: set this if you cannot use the `--release` binding to break sequences.
- `seq_inhibit = true`: pairs well with the key-release `nop` binding to prevent intermediate windows from polluting MRU order during cycling.

### [swaymsg_commands] section

```toml
[swaymsg_commands]
include_predefined = true   # include swayr's built-in swaymsg command list

[swaymsg_commands.commands]
"Window to workspace XXX" = "move window to workspace XXX"
"Workspace to left output" = "move workspace to output left"
"Workspace to right output" = "move workspace to output right"
```

Defines custom entries for `execute-swaymsg-command`.

---

# swayr Command Reference

> Note: commands with `lru` in their name mean MRU (most-recently-used), not least-recently-used. This is a naming quirk from the project's early development.

---

## Non-Menu Switchers

These commands cycle through a sequence of windows without opening a menu. The sequence order is:
1. All windows with urgency hints
2. Matching windows (command-specific)
3. The most-recently-used window at sequence start
4. Back to the origin window (window focused when the sequence began)

No window is visited twice across all steps. Steps 1, 3, and 4 can be suppressed with flags.

**Common flags for all non-menu switchers:**
- `--skip-urgent` — skip step 1 (urgent windows)
- `--skip-lru` — skip step 3 (MRU window)
- `--skip-origin` — skip step 4 (return to origin)
- `--skip-lru-if-current-doesnt-match` — skip MRU window only if the currently focused window does not match the command's criteria

### `switch-to-urgent-or-lru-window`
Cycles to urgent windows first, then the MRU window, then back to origin. Step 2 (matching windows) is disabled — this is the purest MRU switcher. Ideal for Alt+Tab.

### `switch-to-app-or-urgent-or-lru-window <name>`
Cycles through windows matching `<name>`, then urgent windows, then MRU. `<name>` is matched literally against `app_id` (Wayland) or `class`/`instance` (X11). Exits non-zero if no matching window exists, enabling "focus or launch" shell idioms:
```sh
swayr switch-to-app-or-urgent-or-lru-window --skip-lru-if-current-doesnt-match firefox || firefox
```

### `switch-to-mark-or-urgent-or-lru-window <con_mark>`
Cycles to the window carrying `<con_mark>`. Since sway marks are unique per window, this effectively jumps to a specific named window. Exits non-zero if no window has the mark.

### `switch-to-matching-or-urgent-or-lru-window <criteria>`
Cycles through windows matching a criteria query (see Criteria section below), then urgent, then MRU. Exits non-zero if no window matches.

---

## Menu Switchers

These commands open the configured menu program and act on the selection.

### `switch-window`
Shows all windows sorted: urgent first, then MRU order, focused window last. Focusing the selected window.

### `steal-window`
Shows all windows (same order as `switch-window`). Moves the selected window into the current workspace.

### `steal-window-or-container`
Shows all windows and containers. Moves the selected window or container into the current workspace.

### `switch-workspace`
Shows all workspaces in MRU order. Switches to the selected workspace.

### `switch-output`
Shows all outputs (monitors). Focuses the selected output.

### `switch-workspace-or-window`
Shows all workspaces and their windows in a tree structure. Switches to the selected workspace or focuses the selected window.

### `switch-workspace-container-or-window`
Shows workspaces, containers, and windows. Switches to or focuses the selected item.

### `switch-to`
Shows outputs, workspaces, containers, and windows. Switches to or focuses the selected item.

### `quit-window`
Shows all windows. Quits the selected window via sway IPC `kill`.
- `--kill` / `-k` — uses `kill -9 <pid>` instead of the IPC kill message.

### `quit-workspace-or-window`
Shows workspaces and their windows. Quits all windows of the selected workspace, or just the selected window.

### `quit-workspace-container-or-window`
Shows workspaces, containers, and windows. Quits all windows of the selected workspace/container, or the selected window.

### `move-focused-to-workspace`
Shows workspaces. Moves the currently focused window or container to the selected workspace.

Non-matching input creates a new workspace. Supported formats:
- `w:<workspace>` — switch to (or create) workspace by digit, name, or `<digit>:<name>`
- `s:<cmd>` — execute a sway command via swaymsg
- Anything else is treated as a workspace name (`w:<input>`)
- Prefix with `#` to force non-match treatment

### `move-focused-to`
Shows outputs, workspaces, containers, and windows. Moves the currently focused container or window to the selected target. Non-matching input handled same as `move-focused-to-workspace`.

### `swap-focused-with`
Shows all windows and containers. Swaps the currently focused window or container with the selected one.

---

## Cycling Commands

These cycle through windows in tree iteration order (not MRU order). The MRU order is frozen during a cycle sequence and resumes when a non-cycling command is received.

### `next-window all-workspaces|current-workspace`
Focus the next window in depth-first tree order. Argument controls scope.

### `prev-window all-workspaces|current-workspace`
Focus the previous window in depth-first tree order.

### `next-tiled-window` / `prev-tiled-window`
Cycle only windows in tiled containers.

### `next-tabbed-or-stacked-window` / `prev-tabbed-or-stacked-window`
Cycle only windows in tabbed or stacked containers.

### `next-floating-window` / `prev-floating-window`
Cycle only floating windows.

### `next-window-of-same-layout` / `prev-window-of-same-layout`
Cycles windows of the same layout type as the current window:
- Floating current → cycles floating
- Tabbed/stacked current → cycles tabbed/stacked
- Tiled current → cycles tiled
- Otherwise → cycles all windows

### `next-matching-window <criteria>` / `prev-matching-window <criteria>`
Cycle only windows matching the given criteria query.

---

## Layout Modification Commands

### `tile-workspace exclude-floating|include-floating`
Re-tiles all windows on the current workspace. Process: moves all windows to a scratch workspace, sets current workspace to `splith`, re-inserts windows. Works with `auto_tile` to produce balanced layouts.

### `shuffle-tile-workspace exclude-floating|include-floating`
Like `tile-workspace` but shuffles window order before re-insertion and randomly focuses already-inserted windows during insertion. Produces more balanced layouts with `auto_tile` (e.g., 2+4 split instead of 1+4).

### `tab-workspace exclude-floating|include-floating`
Puts all windows of the current workspace into a tabbed container.

### `toggle-tab-shuffle-tile-workspace exclude-floating|include-floating`
Toggles between tabbed and tiled layout. Calls `shuffle-tile-workspace` if currently tabbed, and `tab-workspace` if currently tiled.

---

## Scripting Commands

### `get-windows-as-json`
Returns a JSON array of all windows.
- `--include-scratchpad` — include scratchpad windows
- `--matching <CRITERIA>` — restrict to matching windows
- `--error-if-no-match` — exit non-zero if no windows match (makes it suitable for `if` checks in scripts)

### `for-each-window <CRITERIA> <SHELL_COMMAND>`
Executes `<SHELL_COMMAND>` for each window matching `<CRITERIA>`. Format placeholders (e.g. `{app_name}`, `{pid}`) are substituted in the command. Commands run in parallel and must complete within 2 seconds. Returns a JSON array with exit code, stdout, stderr, and error for each execution.

Example:
```sh
swayr for-each-window true echo "App {app_name} has PID {pid}."
```

---

## Miscellaneous Commands

### `configure-outputs`
Repeatedly prompts for output configuration commands via the menu until aborted. Useful for ad-hoc monitor setup.

### `execute-swaymsg-command`
Shows most common swaymsg commands (that need no additional input) and executes the selected one. Non-matching input is passed directly to swaymsg. Custom commands can be added via `[swaymsg_commands]` in config.

### `execute-swayr-command`
Shows all swayr commands in the menu and executes the selected one. Useful for commands without keybindings.

### `nop`
Does nothing. Used to explicitly break out of a non-menu switching sequence or cycling sequence without side effects.

### `print-config`
Prints the current active config in TOML format to stdout.

### `print-default-config`
Prints the built-in default config (the one generated on first run) in TOML format to stdout.

### `merge-config <FILE>`
Reads config from `<FILE>` and merges it with the current config. Options in `<FILE>` override current options; unspecified options are unchanged. Useful for temporary alternate configs:
```sh
swayr merge-config ~/.config/swayr/alt.toml; swayr switch-window; swayr reload-config
```

### `reload-config`
Reloads config from the standard config file (`~/.config/swayr/config.toml`), discarding any merges or in-memory changes.

---

## Criteria Queries

Used by `switch-to-matching-or-urgent-or-lru-window`, `next-matching-window`, `get-windows-as-json`, `for-each-window`, and others.

### Simple criteria (compatible with sway's `[criteria]` syntax)

| Criterion | Description |
|---|---|
| `app_id=<regex\|__focused__>` | Match Wayland app ID |
| `class=<regex\|__focused__>` | Match X11 window class |
| `instance=<regex\|__focused__>` | Match X11 window instance |
| `title=<regex\|__focused__>` | Match window title |
| `workspace=<regex\|__focused__\|__visible__>` | Match workspace |
| `con_mark=<regex>` | Match container mark |
| `con_id=<uint\|__focused__>` | Match container ID |
| `shell=<"xdg_shell"\|"xwayland"\|__focused__>` | Match shell type |
| `pid=<uint>` | Match process ID |
| `floating` | Match floating windows |
| `tiling` | Match tiled windows |
| `app_name=<regex\|__focused__>` | Match app_id OR class OR instance (swayr extension) |

All regex values use Rust's `regex` crate syntax. `__focused__` performs a literal match against the focused window's value.

### Compound criteria

```
[and <crit1> <crit2> ...]   # all must match (and is optional)
[or <crit1> <crit2> ...]    # any must match
not <crit>                   # negate a criterion
```

Combinators can be `AND`/`OR`/`NOT` or `&&`/`||`/`!`. Criteria can be nested:
```
[|| [app_id="firefox" tiling]
    [&& !app_id="firefox" floating workspace=__focused__]]
```

Boolean literals `true` and `false` (or `TRUE`/`FALSE`) are also valid criteria.

---

# swayr Configuration Reference

## File Location

User config: `~/.config/swayr/config.toml`
System-wide fallback: `/etc/xdg/swayr/config.toml`

On first run, if no config file exists, swayr creates a default config at `~/.config/swayr/config.toml` configured for wofi.

Print the current active config:
```sh
swayr print-config
```

Print the built-in default config:
```sh
swayr print-default-config
```

Apply a temporary override config and revert:
```sh
swayr merge-config ~/.config/swayr/alt.toml
swayr <command>
swayr reload-config
```

---

## Full Default Config

```toml
[menu]
executable = 'wofi'
args = [
    '--show=dmenu',
    '--define=layer=overlay',
    '--allow-markup',
    '--allow-images',
    '--insensitive',
    '--cache-file=/dev/null',
    '--parse-search',
    '--height=40%',
    '--prompt={prompt}',
]

[format]
output_format = '{indent}<b>Output {name}</b>    <span alpha="20000">({id})</span>'
workspace_format = '{indent}<b>Workspace {name} [{layout}]</b>    <span alpha="20000">({id})</span>'
container_format = '{indent}<b>Container [{layout}]</b> on workspace {workspace_name} <i>{marks}</i>    <span alpha="20000">({id})</span>'
window_format = 'img:{app_icon}:text:{indent}<i>{app_name}</i> — {urgency_start}<b>"{title}"</b>{urgency_end} on workspace {workspace_name} <i>{marks}</i>    <span alpha="20000">({id})</span>'
indent = '    '
urgency_start = '<span background="darkred" foreground="yellow">'
urgency_end = '</span>'
html_escape = true
icon_dirs = [
    '/usr/share/icons/hicolor/scalable/apps',
    '/usr/share/icons/hicolor/64x64/apps',
    '/usr/share/icons/hicolor/48x48/apps',
    '/usr/share/icons/Adwaita/64x64/apps',
    '/usr/share/icons/Adwaita/48x48/apps',
    '/usr/share/pixmaps',
]

[layout]
auto_tile = false
auto_tile_min_window_width_per_output_width = [
    [1024, 500],
    [1280, 600],
    [1400, 680],
    [1440, 700],
    [1600, 780],
    [1920, 920],
    [2560, 1000],
    [3440, 1000],
    [4096, 1200],
]

[focus]
lockin_delay = 750

[misc]
auto_nop_delay = 3000
seq_inhibit = false

[swaymsg_commands]
include_predefined = true
[swaymsg_commands.commands]
"Window to workspace XXX" = "move window to workspace XXX"
"Workspace to left output" = "move workspace to output left"
"Workspace to right output" = "move workspace to output right"
```

---

## [menu] Section

Controls which program is used for fuzzy selection.

| Option | Type | Description |
|---|---|---|
| `executable` | string | Name or full path of the menu program |
| `args` | array of strings | Arguments passed to the program |

The `{prompt}` placeholder in any arg is replaced by a context-sensitive string (e.g. "Switch to window", "Switch to workspace").

**Requirements for menu programs:** must read items from stdin (one per line) and write the selected item to stdout.

### Adapting for other menu programs

**fuzzel:**
```toml
[menu]
executable = 'fuzzel'
args = ['--dmenu', '--prompt={prompt}: ']
```

**rofi:**
```toml
[menu]
executable = 'rofi'
args = ['-dmenu', '-p', '{prompt}', '-i']
```

**bemenu:**
```toml
[menu]
executable = 'bemenu'
args = ['-i', '-p', '{prompt}']
```

**fzf (in a terminal):**
```toml
[menu]
executable = 'foot'
args = ['fzf', '--prompt={prompt}: ']
```

---

## [format] Section

Controls how items appear in the menu. Supports [pango markup](https://docs.gtk.org/Pango/pango_markup.html) (HTML-like tags) when the menu program supports it (wofi does).

### Format strings

| Option | Default purpose |
|---|---|
| `output_format` | How monitor outputs are displayed |
| `workspace_format` | How workspaces are displayed |
| `container_format` | How non-workspace containers are displayed |
| `window_format` | How application windows are displayed |

### Placeholders

| Placeholder | Available in | Description |
|---|---|---|
| `{name}` | all | Output name, workspace number/name, or window title (`{title}` is a deprecated synonym) |
| `{id}` | all | sway-internal container ID (guarantees uniqueness) |
| `{layout}` | workspace, container | Layout type (splith, splitv, tabbed, stacked) |
| `{indent}` | all | Repeated `format.indent` string, N times for depth N |
| `{pid}` | window | Process ID |
| `{app_name}` | window, container | Application name (app_id or X11 class/instance) |
| `{marks}` | window, container | Comma-separated list of sway marks |
| `{app_icon}` | window | Path to application icon PNG/SVG |
| `{workspace_name}` | window, container | Name/number of containing workspace |
| `{urgency_start}` | window | Replaced by `format.urgency_start` if urgent, else empty string |
| `{urgency_end}` | window | Replaced by `format.urgency_end` if urgent, else empty string |

### Placeholder formatting

Placeholders (except `{app_icon}`, `{indent}`, `{urgency_start}`, `{urgency_end}`) support Rust's `std::fmt` format strings:

```
{<placeholder>:<fmt_str><clipped_str>}
```

Examples:
- `{app_name:{:>10.10}}` — right-align, exactly 10 chars (pad or cut)
- `{app_name:{:.10}...}` — truncate at 10 chars, append `...` if cut
- `{title:{:<30.30}}` — left-align, exactly 30 chars

### Other format options

| Option | Type | Default | Description |
|---|---|---|---|
| `indent` | string | `'    '` | String used at `{indent}` placeholder per depth level |
| `html_escape` | bool | `true` | HTML-escape `<`, `>`, `&` in placeholder values (except urgency) |
| `urgency_start` | string | pango red span | Replaces `{urgency_start}` for urgent windows |
| `urgency_end` | string | `</span>` | Replaces `{urgency_end}` for urgent windows |
| `icon_dirs` | array of strings | system icon paths | Directories searched for `{app_icon}` |
| `fallback_icon` | string | (none) | Path to PNG/SVG used when no app icon is found |

### Icon syntax by menu program

**wofi** — start `window_format` with `img:{app_icon}:text:`:
```toml
window_format = 'img:{app_icon}:text:{app_name} — {title}'
```

**rofi / fuzzel** — end `window_format` with the null-separator syntax (requires double-quoted TOML string for escape sequences):
```toml
window_format = "{app_name} — {title}\u0000icon\u001f{app_icon}"
```

Note: rofi/fuzzel require double-quoted strings in TOML (single-quoted strings are literal and do not process `\uXXXX` escapes).

---

## [layout] Section

Controls automatic tiling behavior.

| Option | Type | Default | Description |
|---|---|---|---|
| `auto_tile` | bool | `false` | Enable automatic split direction management |
| `auto_tile_min_window_width_per_output_width` | array of `[output_width, min_window_width]` | see default config | Per-output-width minimum window width in pixels |

### How auto_tile works

When enabled, swayrd monitors window events and automatically issues `split vertical` or `split horizontal` sway commands:
- If a horizontal container would make a child window narrower than the minimum: `split vertical`
- If a vertical container has enough space for another window above minimum width: `split horizontal`
- Stacked/tabbed containers are never affected.

**Important:** `auto_tile_min_window_width_per_output_width` must include your exact monitor width. If your output width is not in the list, auto-tiling will not activate for that output. Include borders and gaps in your width calculations.

---

## [focus] Section

| Option | Type | Default | Description |
|---|---|---|---|
| `lockin_delay` | integer (ms) | `750` | Milliseconds a window must hold focus before its MRU position is updated |

With `focus_follows_mouse = yes` in sway, briefly mousing over a window could pollute MRU order. `lockin_delay` prevents transient focus changes (shorter than this threshold) from affecting the order.

---

## [misc] Section

| Option | Type | Default | Description |
|---|---|---|---|
| `auto_nop_delay` | integer (ms) | (unset = disabled) | After this many ms of no swayr commands, automatically send `nop` to end a cycling sequence |
| `seq_inhibit` | bool | `false` | If true, inhibit MRU updates during cycling sequences |

### auto_nop_delay

Each new swayr command resets the timer. Use this when you cannot bind `nop` to the modifier key release. Set to e.g. `3000` (3 seconds).

If not specified in config, no automatic nop is sent.

### seq_inhibit

- `false` (default): focus events are always processed normally, even during a cycling sequence.
- `true`: MRU order updates are paused during a cycling sequence; they resume when a non-cycling command (like `nop`) is received. Also suppresses MRU updates for focus changes made outside swayr during the sequence. Best used with the `--release` nop binding.

---

## [swaymsg_commands] Section

Configures the command list shown by `execute-swaymsg-command`.

| Option | Type | Default | Description |
|---|---|---|---|
| `include_predefined` | bool | `true` | Include swayr's built-in list of common swaymsg commands |

```toml
[swaymsg_commands.commands]
"<label shown in menu>" = "<swaymsg command to execute>"
```

Labels (keys) must be unique within the map. Example:
```toml
[swaymsg_commands.commands]
"Window to workspace 1" = "move window to workspace 1"
"Toggle floating" = "floating toggle"
"Workspace to left output" = "move workspace to output left"
"Workspace to right output" = "move workspace to output right"
```

---

## swayrbar Configuration

swayrbar is a separate binary with its own config at `~/.config/swayrbar/config.toml`.

### Top-level options

| Option | Type | Default | Description |
|---|---|---|---|
| `refresh_interval` | integer (ms) | 1000 | How often swaybar is refreshed |

### Module definition

Modules are defined as an array of tables:

```toml
[[modules]]
name = 'window'        # module type
instance = '0'         # arbitrary string to distinguish duplicate module types
format = '{app_name} — {title}'
html_escape = false

[modules.on_click]
Left = ['swayr', 'switch-to-urgent-or-lru-window']
Right = ['kill', '{pid}']
Middle = ['foot']
WheelUp = ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+5%']
WheelDown = ['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%']
```

**on_click** buttons: `Left`, `Middle`, `Right`, `WheelUp`, `WheelDown`, `WheelLeft`, `WheelRight`.

### Available modules and their placeholders

| Module | Placeholders | Notes |
|---|---|---|
| `window` | `{title}` / `{name}`, `{app_name}`, `{pid}` | Also reacts to title changes on non-focused windows |
| `sysinfo` | `{cpu_usage}`, `{mem_usage}`, `{load_avg_1}`, `{load_avg_5}`, `{load_avg_15}` | |
| `battery` | `{state_of_charge}`, `{state_of_health}`, `{state}` | |
| `date` | `format` uses chrono strftime specifiers | |
| `pactl` | `{volume}`, `{muted}`, `{volume_source}`, `{muted_source}` | Requires PulseAudio or PipeWire+pipewire-pulse |
| `wpctl` | `{volume}`, `{muted}`, `{volume_source}`, `{muted_source}` | Requires PipeWire |
| `nmcli` | `{name}`, `{signal}`, `{bars}` | Requires NetworkManager |
| `iwctl` | `{name}`, `{signal}` (dBm), `{bars}` | Requires iwd |
| `cmd` | (none — `format` is the shell command) | Runs via `sh -c`, displays stdout |
| `mpd` | `{song}`, `{cycling_song}`, `{elapsed}`, `{queue_len}`, `{volume}` | Requires mpd+mpc |
| `wttr.in` | `format` is the wttr.in URL path | Fetches weather every 30 min |
| `ppd` | `{profile}`, `{profile_icon}` | Requires power-profiles-daemon |

### swayrbar sway config setup

```conf
bar {
    swaybar_command swaybar
    status_command env RUST_BACKTRACE=1 RUST_LOG=swayr=debug swayrbar 2> /tmp/swayrbar.log
    position top
    font pango:Iosevka 11
    height 20

    colors {
        statusline #f8c500
        background #33333390
    }
}
```

Note: redirect only stderr (`2>`), not stdout — swaybar reads the swaybar JSON protocol from stdout.
