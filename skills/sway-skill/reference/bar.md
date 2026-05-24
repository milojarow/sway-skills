# Swaybar Configuration and JSON Status Protocol


Swaybar is the built-in status bar for sway. It is configured inside the sway config file using a `bar { ... }` block. The bar can run an external command to populate its right-side status area — either as plain text (one line per update) or using the i3bar-compatible JSON protocol for rich, per-block styling and click handling. This skill covers the full configuration surface and the complete JSON protocol.

---

## Bar Configuration Block

Named bars use `bar <id> { ... }`. Unnamed bars use `bar { ... }` and get an auto-assigned id (typically `bar-0`).

```
bar {
    id main
    position top
    status_command ~/.scripts/status.sh
    font pango:JetBrainsMono Nerd Font 11
    height 28

    colors {
        background #1e1e2e
        statusline #cdd6f4
        separator  #6c7086

        focused_workspace  #89b4fa #89b4fa #1e1e2e
        active_workspace   #313244 #313244 #cdd6f4
        inactive_workspace #1e1e2e #1e1e2e #6c7086
        urgent_workspace   #f38ba8 #f38ba8 #1e1e2e
    }
}
```

---

## Essential Settings Quick Reference

| Setting | Values | Default | Notes |
|---|---|---|---|
| `id` | `<name>` | auto | Used to target bar with IPC |
| `position` | `top\|bottom` | `bottom` | |
| `mode` | `dock\|hide\|invisible\|overlay` | `dock` | See Bar Modes below |
| `hidden_state` | `show\|hide` | `hide` | Only relevant in `hide` mode |
| `modifier` | `<Modifier>\|none` | `Mod4` | Key that reveals a hidden bar |
| `font` | pango font description | system | e.g. `pango:JetBrainsMono 11` |
| `height` | `<px>` | `0` (auto) | 0 matches font size |
| `status_command` | `<cmd>` | none | Run with `sh -c` |
| `tray_output` | `none\|all\|<output>` | all | Where to show tray icons |
| `tray_padding` | `<px>` | `2` | Padding around/between icons |
| `icon_theme` | `<name>` | hicolor | Icon theme for tray |
| `workspace_buttons` | `yes\|no` | `yes` | Show workspace buttons |
| `binding_mode_indicator` | `yes\|no` | `yes` | Show active binding mode |
| `wrap_scroll` | `yes\|no` | `no` | Scroll through workspaces cyclically |

---

## Bar Modes

**dock** (default) — bar is always visible at the screen edge, takes up space.

**hide** — bar is normally hidden. It appears when the `modifier` key is held, or when any window has an urgency hint. Its default visibility while hidden is controlled by `hidden_state`:
- `hidden_state hide` — stays hidden until modifier is pressed (the default)
- `hidden_state show` — stays visible, drawn on top of windows (like overlay)

**invisible** — bar is permanently hidden. Cannot be revealed by any key.

**overlay** — bar is permanently visible and drawn on top of all windows, but is transparent to input events (clicks pass through it).

Toggle between `hide` and `dock` at runtime via IPC:
```
swaymsg bar mode toggle
swaymsg bar bar-0 mode toggle
```

---

## Status Command

`status_command` runs a program with `sh -c`. Sway reads its stdout:

- **Plain text mode**: each line replaces the status area text. Enable pango markup for plain text with `pango_markup enabled`.
- **JSON mode**: first line is a header object, then an infinite JSON array of block arrays. Detected automatically by sway when the output starts with `{`.

```
# Plain text — one line per update
status_command while true; do date +"%a %b %d %H:%M"; sleep 1; done

# JSON protocol — use a script
status_command ~/.scripts/status.sh
```

Edge/padding settings for the status area:
- `status_edge_padding <px>` — padding at the right screen edge (default: 3, scaled by output scale)
- `status_padding <px>` — vertical padding inside blocks (default: 1; set to 0 for full-height blocks)

---

---

# Swaybar Configuration Options

Complete reference for all settings in a `bar { ... }` block. All settings except `id` can also be changed at runtime via IPC (`swaymsg bar <id> <setting> <value>`).

---

## Identification and Positioning

### `id <name>`

Sets the bar's identifier. Used to target the bar with IPC commands and `bar <id> { ... }` syntax. If omitted, sway assigns an id automatically (e.g. `bar-0`).

```
id main
```

### `position top|bottom`

