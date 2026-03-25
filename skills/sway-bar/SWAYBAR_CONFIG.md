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
