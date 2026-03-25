# Keyboard XKB Configuration

XKB (X Keyboard Extension) is the standard mechanism for keyboard layout configuration on Linux, and sway uses it natively under Wayland. All XKB settings apply to `input type:keyboard` or a specific keyboard identifier.

---

## XKB Configuration Options

### `xkb_layout`

Sets the keyboard layout. Multiple layouts can be specified as a comma-separated list; they are indexed from zero.

```
input type:keyboard {
    xkb_layout us
}

# Two layouts: English and Spanish
input type:keyboard {
    xkb_layout us,es
}
```

### `xkb_variant`

Sets the layout variant. Examples: `dvorak`, `colemak`, `intl` (international with dead keys), `nodeadkeys`.

```
input type:keyboard {
    xkb_layout us
    xkb_variant dvorak
}

# Spanish with no dead keys
input type:keyboard {
    xkb_layout es
    xkb_variant nodeadkeys
}
```

### `xkb_model`

Sets the keyboard model, which affects extra keys specific to certain hardware. Most users can omit this; the default works for standard PC keyboards. Example values: `pc105`, `thinkpad`, `apple`.

```
input type:keyboard {
    xkb_model pc105
}
```

### `xkb_rules`

Sets the rules file used for keyboard mapping composition. Almost never needs to be changed from the default (`evdev`).

```
input type:keyboard {
    xkb_rules evdev
}
```

### `xkb_options`

Sets extra XKB options. Multiple options are separated by commas. This is the most commonly customized XKB setting.

```
input type:keyboard {
    xkb_options grp:alt_shift_toggle,caps:escape
}
```

For a full list of available options, see `man xkeyboard-config` or browse `/usr/share/X11/xkb/rules/evdev.lst`.

---

## Common Layout Examples

### US English only

```
input type:keyboard {
    xkb_layout us
}
```

### Spanish (Spain)

```
input type:keyboard {
    xkb_layout es
}
```

### French (AZERTY)

```
input type:keyboard {
    xkb_layout fr
}
```

### German (QWERTZ)

```
input type:keyboard {
    xkb_layout de
}
```

### Switching between two layouts

Define both layouts and pick a toggle key combo via `xkb_options`. At runtime, switch programmatically with `xkb_switch_layout`:

```
input type:keyboard {
    xkb_layout us,es
    xkb_options grp:alt_shift_toggle
}
```

Toggle via swaymsg at runtime (e.g., bound to a key):

```
# In sway config — bind Super+Space to cycle layouts
bindsym $mod+Space input type:keyboard xkb_switch_layout next
```

`xkb_switch_layout` accepts `next`, `prev`, or a zero-based index:

```bash
swaymsg input type:keyboard xkb_switch_layout next
swaymsg input type:keyboard xkb_switch_layout 0   # switch to first layout
```

### Using Caps Lock as Escape

```
input type:keyboard {
    xkb_options caps:escape
}
```

### Caps Lock as both Escape (tap) and Ctrl (hold)

```
input type:keyboard {
    xkb_options caps:escape_shifted_capslock
}
```

Or use the `xcape`-style XKB option if your distro ships it:

```
input type:keyboard {
    xkb_options ctrl:nocaps
}
```

---

## Repeat Settings

These control how long a key must be held before repeating begins, and how fast it repeats once started.

```
input type:keyboard {
    repeat_delay 300    # ms before repeat starts (default: 600)
    repeat_rate  40     # characters per second (default: 25)
}
```

Lower `repeat_delay` and higher `repeat_rate` = snappier key repeat, useful for fast typists and Vim users.

---

## Key Grouping

`xkb_keyboard_grouping` controls how multiple physical keyboard devices share layout state within a seat.

```
seat seat0 {
    keyboard_grouping smart    # default: sync layout state across keyboards
}

seat seat0 {
    keyboard_grouping none     # each keyboard device has isolated state
}
```

- `smart`: keyboards with the same keymap and repeat info are grouped. Layout switches (e.g., switching to Spanish) affect all keyboards in the group simultaneously. Useful when a keyboard appears as multiple input devices (common with some USB keyboards).
- `none`: each keyboard is independent. Restores behavior from older sway versions.

This is a `seat` setting, not an `input` setting.

---

## NumLock and CapsLock Initialization

These can only be set in the config file, not at runtime:

```
input type:keyboard {
    xkb_numlock  enabled    # turn on NumLock at startup
    xkb_capslock disabled   # keep CapsLock off at startup (default)
}
```

Useful on systems with a numpad where NumLock should always be on at login.

---

## Loading a Custom XKB File

For fully custom keyboard configurations, you can dump a keymap and load it directly. This overrides all `xkb_layout`, `xkb_model`, `xkb_options`, `xkb_rules`, and `xkb_variant` settings.

**Dump current keymap (X11 only, useful for reference):**
```bash
xkbcomp $DISPLAY keymap.xkb
```

**Load a custom keymap file in sway config:**
```
input "1:1:AT_Translated_Set_2_keyboard" {
    xkb_file /home/milo/.config/sway/my-keymap.xkb
}
```

---

## Applying Settings to Specific vs. All Keyboards

Apply to all keyboards (recommended for single-keyboard setups):
```
input type:keyboard {
    xkb_layout us
    xkb_options caps:escape
}
```

Apply only to a specific device (useful in multi-keyboard setups):
```
input "1:1:AT_Translated_Set_2_keyboard" {
    xkb_layout us
}

input "9610:30:SINO_WEALTH_USB_Keyboard" {
    xkb_layout us,es
    xkb_options grp:alt_shift_toggle
}
```

Find identifiers with `swaymsg -t get_inputs | grep identifier`.
