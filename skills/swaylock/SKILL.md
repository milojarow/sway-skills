---
name: swaylock
description: "Screen locking utility for Wayland compositors that implements the ext-session-lock-v1 protocol. Use when locking the screen, customizing the lock screen appearance (colors, indicator, images), configuring per-output backgrounds, setting up swaylock with swayidle, using the config file for persistent settings, or scripting lock behavior with signals."
---
# swaylock

swaylock is a screen locking utility for Wayland compositors that implement the ext-session-lock-v1 protocol. It displays a configurable lock screen with a password prompt indicator and supports per-output background images, extensive color theming, keyboard layout display, and programmatic unlock via UNIX signals.

---

## Basic Usage

```bash
# Lock the screen (stays in foreground)
swaylock

# Daemonize — detach from terminal after locking (equivalent to i3lock default)
swaylock -f

# Lock with a background image, scaled to fill
swaylock -i /path/to/image.png -s fill

# Lock with a solid background color (hex, no #)
swaylock -c 1e1e2e

# Lock with image, ignore empty password submissions
swaylock -f -e -i ~/wallpaper.jpg -s fill
```

---

## Key Options

| Flag | Long form | Description |
|------|-----------|-------------|
| `-f` | `--daemonize` | Detach from controlling terminal after locking |
| `-e` | `--ignore-empty-password` | Do not validate empty password submissions |
| `-F` | `--show-failed-attempts` | Show count of failed authentication attempts on indicator |
| `-R <fd>` | `--ready-fd <fd>` | Write a newline to `<fd>` once the session is locked |
| `-C <path>` | `--config <path>` | Use a specific config file instead of the default locations |
| `-u` | `--no-unlock-indicator` | Hide the circular password indicator entirely |
| `-d` | `--debug` | Enable debug output |

### --ready-fd

When the session is locked, swaylock writes a single newline to the given file descriptor. At that point the compositor guarantees no security-sensitive content is visible. This is used by **swayidle -w** to wait for the lock screen to be fully active before suspending.

---

## Background & Image

```bash
# Single image for all outputs
swaylock -i /path/to/bg.png

# Per-output images (output name from `swaymsg -t get_outputs`)
swaylock -i eDP-1:/path/to/laptop.png -i HDMI-A-1:/path/to/external.png

# Path that contains a colon — prefix with another colon
swaylock -i :/path/with:colon/image.png

# Solid color only (no image)
swaylock -c 282a36

# Image with a background color for unfilled areas
swaylock -i ~/bg.png -c 000000 -s fit
```

### Scaling Modes (`-s` / `--scaling`)

| Mode | Description |
|------|-------------|
| `stretch` | Stretch image to fill the output (may distort) |
| `fill` | Scale to fill, cropping if needed (no distortion) |
| `fit` | Scale to fit within output, letterboxing |
| `center` | Center at original resolution, no scaling |
| `tile` | Tile the image across the output |
| `solid_color` | Ignore the image; show only the background color |

`-t` / `--tiling` is a shortcut for `--scaling=tile`.

---

## Indicator Appearance

The unlock indicator is a circular ring with an inner fill. Its color changes based on current state (idle, typing, verifying, wrong password, cleared). See `APPEARANCE.md` for the complete color reference.

### Geometry

| Option | Default | Description |
|--------|---------|-------------|
| `--indicator-radius <r>` | 50 | Radius of the indicator circle in pixels |
| `--indicator-thickness <t>` | 10 | Thickness of the ring in pixels |
| `--indicator-x-position <x>` | centered | Horizontal position of the indicator |
| `--indicator-y-position <y>` | centered | Vertical position of the indicator |
| `--indicator-idle-visible` | off | Keep indicator visible even when idle (not typing) |
| `--no-unlock-indicator` / `-u` | shown | Disable the indicator entirely |

### Font

