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

The unlock indicator is a circular ring with an inner fill. Its color changes based on current state (idle, typing, verifying, wrong password, cleared). See `this document` for the complete color reference.

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

# Colors — see this document for all options
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

---

# swaylock Appearance — Complete Color Reference

All color values use the format `rrggbbaa` (hex, no `#`). The alpha channel (`aa`) is optional — omit it for fully opaque. Example: `ff0000` = red, `ff000080` = semi-transparent red.

---

## Indicator State Overview

The circular indicator transitions through these states:

| State | When it occurs |
|-------|----------------|
| **Idle** | Locked, no input yet (indicator hidden unless `--indicator-idle-visible`) |
| **Input / Typing** | User is actively typing a password |
| **Clear** | Password field was cleared (Escape or all backspaced) |
| **Caps Lock** | Caps Lock is active (requires `-l` to affect ring color) |
| **Verifying** | Password submitted, PAM is checking it |
| **Wrong / Invalid** | PAM rejected the password |

---

## Color Options by Component

### Ring (outer arc)

| Option | State | Description |
|--------|-------|-------------|
| `--ring-color` | Idle / typing | Default ring color |
| `--ring-clear-color` | Cleared | Ring color when field is cleared |
| `--ring-caps-lock-color` | Caps Lock active | Ring color when Caps Lock is on |
| `--ring-ver-color` | Verifying | Ring color while PAM is verifying |
| `--ring-wrong-color` | Wrong password | Ring color after failed attempt |

### Inside fill (inner circle)

| Option | State | Description |
|--------|-------|-------------|
| `--inside-color` | Idle / typing | Default inside fill |
| `--inside-clear-color` | Cleared | Inside color when field is cleared |
| `--inside-caps-lock-color` | Caps Lock active | Inside color when Caps Lock is on |
| `--inside-ver-color` | Verifying | Inside color while verifying |
| `--inside-wrong-color` | Wrong password | Inside color after failed attempt |

### Line (separator between inside and ring)

| Option | State | Description |
|--------|-------|-------------|
| `--line-color` | Idle / typing | Default line color |
| `--line-clear-color` | Cleared | Line color when field is cleared |
| `--line-caps-lock-color` | Caps Lock active | Line color when Caps Lock is on |
| `--line-ver-color` | Verifying | Line color while verifying |
| `--line-wrong-color` | Wrong password | Line color after failed attempt |
| `-n` / `--line-uses-inside` | All | Override: line inherits inside color |
| `-r` / `--line-uses-ring` | All | Override: line inherits ring color |

### Text (label inside the indicator)

| Option | State | Description |
|--------|-------|-------------|
| `--text-color` | Idle / typing | Default text color |
| `--text-clear-color` | Cleared | Text color when field is cleared |
| `--text-caps-lock-color` | Caps Lock active | Text color when Caps Lock is on |
| `--text-ver-color` | Verifying | Text color while verifying |
| `--text-wrong-color` | Wrong password | Text color after failed attempt |

### Highlight segments (arc segments on the ring)

| Option | State | Description |
|--------|-------|-------------|
| `--key-hl-color` | Typing | Color of key-press arc segments on the ring |
| `--bs-hl-color` | Backspace | Color of backspace arc segments on the ring |
| `--caps-lock-key-hl-color` | Caps Lock + typing | Key highlight color when Caps Lock is active |
| `--caps-lock-bs-hl-color` | Caps Lock + backspace | Backspace highlight color when Caps Lock is active |
| `--separator-color` | All | Color of gaps between highlight arc segments |

### Layout text box (shown with `-k` / `--show-keyboard-layout`)

| Option | Description |
|--------|-------------|
| `--layout-bg-color` | Background fill of the layout label box |
| `--layout-border-color` | Border of the layout label box |
| `--layout-text-color` | Text color of the keyboard layout name |

### Background

| Option | Description |
|--------|-------------|
| `-c` / `--color` | Solid background color (default: `A3A3A3`, light gray) |

---

## Complete Option Index (alphabetical)

