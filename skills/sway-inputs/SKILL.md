---
name: sway-inputs
description: "Keyboard layout (XKB), pointer and touchpad configuration via libinput, tablet devices, and multiseat setup in sway. Use when configuring keyboard layout or language switching, adjusting touchpad tap/scroll behavior, setting mouse acceleration, mapping a drawing tablet to an output, configuring cursor themes, disabling a touchpad while typing, or setting up shortcut inhibition."
---
# Sway Input Configuration

Sway configures all input devices — keyboards, mice, touchpads, tablets, and touch screens — directly inside `~/.config/sway/config` using `input` and `seat` blocks. Settings are backed by libinput for pointer/touchpad devices and by XKB for keyboards. No external daemon is required.

---

## Input Device Selectors

There are three ways to target a device:

**By exact identifier** (most specific, wins in config file):
```
input "1:1:AT_Translated_Set_2_keyboard" {
    xkb_layout us
}
```

**By device type** (applies to all devices of that type):
```
input type:touchpad {
    tap enabled
    natural_scroll enabled
}
```

**By wildcard** (least specific, applies to everything):
```
input "*" {
    accel_profile flat
}
```

Available types: `touchpad`, `pointer`, `keyboard`, `touch`, `tablet_tool`, `tablet_pad`, `switch`.

**Precedence in config files:** `<identifier>` > `type:<input_type>` > `*`

**Important:** When applying settings at runtime via `swaymsg`, specificity is ignored — all matching devices are updated. A later `type:` command can override an earlier `<identifier>` command when used at runtime.

### Finding device identifiers

```bash
swaymsg -t get_inputs
```

Look for the `identifier` field in the JSON output. Copy it exactly, including quotes, into the config.

---

## Config Pattern

Both inline and block forms are valid. The block form is preferred for readability when setting more than one option:

```
# Inline form
input type:keyboard xkb_layout us

# Block form (preferred for multiple options)
input type:keyboard {
    xkb_layout us,es
    xkb_options grp:alt_shift_toggle,caps:escape
    repeat_delay 300
    repeat_rate 40
}

input type:touchpad {
    tap enabled
    natural_scroll enabled
    dwt enabled
    scroll_method two_finger
}
```

---

## Quick Reference Table

| Goal | Option | Example |
|---|---|---|
| Set keyboard layout | `xkb_layout` | `xkb_layout us` |
| Two layouts + switch key | `xkb_layout` + `xkb_options` | `xkb_layout us,es` / `xkb_options grp:alt_shift_toggle` |
| Caps Lock as Escape | `xkb_options` | `xkb_options caps:escape` |
| Key repeat delay | `repeat_delay` | `repeat_delay 300` |
| Key repeat rate | `repeat_rate` | `repeat_rate 40` |
| Tap to click | `tap` | `tap enabled` |
| Natural scroll | `natural_scroll` | `natural_scroll enabled` |
| Disable while typing | `dwt` | `dwt enabled` |
| Mouse acceleration | `pointer_accel` | `pointer_accel -0.5` |
| Flat accel profile | `accel_profile` | `accel_profile flat` |
| Cursor theme | `xcursor_theme` (seat) | `seat * xcursor_theme Adwaita 24` |
| Hide cursor on typing | `hide_cursor` (seat) | `seat * hide_cursor when-typing enable` |
| Map tablet to output | `map_to_output` | `map_to_output HDMI-A-1` |

---

## Reference Files

- **KEYBOARD_XKB.md** — XKB layout, variant, options, repeat rate, numlock/capslock init
- **POINTER_LIBINPUT.md** — acceleration, tap, scroll, DWT, click methods, send events
- **ADVANCED_SEAT.md** — tablet mapping, seat config, cursor theme, shortcut inhibition