Controls which edge of the screen the bar attaches to.

```
position top     # bar at top of screen
position bottom  # bar at bottom (default)
```

---

## Visibility Modes

### `mode dock|hide|invisible|overlay`

Controls how the bar is displayed.

| Mode | Behavior |
|---|---|
| `dock` | Always visible at screen edge, reserves space (default) |
| `hide` | Hidden by default; shown when modifier key is held or on urgency |
| `invisible` | Always hidden, cannot be shown |
| `overlay` | Always visible, drawn on top of windows, transparent to input |

```
mode dock
mode hide
```

Runtime-only variant: `mode toggle` switches between `hide` and `dock`.

### `hidden_state show|hide`

Only meaningful when `mode hide` is active. Controls whether the bar is currently revealed or concealed.

- `hide` — bar is hidden (default), shown only when modifier is pressed or urgency fires
- `show` — bar is visible even in hide mode, drawn on top of windows

```
hidden_state hide
```

### `modifier <Modifier>|none`

The key that reveals the bar when `mode hide` is active. Uses the same modifier names as sway keybindings (e.g. `Mod4`, `Mod1`, `Shift`, `Control`). Set to `none` to disable keyboard reveal.

Default: `Mod4` (Super/Windows key).

```
modifier Mod4
modifier none
```

---

## Fonts and Spacing

### `font <pango font description>`

Sets the font for workspace buttons, status text, and all bar labels. Must be a Pango font description string.

```
font pango:JetBrainsMono Nerd Font 11
font pango:DejaVu Sans Mono 10
font pango:sans-serif 12
```

### `gaps <all> | <horizontal> <vertical> | <top> <right> <bottom> <left>`

Sets gaps (in pixels) between the bar and the screen edges. Only sides that touch a screen edge can have gaps.

```
gaps 4              # 4px on all sides
gaps 4 0            # 4px horizontal, 0px vertical
gaps 4 0 4 0        # top right bottom left
```

### `height <px>`

Sets the bar height in pixels. Default `0` auto-sizes to match the font.

```
height 28
```

---

## Status Command

### `status_command <cmd>`

Runs `<cmd>` via `sh -c`. Each line written to stdout updates the status area. Supports plain text and the JSON protocol (swaybar-protocol(7)).

To disable a running status command via IPC, set it to a single dash:
```
# In config
status_command ~/.scripts/status.sh

# Via IPC to disable
swaymsg 'bar bar-0 status_command -'
```

### `status_edge_padding <px>`

Padding between the status area and the right edge of the bar. Multiplied by output scale. Default: `3`.

```
status_edge_padding 5
```

### `status_padding <px>`

Vertical padding inside status blocks. Multiplied by output scale. Default: `1`. Set to `0` to allow blocks to fill the full bar height.

```
status_padding 0
```

### `pango_markup enabled|disabled`

Enables or disables Pango markup for plain-text status lines. Has no effect when using the JSON protocol (markup is controlled per-block via the `markup` property).

```
pango_markup enabled
```

### `separator_symbol <symbol>`

Sets the separator character drawn between blocks.

```
separator_symbol " | "
separator_symbol "·"
```

---

## Workspace Buttons

### `workspace_buttons yes|no`

Show or hide the workspace buttons. Default: `yes`.

```
workspace_buttons yes
```

### `workspace_min_width <px>`

Minimum width of each workspace button in pixels. Also applies to the binding mode indicator. Default: `0`.

```
workspace_min_width 30
```

### `strip_workspace_numbers yes|no`

If `yes`, hides the number prefix from workspace buttons and shows only the custom name. Default: `no`.

```
strip_workspace_numbers yes
# Workspace "1: Terminal" shows as "Terminal"
```

### `strip_workspace_name yes|no`

If `yes`, hides the custom name from workspace buttons and shows only the number. Default: `no`.

```
strip_workspace_name yes
# Workspace "1: Terminal" shows as "1"
```

### `wrap_scroll yes|no`

Whether scrolling through workspaces on the bar wraps around from last to first. Default: `no`.

```
wrap_scroll yes
```

---

## Binding Mode Indicator

### `binding_mode_indicator yes|no`

Shows or hides the current binding mode name in the bar. Colored using `binding_mode` colors (falls back to `urgent_workspace` colors). Default: `yes`.

```
binding_mode_indicator yes
```

---

## System Tray

### `tray_output none|all|<output>`

