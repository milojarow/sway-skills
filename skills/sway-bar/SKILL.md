---
name: sway-bar
description: "Status bar configuration (swaybar) and the JSON protocol for writing custom status generators. Use when configuring the swaybar appearance, choosing between dock/hide/invisible bar modes, setting bar colors or fonts, configuring the system tray icon size or gap, implementing a custom status_command script, handling click events in status blocks, or using pango markup in status output."
---
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

## Reference Files

- **SWAYBAR_CONFIG.md** — complete reference for every bar configuration option
- **COLORS.md** — full color theming reference with examples
- **STATUS_PROTOCOL.md** — JSON protocol spec for custom status_command scripts