| Option | Default | Notes |
|--------|---------|-------|
| `--bs-hl-color` | — | Backspace highlight segments |
| `--caps-lock-bs-hl-color` | — | Backspace highlight when Caps Lock active |
| `--caps-lock-key-hl-color` | — | Key highlight when Caps Lock active |
| `-c` / `--color` | `A3A3A3` | Solid background color |
| `--font` | — | Font family for indicator text |
| `--font-size` | — | Fixed font size in points |
| `--indicator-idle-visible` | off | Show indicator even when idle |
| `--indicator-radius` | 50 | Indicator circle radius (px) |
| `--indicator-thickness` | 10 | Ring thickness (px) |
| `--indicator-x-position` | centered | Horizontal indicator position |
| `--indicator-y-position` | centered | Vertical indicator position |
| `--inside-caps-lock-color` | — | Inside fill on Caps Lock |
| `--inside-clear-color` | — | Inside fill on clear |
| `--inside-color` | — | Inside fill (idle/typing) |
| `--inside-ver-color` | — | Inside fill on verifying |
| `--inside-wrong-color` | — | Inside fill on wrong password |
| `--key-hl-color` | — | Key press highlight segments |
| `--layout-bg-color` | — | Layout box background |
| `--layout-border-color` | — | Layout box border |
| `--layout-text-color` | — | Layout label text |
| `--line-caps-lock-color` | — | Line on Caps Lock |
| `--line-clear-color` | — | Line on clear |
| `--line-color` | — | Line (idle/typing) |
| `--line-uses-inside` / `-n` | — | Line inherits inside color |
| `--line-uses-ring` / `-r` | — | Line inherits ring color |
| `--line-ver-color` | — | Line on verifying |
| `--line-wrong-color` | — | Line on wrong password |
| `--ring-caps-lock-color` | — | Ring on Caps Lock |
| `--ring-clear-color` | — | Ring on clear |
| `--ring-color` | — | Ring (idle/typing) |
| `--ring-ver-color` | — | Ring on verifying |
| `--ring-wrong-color` | — | Ring on wrong password |
| `--separator-color` | — | Gaps between highlight segments |
| `--text-caps-lock-color` | — | Text on Caps Lock |
| `--text-clear-color` | — | Text on clear |
| `--text-color` | — | Text (idle/typing) |
| `--text-ver-color` | — | Text on verifying |
| `--text-wrong-color` | — | Text on wrong password |

---

## Example Themes

### Dracula

```ini
color=282a36
ring-color=bd93f9
inside-color=282a36cc
line-color=00000000
text-color=f8f8f2
key-hl-color=50fa7b
bs-hl-color=ff5555
separator-color=00000000

ring-clear-color=6272a4
inside-clear-color=282a36cc
line-clear-color=00000000
text-clear-color=6272a4

ring-caps-lock-color=ffb86c
inside-caps-lock-color=282a36cc
line-caps-lock-color=00000000
text-caps-lock-color=ffb86c

ring-ver-color=8be9fd
inside-ver-color=282a36cc
line-ver-color=00000000
text-ver-color=8be9fd

ring-wrong-color=ff5555
inside-wrong-color=282a36cc
line-wrong-color=00000000
text-wrong-color=ff5555
```

### Catppuccin Mocha

```ini
color=1e1e2e
ring-color=cba6f7
inside-color=1e1e2ecc
line-color=00000000
text-color=cdd6f4
key-hl-color=a6e3a1
bs-hl-color=f38ba8
separator-color=00000000

ring-clear-color=89b4fa
inside-clear-color=1e1e2ecc
text-clear-color=89b4fa

ring-caps-lock-color=fab387
inside-caps-lock-color=1e1e2ecc
text-caps-lock-color=fab387

ring-ver-color=89dceb
inside-ver-color=1e1e2ecc
text-ver-color=89dceb

ring-wrong-color=f38ba8
inside-wrong-color=1e1e2ecc
text-wrong-color=f38ba8
```

### Minimal (no visible line, transparent inside)

```ini
color=000000
ring-color=ffffff40
inside-color=00000000
line-uses-ring
text-color=ffffffff
key-hl-color=ffffffff
bs-hl-color=ff000080
separator-color=00000000
ring-ver-color=00ff00
ring-wrong-color=ff0000
```