| Option | Description |
|--------|-------------|
| `--font <font>` | Font family for indicator text |
| `--font-size <size>` | Fixed font size in points |

---

## Keyboard Layout Display

| Flag | Description |
|------|-------------|
| `-k` / `--show-keyboard-layout` | Show current xkb layout name while typing |
| `-K` / `--hide-keyboard-layout` | Force-hide layout even if multiple layouts are configured |
| `-L` / `--disable-caps-lock-text` | Suppress the "CapsLock" text on the indicator |
| `-l` / `--indicator-caps-lock` | Reflect Caps Lock state on the indicator ring color |

---

## Config File

swaylock reads a config file on startup. Checked in order:

1. `$HOME/.swaylock/config`
2. `$XDG_CONFIG_HOME/swaylock/config`
3. `SYSCONFDIR/swaylock/config` (system-wide, e.g. `/etc/swaylock/config`)

A custom path can be passed with `-C`.

### Format Rules

- One option per line
- Use the **long option name** without leading dashes
- Options that take a value require `=`: `ring-color=ff0000`
- Boolean/flag options use just the name: `show-failed-attempts`
- `-C` / `--config` itself is **not** valid inside the config file

### Example Config

```ini
# Background
image=/home/milo/pictures/wallpaper.jpg
scaling=fill
color=1e1e2e

# Behavior
daemonize
ignore-empty-password
show-failed-attempts
indicator-idle-visible

# Indicator geometry
indicator-radius=60
indicator-thickness=8

# Colors — see APPEARANCE.md for all options
ring-color=bd93f9
inside-color=1e1e2ebb
text-color=f8f8f2
key-hl-color=50fa7b
bs-hl-color=ff5555
ring-ver-color=8be9fd
ring-wrong-color=ff5555
```

---

## Signals

| Signal | Effect |
|--------|--------|
| `SIGUSR1` | Unlock the screen and exit immediately |

Useful for scripted unlock (e.g., when a hardware key is pressed or a PAM module triggers it):

```bash
# Unlock programmatically
pkill -SIGUSR1 swaylock
```

---

## Integration with swayidle

The `-f` flag and `--ready-fd` are both important for swayidle integration.

### Basic swayidle lock setup

```bash
swayidle -w \
    timeout 300 'swaylock -f' \
    before-sleep 'swaylock -f'
```

### Coordinated lock-then-suspend with --ready-fd

swayidle's `-w` flag waits for the lock command to signal readiness before running the `resume` command. swaylock signals via `--ready-fd`:

```bash
swayidle -w \
    timeout 300 'swaylock -f' \
    timeout 600 'swaylock -f; systemctl suspend' \
    before-sleep 'swaylock -f'
```

When using `before-sleep` with swayidle `-w`, swayidle passes a file descriptor to swaylock automatically and waits for the lock screen to be fully drawn before the system suspends. This prevents the desktop from being briefly visible on wake.

---

## Practical Examples

```bash
# Minimal: lock with defaults
swaylock

# Lock with image, daemonized, showing failed attempts
swaylock -f -F -i ~/wallpaper.jpg -s fill

# Dark solid color lock, no indicator
swaylock -c 000000 -u

# Per-output backgrounds
swaylock \
    -i eDP-1:/home/milo/pics/laptop-bg.png \
    -i DP-1:/home/milo/pics/desk-bg.png \
    -s fill

# Full themed lock from config file
swaylock -C ~/.config/swaylock/config

# Lock with Dracula theme inline
swaylock -f \
    -c 282a36 \
    --ring-color bd93f9 \
    --inside-color 1e1e2e \
    --key-hl-color 50fa7b \
    --bs-hl-color ff5555 \
    --text-color f8f8f2 \
    --ring-ver-color 8be9fd \
    --inside-ver-color 282a36 \
    --ring-wrong-color ff5555 \
    --inside-wrong-color 282a36 \
    --text-wrong-color ff5555 \
    --separator-color 00000000
```
