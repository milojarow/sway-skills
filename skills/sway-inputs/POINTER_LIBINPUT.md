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
