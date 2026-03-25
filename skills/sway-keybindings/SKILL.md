---
name: sway-keybindings
description: "Keybinding syntax, binding modes, window criteria, layout management, and workspace control for sway WM. Use when defining keyboard shortcuts with bindsym or bindcode, creating or switching binding modes, moving or resizing tiled and floating windows, managing window layout (tiling/floating/tabbed/stacking), working with window criteria for targeting specific windows, switching workspaces or moving containers between workspaces, or assigning windows to outputs and workspaces automatically."
---
# Sway Keybindings, Modes, and Window Management

Sway uses a declarative config where keybindings are defined with `bindsym` (by key name) or `bindcode` (by hardware code), and complex behavior is organized into named binding modes. Window management commands operate on the currently focused container by default, or on any container matching a criteria expression. All commands can be used at runtime via `swaymsg` or bound to keys.

---

## Keybinding Syntax

### `bindsym` — bind by key name (most common)

```
bindsym [flags] <modifier+...+key> <command>
```

```sway
# Basic binding
bindsym $mod+Return exec foot

# Multi-modifier
bindsym $mod+Shift+q kill

# Exec on key release instead of press
bindsym --release $mod+Print exec grimshot save area

# Run even when screen is locked
bindsym --locked XF86AudioRaiseVolume exec pactl set-sink-volume @DEFAULT_SINK@ +5%

# Run even when a shortcuts inhibitor is active (e.g., inside a VM)
bindsym --inhibited $mod+Escape mode "default"

# Silence the "overwriting existing binding" warning
bindsym --no-warn $mod+d exec wofi

# Do not repeat when key is held
bindsym --no-repeat $mod+Print exec grimshot save screen

# Bind to a specific input device only
bindsym --input-device="1:1:AT_Translated_Set_2_keyboard" $mod+Return exec foot
```

### `bindcode` — bind by hardware keycode

Use when you want layout-independent bindings or for keys that lack a standard XKB name.

```sway
# Bind hardware keycode 108 (typically Alt_R on many keyboards)
bindcode 108 exec swaymsg mode "default"
```

### Modifier key names

| XKB name | Alias | Meaning |
|---|---|---|
| `Shift` | — | Shift |
| `Lock` | — | Caps Lock |
| `Control` | `Ctrl` | Control |
| `Mod1` | `Alt` | Alt |
| `Mod2` | — | Num Lock |
| `Mod4` | `Super` | Logo / Super / Windows key |
| `Mod5` | — | AltGr |

The standard sway convention is to define `$mod` as a variable:

```sway
# Use Super as modifier
set $mod Mod4

# Or Alt (less common, conflicts with many apps)
set $mod Mod1
```

Combine modifiers with `+`:

```sway
bindsym $mod+Shift+Return exec foot
bindsym Ctrl+Alt+t exec foot
bindsym $mod+Shift+Ctrl+r reload
```

### `--to-code` flag

Keysym bindings are layout-dependent. If you switch keyboard layouts and want bindings to follow physical key positions rather than the symbol printed on the key, use `--to-code`:

```sway
# Works on physical key position, not the symbol (useful with AZERTY, Dvorak, etc.)
bindsym --to-code $mod+h focus left
```

### `bindswitch` — bind to hardware switches

```sway
# Suspend when laptop lid is closed
bindswitch lid:on exec systemctl suspend

# Show virtual keyboard in tablet mode
bindswitch tablet:on exec swaymsg input type:touch events enabled
```

### `bindgesture` — bind to touchpad gestures

```sway
# Three-finger swipe to switch workspaces
bindgesture swipe:right workspace prev
bindgesture swipe:left workspace next

# Pinch to move containers
bindgesture pinch:inward+up move up
bindgesture pinch:inward+down move down
```

---

## Quick Reference

Common binding patterns used in a typical sway config:

| Action | Binding | Command |
|---|---|---|
| Focus left/down/up/right | `$mod+h/j/k/l` | `focus left/down/up/right` |
| Move container left/down/up/right | `$mod+Shift+h/j/k/l` | `move left/down/up/right` |
| Kill focused window | `$mod+Shift+q` | `kill` |
| Launch terminal | `$mod+Return` | `exec foot` |
| Launch app launcher | `$mod+d` | `exec wofi --show drun` |
| Toggle fullscreen | `$mod+f` | `fullscreen toggle` |
| Toggle floating | `$mod+Shift+space` | `floating toggle` |
| Toggle tiling/floating focus | `$mod+space` | `focus mode_toggle` |
| Split horizontal | `$mod+b` | `splith` |
| Split vertical | `$mod+v` | `splitv` |
| Layout tabbed | `$mod+w` | `layout tabbed` |
| Layout stacking | `$mod+s` | `layout stacking` |
| Layout toggle split | `$mod+e` | `layout toggle split` |
| Switch to workspace N | `$mod+1..9` | `workspace number 1..9` |
| Move to workspace N | `$mod+Shift+1..9` | `move container to workspace number 1..9` |
| Reload config | `$mod+Shift+c` | `reload` |
| Exit sway | `$mod+Shift+e` | `exit` |
| Enter resize mode | `$mod+r` | `mode "resize"` |

```sway
# Typical workspace bindings (repeat for 1-9)
set $ws1 "1"
bindsym $mod+1 workspace number $ws1
bindsym $mod+Shift+1 move container to workspace number $ws1
```

---

## Binding Modes

Modes allow a second (or Nth) layer of keybindings activated by a trigger. All keys not defined in the active mode are ignored. See **MODES.md** for the full reference.

```sway
# Define a resize mode
mode "resize" {
    bindsym h resize shrink width 10px
    bindsym l resize grow width 10px
    bindsym j resize grow height 10px
    bindsym k resize shrink height 10px

    # Exit the mode
    bindsym Return mode "default"
    bindsym Escape mode "default"
}

# Enter the resize mode from the default mode
bindsym $mod+r mode "resize"
```

---

## Window Criteria

Criteria let you target specific windows rather than just the focused one. Used with commands, `for_window`, and `assign`. See **WINDOWS.md** for the full reference.

```sway
# Syntax: [attribute="value" ...] command
[app_id="firefox"] focus
[app_id="pavucontrol"] floating enable

# for_window: run command whenever a matching window opens
for_window [app_id="pavucontrol"] floating enable, resize set 800 600

# assign: route windows to a workspace automatically
assign [app_id="firefox"] workspace 2
assign [class="Spotify"] workspace 9
```

---

## Reference Files

- **MODES.md** — Defining and switching binding modes, practical patterns (system mode, launcher mode, passthrough mode)
- **WINDOWS.md** — Full criteria reference, layout commands, focus/move/resize/floating/border commands
- **WORKSPACES.md** — Workspace switching, naming, output assignment, `workspace_auto_back_and_forth`
