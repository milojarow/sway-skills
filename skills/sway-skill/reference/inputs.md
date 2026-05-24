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

---

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

---

# Pointer and Touchpad Configuration (libinput)

Sway uses libinput for all pointer, mouse, and touchpad devices. All options below apply under `input type:touchpad`, `input type:pointer`, or a specific device identifier.

---

## Acceleration

### `pointer_accel`

Adjusts pointer speed. Range is -1.0 (slowest) to 1.0 (fastest). The default is 0.

```
input type:pointer {
    pointer_accel 0.3     # slightly faster
}

input type:touchpad {
    pointer_accel -0.2    # slightly slower
}
```

### `accel_profile`

Sets the acceleration algorithm.

| Profile | Behavior |
|---|---|
| `adaptive` | Speed scales with movement velocity (default libinput behavior) |
| `flat` | No acceleration; 1:1 movement ratio at all speeds |

```
input type:pointer {
    accel_profile flat        # preferred for gaming mice
}

input type:touchpad {
    accel_profile adaptive    # default, usually best for touchpads
}
```

---

## Click Methods

Controls how physical clicks are generated on touchpads.

```
input type:touchpad {
    click_method clickfinger    # 1 finger = left, 2 = right, 3 = middle
}

input type:touchpad {
    click_method button_areas   # bottom-left area = left, bottom-right = right
}

input type:touchpad {
    click_method none           # disable software click methods
}
```

When using `clickfinger`, you can also configure the button mapping:

```
input type:touchpad {
    click_method clickfinger
    clickfinger_button_map lrm    # 1=left 2=right 3=middle (default)
    # or
    clickfinger_button_map lmr    # 1=left 2=middle 3=right
}
```

---

## Tap to Click

Enables tapping the touchpad surface instead of physically clicking.

```
input type:touchpad {
    tap enabled
}
```

Configure the finger-to-button mapping for taps:

```
input type:touchpad {
    tap enabled
    tap_button_map lrm    # 1 finger=left, 2 fingers=right, 3 fingers=middle (default)
    # or
    tap_button_map lmr    # 1 finger=left, 2 fingers=middle, 3 fingers=right
}
```

---

## Drag

Tap-and-drag allows clicking by tapping and then immediately moving without lifting.

```
input type:touchpad {
    tap    enabled
    drag   enabled    # allow tap-and-drag (default when tap is on)
}
```

### `drag_lock`

Controls whether drag is released immediately on lift or waits for a second tap.

```
input type:touchpad {
    drag_lock enabled          # brief lift does not release drag
    drag_lock disabled         # lift always releases drag
    drag_lock enabled_sticky   # drag persists until next tap (default)
}
```

---

## Scroll

### `scroll_method`

```
input type:touchpad {
    scroll_method two_finger      # two-finger scroll (default for touchpads)
}

input type:pointer {
    scroll_method on_button_down  # hold a button and move to scroll
}

input type:touchpad {
    scroll_method edge            # scroll along right/bottom edge
}

input type:touchpad {
    scroll_method none            # disable scrolling
}
```

### `scroll_button`

Used with `scroll_method on_button_down`. Sets which button activates scroll mode.

```
input "device-identifier" {
    scroll_method    on_button_down
    scroll_button    button8        # use the back thumb button
}
```

Button names: `button1` (left), `button2` (middle), `button3` (right), `button8`, `button9`, or an event code from `libinput debug-events`. Set to `disable` to turn off `on_button_down`.

### `scroll_button_lock`

When enabled, the scroll button acts as a toggle rather than requiring it to be held.

```
input "device-identifier" {
    scroll_button_lock enabled
}
```

### `scroll_factor`

Multiplies scroll speed. Must be non-negative.

```
input type:touchpad {
    scroll_factor 0.8    # slower scroll
}

input type:pointer {
    scroll_factor 1.5    # faster scroll
}
```

### `natural_scroll`

Reverses scroll direction to match touchscreen-style behavior (content follows finger).

```
input type:touchpad {
    natural_scroll enabled
}
```

---

## Touchpad-Specific Options

