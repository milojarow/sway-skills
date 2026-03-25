---
name: swayr
description: "Window switcher and MRU (most-recently-used) manager for sway. Use when switching between windows in MRU order, switching to urgent windows first, switching workspaces, moving windows or workspaces, running fuzzy-search window switchers, setting up swayrd daemon, or binding swayr commands to sway keybindings."
---
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