Controls which outputs show the system tray. Can be specified multiple times. Use `*` to reset to all outputs.

```
tray_output none           # disable tray entirely
tray_output eDP-1          # tray on internal display only
tray_output DP-1
tray_output DP-2           # tray on both external displays
```

### `tray_padding <px>`

Pixel padding surrounding the tray and between tray icons. Default: `2`.

```
tray_padding 4
```

### `icon_theme <name>`

Name of the icon theme used for tray icons. Defaults to the hicolor fallback theme.

```
icon_theme Papirus-Dark
icon_theme Adwaita
```

### Tray Mouse Bindings

```
# By x11 button number or event name
tray_bindsym button1 Activate
tray_bindsym button2 ContextMenu
tray_bindsym button3 SecondaryActivate

# By event code (from libinput debug-events)
tray_bindcode 272 Activate
```

Valid actions: `ContextMenu`, `Activate`, `SecondaryActivate`, `ScrollDown`, `ScrollLeft`, `ScrollRight`, `ScrollUp`, `nop` (disables the button).

---

## Mouse Bindings on Bar Background

Bindings here fire when clicking the bar background (not workspace buttons or tray).

```
bindsym button4 workspace prev    # scroll up = previous workspace
bindsym button5 workspace next    # scroll down = next workspace

# --release fires on button release instead of press
bindsym --release button3 exec wofi --show drun
```

`unbindsym` removes a binding:
```
unbindsym button4
```

`bindcode` / `unbindcode` accept raw event codes instead of x11 button numbers.

---

## Output Selection

### `output <name>`

Restricts the bar to a specific output. Can be specified multiple times for multiple outputs. If omitted, the bar appears on all outputs. Use `*` to reset to all outputs.

```
output eDP-1          # internal display only
output DP-1
output DP-2           # two external displays
output *              # reset to all outputs
```

---

## Custom Bar Binary

### `swaybar_command <command>`

Replaces the default `swaybar` binary with a custom implementation. Rarely needed.

```
swaybar_command swaybar
```

---

## Full Example Bar Block

```
bar {
    id main
    position top
    mode dock
    font pango:JetBrainsMono Nerd Font 11
    height 28
    gaps 4
    status_command ~/.scripts/status.sh
    status_edge_padding 6
    status_padding 1
    workspace_buttons yes
    workspace_min_width 24
    strip_workspace_numbers yes
    binding_mode_indicator yes
    wrap_scroll no
    tray_output eDP-1
    tray_padding 3
    icon_theme Papirus-Dark

    bindsym button4 workspace prev
    bindsym button5 workspace next

    colors {
        background #1e1e2e
        statusline #cdd6f4
        separator  #6c7086

        focused_workspace  #89b4fa #89b4fa #1e1e2e
        active_workspace   #313244 #313244 #cdd6f4
        inactive_workspace #1e1e2e #1e1e2e #6c7086
        urgent_workspace   #f38ba8 #f38ba8 #1e1e2e
        binding_mode       #fab387 #fab387 #1e1e2e
    }
}
```

---

# Swaybar JSON Status Line Protocol

Reference for the i3bar-compatible JSON protocol used by `status_command` scripts. Full spec: `swaybar-protocol(7)`.

---

## Overview

When a `status_command` script outputs a line starting with `{`, sway switches to JSON mode. The protocol has two parts:

1. **Header** — a single JSON object on the first line, followed by a newline
2. **Body** — an opening `[` on its own line, then an infinite stream of update arrays, one per line

Each update is an array of block objects. Sway renders each block object as a separate segment in the status area. After writing a block array, flush stdout.

---

## Header Object

The header must be the first line of output. Only `version` is required.

| Property | Type | Default | Description |
|---|---|---|---|
| `version` | integer | required | Must be `1` |
| `click_events` | boolean | `false` | If `true`, sway writes click events to the script's stdin |
| `stop_signal` | integer | `SIGSTOP` (17) | Signal sway sends when the bar is hidden (pause rendering) |
| `cont_signal` | integer | `SIGCONT` (18) | Signal sway sends when the bar becomes visible again (resume rendering) |

Minimal header:
```json
{"version": 1}
```

Full header (with click events and custom signals):
```json
{
    "version": 1,
    "click_events": true,
    "stop_signal": 19,
    "cont_signal": 18
}
```

---

## Body Format

Open the outer array once, then write one update array per status change:

