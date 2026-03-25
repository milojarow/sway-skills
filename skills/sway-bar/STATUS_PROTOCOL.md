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
