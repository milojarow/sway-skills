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

See KEYBOARD_XKB.md for full details. Summary:

```
seat seat0 {
    keyboard_grouping smart    # group keyboards with matching keymaps (default)
}

seat seat0 {
    keyboard_grouping none     # each keyboard device is fully independent
}
```