### `dwt` — Disable While Typing

Disables the touchpad while the keyboard is in use, preventing accidental cursor movement.

```
input type:touchpad {
    dwt enabled    # recommended for laptop use
}
```

### `dwtp` — Disable While Trackpoint in Use

Disables the touchpad while a TrackPoint (pointing stick) is active. Useful on ThinkPads.

```
input type:touchpad {
    dwtp enabled
}
```

### `middle_emulation`

Simulates a middle click by pressing left and right buttons simultaneously.

```
input type:pointer {
    middle_emulation enabled
}
```

---

## Rotation

Rotates the input device coordinates clockwise by the given angle. Useful for rotated displays with touch or pen input.

```
input "device-identifier" {
    rotation_angle 90.0    # rotate 90 degrees clockwise
}
```

Valid range: 0.0 (inclusive) to 360.0 (exclusive).

---

## Calibration Matrix

Sets a raw transformation matrix for absolute-position devices (touch screens, drawing tablets). Takes 6 space-separated floats representing a 3x2 affine transformation.

```
input "device-identifier" {
    calibration_matrix 1.0 0.0 0.0 0.0 1.0 0.0    # identity (no transform)
}
```

---

## Left-Handed Mode

Swaps left and right buttons for left-handed use.

```
input type:pointer {
    left_handed enabled
}
```

---

## Send Events (Enable/Disable Input Device)

Controls whether the device sends events at all. Useful for disabling an internal touchpad when an external mouse is connected.

```
input type:touchpad {
    events disabled_on_external_mouse    # auto-disable when USB/BT mouse detected
}

input "device-identifier" {
    events disabled    # always disabled
}

input type:touchpad {
    events enabled     # always enabled (default)
}
```

At runtime, the `toggle` mode cycles through all supported modes for the device:

```bash
swaymsg input type:touchpad events toggle
```

Toggle is not valid in the config file, only at runtime.

---

# Advanced: Tablet Mapping, Seats, and Cursor Configuration

---

## Input Mapping to Output

Maps a pointer, touch, or tablet device so its input coordinates correspond to a specific monitor. Without this, a tablet or touch screen maps across the entire desktop.

```
input "device-identifier" {
    map_to_output HDMI-A-1
}

# Map to the whole desktop layout (useful for resetting a previous mapping)
input "device-identifier" {
    map_to_output *
}
```

Use `swaymsg -t get_outputs` to find output names.

---

## Input Region Cropping

### `map_to_region`

Maps the device's full input area to a specific region of the global output layout. Coordinates are in pixels relative to the global compositor space.

```
input "device-identifier" {
    map_to_region 0 0 1920 1080    # X Y width height
}
```

### `map_from_region`

Ignores input that falls outside the specified region of the device's physical surface. Useful for matching tablet aspect ratio to screen aspect ratio.

Accepts pixel coordinates or fractions (0.0 to 1.0):

```
# Crop a 16:10 tablet to match a 16:9 display (using fractions)
input "device-identifier" {
    map_from_region 0x0 1x0.9
}

# Crop using millimeters (not all devices support this)
input "device-identifier" {
    map_from_region 10x20mm 200x130mm
}
```

Only applies to devices that report absolute coordinates (tablets, touch screens). Has no effect on regular mice.

---

## Tablet Tool Configuration

### `tool_mode`

Controls whether tablet pen movement is treated as absolute (default) or relative.

```
input "device-identifier" {
    tool_mode pen      absolute    # pen tip maps to screen position (default)
    tool_mode eraser   absolute
    tool_mode *        absolute    # apply to all tools
}

input "device-identifier" {
    tool_mode pen      relative    # pen acts like a mouse — moves cursor relatively
}
```

Valid tool names: `pen`, `eraser`, `brush`, `pencil`, `airbrush`, `*` (all).

Mouse and lens tools always use relative mode regardless of this setting.

---

## Touch Input

Touch input is handled automatically when `map_to_output` is set correctly. For multi-touch screens:

```
input type:touch {
    map_to_output eDP-1
}
```

---

