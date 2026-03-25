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
