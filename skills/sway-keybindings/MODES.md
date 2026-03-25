# Binding Modes in Sway

Binding modes let you define a completely separate set of keybindings that become active when you enter that mode. While in a non-default mode, only the keys defined for that mode are recognized — everything else is silently ignored. This prevents accidental key conflicts and enables modal workflows similar to Vim.

---

## What are Modes

When sway starts, it is in the `"default"` mode. All keybindings defined at the top level of your config are part of `"default"`. You can define additional named modes and switch into them. Once in a non-default mode, none of the default bindings fire until you explicitly return to `"default"`.

Use cases:
- Resize mode (avoid conflicting with h/j/k/l for focus)
- System mode (lock, logout, reboot behind a second keypress)
- Launcher mode (dedicated keys for specific apps)
- Passthrough mode (send all keypresses to a nested compositor or VM)

---

## Defining a Mode

```sway
mode [--pango_markup] "<mode-name>" {
    bindsym <key> <command>
    bindcode <code> <command>
    # set is also valid inside a mode block
    set $var value
}
```

The `--pango_markup` flag allows the mode name to contain Pango markup, which is displayed in the status bar.

Only `bindsym`, `bindcode`, `bindswitch`, and `set` are valid inside a mode block. Every other command must go outside.

```sway
# Minimal valid mode definition
mode "resize" {
    bindsym h resize shrink width 10px
    bindsym Escape mode "default"
}
```

---

## Mode Switching

### Entering a mode

From within `"default"` (or any other mode), use `mode "<name>"` as the command for a binding:

```sway
bindsym $mod+r mode "resize"
bindsym $mod+Shift+e mode "system"
```

### Exiting a mode

Always define at least two exit keys: `Escape` and `Return`. This matches user expectations and provides a reliable bail-out:

```sway
mode "resize" {
    bindsym h resize shrink width 10px
    bindsym l resize grow width 10px

    bindsym Return mode "default"
    bindsym Escape mode "default"
}
```

You can also exit to a different mode (nested entry), but this is unusual.

---

## Complete Resize Mode Example

The canonical resize mode — supports both vim-style (h/j/k/l) and arrow keys, with pixel and percentage-point variants:

```sway
mode "resize" {
    # Shrink/grow width and height with vim keys
    bindsym h resize shrink width 10px
    bindsym j resize grow height 10px
    bindsym k resize shrink height 10px
    bindsym l resize grow width 10px

    # Same with arrow keys (convenience)
    bindsym Left  resize shrink width 10px
    bindsym Down  resize grow height 10px
    bindsym Up    resize shrink height 10px
    bindsym Right resize grow width 10px

    # Larger steps with Shift held
    bindsym Shift+h resize shrink width 50px
    bindsym Shift+j resize grow height 50px
    bindsym Shift+k resize shrink height 50px
    bindsym Shift+l resize grow width 50px

    # For tiling containers: use ppt (percentage points) instead of px
    # (px is used for floating containers; tiling ignores px and uses ppt)
    # Uncomment to use ppt:
    # bindsym h resize shrink width 5ppt
    # bindsym l resize grow width 5ppt

    # Exit resize mode
    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym $mod+r mode "default"
}

bindsym $mod+r mode "resize"
```

Resize command syntax:

```
resize shrink|grow width|height [<amount> [px|ppt]]
resize set [width] <width> [px|ppt] [height] <height> [px|ppt]
```

- `px` — pixels (default for floating windows)
- `ppt` — percentage points (default for tiling windows)
- Amount defaults to 10 if omitted

---

## Named Modes vs Default

`"default"` is the built-in starting mode. The name is literal — the string must be exactly `"default"` to return to it.

```sway
# Correct: returns to the default mode
bindsym Escape mode "default"

# Wrong: creates a new mode named "Default" (capital D)
bindsym Escape mode "Default"
```

You can switch between any two modes, not just to/from default:

```sway
mode "launcher" {
    bindsym b exec firefox; mode "default"
    bindsym t exec foot;    mode "default"
    bindsym Escape mode "default"
}

mode "system" {
    bindsym l exec swaylock; mode "default"
    bindsym Escape mode "default"
}

# Jump from system to launcher (unusual but valid)
mode "system" {
    bindsym Return mode "launcher"
}
```

---

## Practical Mode Patterns

### System mode (lock / logout / reboot)

Shows a mode indicator in the bar. Each action returns to default after executing.

```sway
set $mode_system "System: [l] lock  [e] logout  [s] suspend  [r] reboot"

mode $mode_system {
    bindsym l exec swaylock,                    mode "default"
    bindsym e exec swaymsg exit,                mode "default"
    bindsym s exec systemctl suspend,           mode "default"
    bindsym r exec systemctl reboot,            mode "default"

    bindsym Return mode "default"
    bindsym Escape mode "default"
}

bindsym $mod+Shift+e mode $mode_system
```

Note: use `,` (comma) to chain `mode "default"` after the exec — criteria are retained across `,` so the mode switch happens in the same command sequence.

### Launcher mode (open specific apps)

```sway
set $mode_launch "Launch: [b] browser  [f] files  [t] terminal  [m] music"

mode $mode_launch {
    bindsym b exec firefox,                 mode "default"
    bindsym f exec thunar,                  mode "default"
    bindsym t exec foot,                    mode "default"
    bindsym m exec foot -e ncmpcpp,         mode "default"

    bindsym Return mode "default"
    bindsym Escape mode "default"
}

bindsym $mod+o mode $mode_launch
```

### Passthrough mode (send all keys to nested session)

Define only the exit binding. Every other key passes through unfiltered.

```sway
mode "passthrough" {
    bindsym $mod+Shift+F12 mode "default"
}

bindsym $mod+Shift+F12 mode "passthrough"
```

Useful for: QEMU/KVM, nested Sway/Wayland, VNC sessions.

### Pango markup in mode name (displays in bar)

```sway
mode --pango_markup "<b>Resize</b> | h/j/k/l or arrows | Esc to exit" {
    bindsym h resize shrink width 10px
    bindsym l resize grow width 10px
    bindsym j resize grow height 10px
    bindsym k resize shrink height 10px
    bindsym Return mode "default"
    bindsym Escape mode "default"
}
```

The mode name string (with markup) appears in the sway bar while the mode is active.