## Seat Configuration

A seat is a collection of input devices that share an independent keyboard focus and cursor. The default seat is `seat0`. Multiple seats are useful when multiple people share one machine with their own keyboards and mice.

```
# Configure the default seat
seat seat0 {
    xcursor_theme Adwaita 24
    hide_cursor 5000
}

# Wildcard: apply to all seats
seat * {
    xcursor_theme Adwaita 24
}
```

Find seats with:
```bash
swaymsg -t get_seats
```

The alias `-` refers to the current seat when used at runtime:
```bash
swaymsg seat - shortcuts_inhibitor toggle
```

### `attach`

Assign a specific input device to a seat:
```
seat seat1 {
    attach "3:1:my_second_keyboard"
    attach "3:2:my_second_mouse"
}
```

Use `*` to assign all devices to a seat:
```
seat seat0 {
    attach "*"
}
```

### `fallback`

Marks a seat as the fallback — it will claim any device not explicitly assigned to another seat:
```
seat seat0 {
    fallback true
}
```

---

## Cursor Theme

Sets the XCursor theme and optional size for the seat. The default seat (`seat0`) theme is also exported as `XCURSOR_THEME` and `XCURSOR_SIZE` and used by XWayland.

```
seat * {
    xcursor_theme Adwaita 24
}

seat seat0 {
    xcursor_theme Bibata-Modern-Classic 32
}
```

Installed cursor themes are typically found in `/usr/share/icons/` or `~/.local/share/icons/`. Use any directory name that contains a `cursors/` subdirectory.

---

## Hide Cursor

### Timeout-based

Hides the cursor after the specified number of milliseconds of inactivity. Minimum effective value is 100ms; 0 disables auto-hiding (default).

```
seat * {
    hide_cursor 3000    # hide after 3 seconds of inactivity
}
```

### When typing

Hides the cursor whenever a key is pressed. Useful to keep the cursor out of the way while writing.

```
seat * {
    hide_cursor when-typing enable
}
```

Note: this can interfere with applications that use simultaneous mouse + keyboard input (games, Blender, GIMP).

---

## Idle Inhibit Sources

Controls which input types prevent the seat from becoming idle. By default, any input event prevents idle.

```
seat seat0 {
    idle_inhibit keyboard pointer    # only keyboard/mouse prevent idle (touchpad excluded)
}
```

Valid sources: `keyboard`, `pointer`, `touchpad`, `touch`, `tablet_pad`, `tablet_tool`, `switch`.

---

## Pointer Constraints

Controls whether clients (e.g., games) can capture and lock the cursor.

```
seat * {
    pointer_constraint enable     # allow cursor capture (default)
}

seat * {
    pointer_constraint disable    # prevent cursor capture globally
}
```

To escape a captured application at runtime:
```bash
swaymsg seat - pointer_constraint escape
```

---

## Shortcuts Inhibition

Controls whether clients can inhibit sway keyboard shortcuts (used by virtual machines, remote desktop apps, and some games).

```
seat * {
    shortcuts_inhibitor enable     # allow clients to inhibit shortcuts (default)
}

seat * {
    shortcuts_inhibitor disable    # prevent clients from inhibiting shortcuts
}
```

**Runtime subcommands** (not valid in config file):

```bash
# Toggle inhibition for the currently focused window
swaymsg seat - shortcuts_inhibitor toggle

# Forcibly deactivate any active inhibitor on focused window
# Useful when an app becomes unresponsive and won't release shortcuts
swaymsg seat - shortcuts_inhibitor deactivate
```

To allow escaping an inhibited state via a keybinding, use `--inhibited` in `bindsym`:

```
# Bind Super+Escape to deactivate shortcut inhibition even while inhibited
bindsym --inhibited $mod+Escape seat - shortcuts_inhibitor deactivate
```

---

## Keyboard Grouping per Seat

See this document for full details. Summary:

```
seat seat0 {
    keyboard_grouping smart    # group keyboards with matching keymaps (default)
}

seat seat0 {
    keyboard_grouping none     # each keyboard device is fully independent
}
```