```
[
[{...block...},{...block...}],
[{...block...},{...block...}],
[{...block...},{...block...}],
```

The outer `[` is never closed. Each inner array (one per update) ends with a `,` and a newline. Sway renders the most recently received array.

In shell:
```bash
echo '{"version":1}'  # header
echo '['              # open body array
while true; do
    printf '[%s]\n,' "$(build_blocks)"
    sleep 1
done
```

---

## Block Properties

Each block is a JSON object. Only `full_text` is required.

| Property | Type | Default | Description |
|---|---|---|---|
| `full_text` | string | required | Text displayed in the block. Missing = block skipped |
| `short_text` | string | — | Shown instead of `full_text` when space is tight |
| `color` | string | (statusline) | Text color: `#RRGGBB` or `#RRGGBBAA` |
| `background` | string | transparent | Block background color |
| `border` | string | — | Border color |
| `border_top` | integer | `1` | Top border height in pixels |
| `border_right` | integer | `1` | Right border width in pixels |
| `border_bottom` | integer | `1` | Bottom border height in pixels |
| `border_left` | integer | `1` | Left border width in pixels |
| `min_width` | int or string | — | Minimum block width: pixels (int) or reference string (string) |
| `align` | string | `left` | Text alignment when `min_width` is set: `left`, `right`, `center` |
| `name` | string | — | Block identifier for click events |
| `instance` | string | — | Secondary identifier; `name`+`instance` pairs must be unique |
| `urgent` | boolean | `false` | Render block with urgent workspace colors |
| `separator` | boolean | `true` | Draw separator after this block |
| `separator_block_width` | integer | `9` | Pixels reserved after block for the separator |
| `markup` | string | `none` | `none` or `pango` — enables Pango markup in `full_text` |

Custom properties are allowed and silently ignored by sway. Prefix them with `_`:
```json
{"full_text": "75%", "_raw_value": 75}
```

---

## Full Block Example

```json
{
    "full_text": "Thu 30 May 2019 02:09:15",
    "short_text": "02:09",
    "color": "#cccccc",
    "background": "#111111",
    "border": "#222222",
    "border_top": 1,
    "border_bottom": 1,
    "border_left": 0,
    "border_right": 0,
    "min_width": 200,
    "align": "center",
    "name": "clock",
    "instance": "local",
    "urgent": false,
    "separator": true,
    "separator_block_width": 9,
    "markup": "none"
}
```

---

## Click Events

When `click_events: true` is set in the header, sway writes a JSON object to the script's stdin whenever a block is clicked. Read it line by line from stdin.

| Property | Type | Description |
|---|---|---|
| `name` | string | The `name` of the clicked block |
| `instance` | string | The `instance` of the clicked block |
| `x` | integer | Absolute X coordinate of the click |
| `y` | integer | Absolute Y coordinate of the click |
| `button` | integer | X11 button number (0 if no X11 mapping) |
| `event` | integer | Raw event code (from libinput) |
| `relative_x` | integer | X offset from the block's top-left corner |
| `relative_y` | integer | Y offset from the block's top-left corner |
| `width` | integer | Block width in pixels |
| `height` | integer | Block height in pixels |

Example click event:
```json
{
    "name": "clock",
    "instance": "local",
    "x": 1900,
    "y": 10,
    "button": 1,
    "event": 274,
    "relative_x": 100,
    "relative_y": 8,
    "width": 120,
    "height": 18
}
```

Button numbers: `1` = left click, `2` = middle click, `3` = right click, `4` = scroll up, `5` = scroll down.

Note: sway does not currently send a `modifiers` property (unlike i3bar).

---

## Minimal Working Example

A complete shell script implementing the protocol:

```bash
#!/bin/bash
# Minimal swaybar status script — JSON protocol

# Header: tell sway to use protocol version 1
echo '{"version":1}'
# Open the body array (never closed)
echo '['

while true; do
    # Gather data
    time_str=$(date '+%a %b %d  %H:%M:%S')
    bat_raw=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo "N/A")
    bat_status=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || echo "")

    # Determine battery color
    if [[ "$bat_raw" =~ ^[0-9]+$ ]]; then
        if (( bat_raw <= 20 )); then
            bat_color='"#f38ba8"'   # red
        elif (( bat_raw <= 50 )); then
            bat_color='"#fab387"'   # orange
        else
            bat_color='"#a6e3a1"'   # green
        fi
        bat_text="${bat_raw}%"
        [[ "$bat_status" == "Charging" ]] && bat_text="${bat_text} +"
    else
        bat_color='"#6c7086"'
        bat_text="N/A"
    fi

    # Emit one update: array of blocks followed by comma
    printf '[{"full_text":"%s","color":%s,"name":"battery"},{"full_text":"%s","name":"clock"}],\n' \
        "$bat_text" "$bat_color" "$time_str"

    sleep 1
done
```