---

## Color Format Notes

- **`rrggbb`** — 6 hex digits, fully opaque. Example: `ff0000` = red.
- **`rrggbbaa`** — 8 hex digits, with alpha. Example: `ff000080` = 50% transparent red, `00000000` = fully transparent.
- Do **not** include `#`.
- Fully transparent (`00000000`) is useful for `--separator-color` and `--line-color` to make those elements invisible.
- Semi-transparent inside colors (e.g., `1e1e2ecc`) let the background image show through the indicator slightly.

---

# swayidle


swayidle is the idle management daemon for sway and other Wayland compositors. It listens for idle events from the compositor and logind, then executes configured commands — locking the screen, powering off displays, running pre-sleep hooks, and more. Events are defined either as CLI arguments or in a config file using identical syntax.

---

## Synopsis

```bash
swayidle [options] [events...]
```

Using `-w` is almost always correct when `before-sleep` is involved. Without it, the sleep inhibitor is released immediately after spawning the lock command, which may allow the system to sleep before the lock screen is visible.

```bash
# Typical invocation
swayidle -w \
    timeout 300 'swaylock -f -c 000000' \
    timeout 600 'swaymsg "output * power off"' \
        resume 'swaymsg "output * power on"' \
    before-sleep 'swaylock -f -c 000000'
```

## Options

| Flag | Argument | Description |
|------|----------|-------------|
| `-C` | `<path>` | Path to config file. Defaults to `$XDG_CONFIG_HOME/swayidle/config` then `$HOME/.swayidle/config`. |
| `-d` | — | Enable debug output. Useful for troubleshooting event timing. |
| `-h` | — | Print help and exit. |
| `-S` | `<seat-name>` | Specify the seat to use. Defaults to an arbitrary available seat. |
| `-w` | — | Wait for each command to finish before releasing the sleep inhibitor. Critical for `before-sleep`. |

## Events

Events are specified after options, either on the CLI or one per line in the config file.

### `timeout`

```
timeout <seconds> <command> [resume <command>]
```

Runs `<command>` after the session has been idle for `<seconds>`. The optional `resume <command>` runs when activity is detected after the timeout fired.

- Timeouts are counted from the last activity, not from each other.
- Multiple `timeout` entries are independent — all fire when their threshold is met.
- The `resume` keyword must immediately follow its `timeout` line (no other events in between on the CLI).

### `before-sleep`

```
before-sleep <command>
```

Runs before systemd puts the system to sleep. swayidle holds a systemd-logind sleep inhibitor lock while running the command. The system will sleep once the command finishes (with `-w`) or immediately after spawning it (without `-w`).

**Limit:** only delays sleep up to `InhibitDelayMaxSec` as configured in `/etc/systemd/logind.conf` (default: 5 seconds).

### `after-resume`

```
after-resume <command>
```

Runs after logind signals that the system has resumed from sleep.

### `lock`

```
lock <command>
```

Runs when logind signals a session lock (e.g., `loginctl lock-session`).

### `unlock`

```
unlock <command>
```

Runs when logind signals a session unlock.

### `idlehint`

```
idlehint <timeout>
```

Sets `IdleHint` on the logind session after `<timeout>` seconds. Also calls `SetIdleHint(false)` on resume or unlock, signaling to logind (and tools like `loginctl`) that the session is active again.

All commands are executed through a shell.

## The -w Flag

Without `-w`, swayidle spawns the `before-sleep` command and immediately releases the sleep inhibitor. The system can proceed to sleep before the lock screen is fully drawn.

With `-w`, swayidle waits for the command to exit before releasing the inhibitor — ensuring the lock screen is active before the system goes dark.

The matching flag on the swaylock side is `-f` (fork/daemonize). When swaylock forks, it returns immediately, which defeats `-w`. Therefore: **always pair `-w` (swayidle) with `swaylock -f` (swaylock)** — swaylock `-f` does not mean "fork and return"; in this context `-f` makes swaylock run in the foreground (no fork), so swayidle's wait actually works.

