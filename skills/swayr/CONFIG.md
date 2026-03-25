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