---

## Signal Pause/Resume

Sway sends `stop_signal` to the script when the bar hides (mode `hide` with no modifier held), and `cont_signal` when it becomes visible again. Use these to pause expensive work:

```bash
#!/bin/bash

paused=0
trap 'paused=1' SIGUSR1   # stop_signal: 10 -> SIGUSR1
trap 'paused=0' SIGUSR2   # cont_signal: 12 -> SIGUSR2

echo '{"version":1,"stop_signal":10,"cont_signal":12}'
echo '['

while true; do
    if (( paused == 0 )); then
        printf '[{"full_text":"%s"}],\n' "$(date '+%H:%M:%S')"
    fi
    sleep 1
done
```

Default signals if not overridden: `stop_signal` = SIGSTOP (17), `cont_signal` = SIGCONT (18). SIGSTOP cannot be caught by bash; use custom signal numbers if you need trap-based handling.

---

## Pango Markup

Set `"markup": "pango"` on a block to parse its `full_text` as Pango markup. Useful for inline color changes, bold/italic, and icon fonts.

```json
{
    "full_text": "<span color='#f38ba8'></span> <span color='#cdd6f4'>75%</span>",
    "markup": "pango",
    "name": "battery"
}
```

Common Pango tags:

| Tag | Effect |
|---|---|
| `<span color="#RRGGBB">text</span>` | Inline text color |
| `<span background="#RRGGBB">text</span>` | Inline background |
| `<span font="FontName 12">text</span>` | Font override |
| `<b>text</b>` | Bold |
| `<i>text</i>` | Italic |
| `<u>text</u>` | Underline |
| `<tt>text</tt>` | Monospace |

---

## Practical Patterns

### Per-block click handling (bash)

```bash
#!/bin/bash
echo '{"version":1,"click_events":true}'
echo '['

# Read click events in background
handle_clicks() {
    while IFS= read -r line; do
        name=$(printf '%s' "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name',''))")
        button=$(printf '%s' "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('button',0))")
        case "$name:$button" in
            clock:1)    notify-send "Date" "$(date '+%A, %B %d %Y')" ;;
            battery:3)  exec kitty -e watch -n1 acpi ;;
        esac
    done
}
handle_clicks &

while true; do
    printf '[{"full_text":"%s","name":"clock"},{"full_text":"bat","name":"battery"}],\n' \
        "$(date '+%H:%M:%S')"
    sleep 1
done
```

### Conditional color by threshold

```bash
get_cpu_block() {
    local usage
    usage=$(top -bn1 | awk '/^%Cpu/ {print int($2+$4)}')
    local color
    if   (( usage >= 90 )); then color='"#f38ba8"'   # red
    elif (( usage >= 70 )); then color='"#fab387"'   # orange
    else                         color='"#a6e3a1"'   # green
    fi
    printf '{"full_text":"CPU %d%%","color":%s,"name":"cpu"}' "$usage" "$color"
}
```

### Separator customization

```json
{"full_text": "segment", "separator": false, "separator_block_width": 0}
```

Set `separator: false` and `separator_block_width: 0` to make adjacent blocks appear flush with no gap between them. Useful for building segmented/powerline-style layouts.

### min_width for stable layout

Using a string as `min_width` sizes the block to at least the width of that string, preventing the bar from shifting as values change:

```json
{"full_text": "75%", "min_width": "100%", "align": "right", "name": "battery"}
```

### Python status script skeleton