> Note: `-w` causes blocking. If a command hangs, swayidle will not process further events until it finishes.

## Config File

Default locations (checked in order):
1. `$XDG_CONFIG_HOME/swayidle/config` (typically `~/.config/swayidle/config`)
2. `$HOME/.swayidle/config`

Syntax is identical to CLI event arguments, one event per line. The `resume` keyword on its own line applies to the preceding `timeout`.

```
# ~/.config/swayidle/config

timeout 300 'swaylock -f -c 000000'
timeout 600 'swaymsg "output * power off"'
resume 'swaymsg "output * power on"'
before-sleep 'swaylock -f -c 000000'
after-resume 'swaymsg "output * power on"'
lock 'swaylock -f -c 000000'
```

## Common Patterns

| Goal | Event + Command |
|------|-----------------|
| Lock screen after idle | `timeout 300 'swaylock -f -c 000000'` |
| Turn off displays after longer idle | `timeout 600 'swaymsg "output * power off"'` |
| Turn displays back on when active | `resume 'swaymsg "output * power on"'` (follows the timeout above) |
| Lock before sleep | `before-sleep 'swaylock -f -c 000000'` (use with `-w`) |
| Restore display after resume from sleep | `after-resume 'swaymsg "output * power on"'` |
| Lock on `loginctl lock-session` | `lock 'swaylock -f -c 000000'` |
| Combined full setup (recommended) | See example below |

### Full setup example

```bash
swayidle -w \
    timeout 300  'swaylock -f -c 000000' \
    timeout 600  'swaymsg "output * power off"' \
        resume   'swaymsg "output * power on"' \
    before-sleep 'swaylock -f -c 000000' \
    after-resume 'swaymsg "output * power on"' \
    lock         'swaylock -f -c 000000'
```

## Signals

| Signal | Behavior |
|--------|----------|
| `SIGUSR1` | Immediately enter idle state (fires all configured timeouts as if they had elapsed). Useful for testing or forcing a lock. |
| `SIGTERM` | Run all pending resume commands, then terminate cleanly. |
| `SIGINT` | Same as SIGTERM. |

Force idle manually:

```bash
pkill -SIGUSR1 swayidle
```

## Integration with systemd

swayidle is typically run as a systemd user service or launched from the Sway config.

### As a systemd user service

```ini
# ~/.config/systemd/user/swayidle.service
[Unit]
Description=Idle manager for Wayland
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/swayidle -w -C %h/.config/swayidle/config

[Install]
WantedBy=graphical-session.target
```

Enable and start:

```bash
systemctl --user enable --now swayidle.service
```

### IdleHint and logind

The `idlehint` event sets logind's `IdleHint` property on the session. This allows logind-aware tools (e.g., `loginctl show-session`) to detect session idleness independently of the compositor. It also enables logind's `IdleAction` (configured in `logind.conf`) to trigger actions like suspend after `IdleActionSec`.

## Gotchas

- **`InhibitDelayMaxSec` limits `before-sleep`**: even with `-w`, swayidle can only delay sleep up to `InhibitDelayMaxSec` (default 5 s in `/etc/systemd/logind.conf`). If the lock command takes longer than this, the system will sleep anyway. Increase this value if needed.
- **`-w` is blocking**: if the command passed to any event hangs, swayidle blocks until it finishes. Ensure commands exit reliably.
- **`swaylock -f` vs daemon mode**: swaylock's `-f` flag means "run in the foreground" (do not fork to background). This is required for `-w` to work correctly — if swaylock were to fork and return immediately, swayidle would release the sleep inhibitor too early.
- **`resume` scope**: on the CLI, `resume` applies to the `timeout` immediately preceding it. In the config file, place `resume` on the line directly after its `timeout`.
- **Multiple `before-sleep` entries**: all `before-sleep` commands run, but they share the same inhibitor window. With `-w`, they run sequentially; without `-w`, they are all spawned immediately.
- **PATH in systemd services**: scripts called by swayidle via systemd will not have `~/.local/bin` or `~/.cargo/bin` in PATH. Use absolute paths or export PATH at the top of called scripts.
