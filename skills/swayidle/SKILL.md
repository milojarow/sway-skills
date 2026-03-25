---
name: swayidle
description: Idle management daemon for sway and Wayland compositors. Use when configuring screen locking after inactivity, turning off displays when idle, running commands before system sleep, setting up resume actions, configuring swayidle via config file, or troubleshooting idle behavior with the -d flag.
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