```python
#!/usr/bin/env python3
import json
import sys
import time
from datetime import datetime

def get_blocks():
    now = datetime.now().strftime("%a %b %d  %H:%M:%S")
    try:
        with open("/sys/class/power_supply/BAT0/capacity") as f:
            bat = int(f.read().strip())
        color = "#f38ba8" if bat <= 20 else "#fab387" if bat <= 50 else "#a6e3a1"
    except FileNotFoundError:
        bat, color = None, "#6c7086"

    blocks = []
    if bat is not None:
        blocks.append({
            "full_text": f"{bat}%",
            "color": color,
            "name": "battery",
            "min_width": "100%",
            "align": "right",
        })
    blocks.append({"full_text": now, "name": "clock"})
    return blocks

# Header
sys.stdout.write(json.dumps({"version": 1}) + "\n")
# Open body array
sys.stdout.write("[\n")
sys.stdout.flush()

while True:
    line = json.dumps(get_blocks()) + ","
    sys.stdout.write(line + "\n")
    sys.stdout.flush()
    time.sleep(1)
```

---

# Swaybar Color Reference

Colors are defined inside a `colors { }` block nested within the `bar { }` block.

---

## Color Format

All colors use hex notation:

| Format | Description |
|---|---|
| `#RRGGBB` | Opaque color |
| `#RRGGBBAA` | Color with alpha channel (`FF` = fully opaque, `00` = fully transparent) |

```
background #1e1e2e       # opaque
background #1e1e2e80     # 50% transparent
```

---

## Global Colors

These apply to the entire bar.

| Setting | What it colors |
|---|---|
| `background <color>` | Bar background |
| `statusline <color>` | Status area text (plain-text or JSON blocks without an explicit `color`) |
| `separator <color>` | Separator between status blocks |
| `focused_background <color>` | Bar background on the currently focused output; falls back to `background` |
| `focused_statusline <color>` | Status text on focused output; falls back to `statusline` |
| `focused_separator <color>` | Separator on focused output; falls back to `separator` |

```
colors {
    background         #1e1e2e
    statusline         #cdd6f4
    separator          #6c7086
    focused_background #181825
    focused_statusline #cdd6f4
    focused_separator  #89b4fa
}
```

---

## Workspace Button Colors

Each state takes three values: `<border> <background> <text>`.

| State | When it applies |
|---|---|
| `focused_workspace` | The workspace that has input focus |
| `active_workspace` | Visible on a non-focused output (multi-monitor only) |
| `inactive_workspace` | Not visible on any output |
| `urgent_workspace` | Contains a window with the urgency hint set |
| `binding_mode` | The binding mode indicator; falls back to `urgent_workspace` if unset |

```
colors {
    focused_workspace  #89b4fa #89b4fa #1e1e2e
    active_workspace   #313244 #313244 #cdd6f4
    inactive_workspace #1e1e2e #1e1e2e #6c7086
    urgent_workspace   #f38ba8 #f38ba8 #1e1e2e
    binding_mode       #fab387 #fab387 #1e1e2e
}
```

---

## Color Inheritance

When a focused-output variant is not set, it falls back to its base:

```
focused_background  →  background
focused_statusline  →  statusline
focused_separator   →  separator
binding_mode        →  urgent_workspace (all three: border, bg, text)
```

---

## Complete Color Example (Catppuccin Mocha)

```
bar {
    # ... other bar settings ...

    colors {
        # Global
        background         #1e1e2e
        statusline         #cdd6f4
        separator          #6c7086
        focused_background #181825
        focused_statusline #cdd6f4
        focused_separator  #89b4fa

        # Workspace buttons: border background text
        focused_workspace  #89b4fa #89b4fa #1e1e2e
        active_workspace   #313244 #313244 #cdd6f4
        inactive_workspace #1e1e2e #1e1e2e #6c7086
        urgent_workspace   #f38ba8 #f38ba8 #1e1e2e
        binding_mode       #fab387 #fab387 #1e1e2e
    }
}
```

---

## Complete Color Example (Gruvbox Dark)

```
bar {
    colors {
        # Global
        background #282828
        statusline #ebdbb2
        separator  #665c54

        # Workspace buttons: border background text
        focused_workspace  #d79921 #d79921 #282828
        active_workspace   #504945 #504945 #ebdbb2
        inactive_workspace #282828 #282828 #928374
        urgent_workspace   #cc241d #cc241d #fbf1c7
        binding_mode       #98971a #98971a #282828
    }
}
```

---

## Minimal Colors Block

Only the settings you override are needed. Everything else uses sway's built-in defaults (which vary by theme/GTK settings).

```
bar {
    colors {
        background #1e1e2e
        statusline #cdd6f4
        focused_workspace #89b4fa #89b4fa #1e1e2e
        inactive_workspace #1e1e2e #1e1e2e #6c7086
    }
}
```
