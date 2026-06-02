# This system's custom sway functionalities

This machine has custom sway/waybar functionalities, each with its own man page (`man <name>` for the full, authoritative doc). Know they exist, their keybinds, and what they do. (Theming has its own reference — see [theming.md](theming.md).)

These live under `~/.config/sway/` (`scripts/`, `modes/`, `config.d/`) and their waybar counterparts under `~/.config/waybar/`.

## Window binding modes
| Feature | Enter | What it does |
|---|---|---|
| **resize** | `$mod+r` | Resize focused window (`←↓↑→` fine = 10px, `Shift+arrow` coarse = 50px) + adjust the workspace inner gap (`+`/`-`). `man resize` |
| **swap** | `$mod+Ctrl+w` | Two-step window-position swap: phase 1 navigate to mark a target, phase 2 swap the two windows. `man swap` |
| **scratchpad** | `$mod+Shift+minus` send · `$mod+minus` show/cycle | Hidden window storage; waybar indicator refreshed via `SIGRTMIN+7`. `man scratchpad` |

## Capture
| Feature | Enter | What it does |
|---|---|---|
| **screenshots** | `Print` (mode) | `p` = region (frozen screen + slurp → swappy), `o` = whole output → swappy, `Shift+p` = region → upload to x0.at (URL to clipboard + notification). `man screenshots` |
| **recording** | `$mod+Shift+r` (mode) | `r` = region, no audio (`.webm`, VP8); `Shift+r` = region + mic (`.mp4`). Bar indicator while recording. `man recording` |

## Power / session
| Feature | Enter | What it does |
|---|---|---|
| **shutdown** (power menu) | `$mod+Shift+e` or `XF86PowerOff` | Mode menu: `l` lock, logout, reboot, suspend, shutdown. `man shutdown` |
| **lock-screen** | `$mod+x` (immediate) · shutdown menu `l` / `u` (`u` = secure-suspend) | Screenshot + blur background, swaylock, idle/suspend coordination. `man lock-screen` |
| **lid-handling** | (event-driven) | Lid open/close handling for sway on this machine's laptop. `man lid-handling` |

## Waybar indicators / toggles
| Feature | Trigger | What it does |
|---|---|---|
| **clipboard-functionality** | `$mod+Shift+p` | Persistent clipboard history browser (GTK app): per-row clickable pin, multi-select delete (shift/ctrl+click + Del), Enter/double-click to copy. `man clipboard-functionality` |
| **do-not-disturb** | waybar module | Notification suppression toggle + indicator. `man do-not-disturb` |
| **idle-inhibitor** | waybar module | Idle-inhibit toggle + custom-timeout dialog. `man idle-inhibitor` |
| **gamma-correction** | waybar module | Location-based color-temperature adjustment + indicator. `man gamma-correction` |
| **usb-management** | waybar | USB storage device mount/management. `man usb-management` |
| **window-title** | waybar | Smart focused-window title display. `man window-title` |

## Input
| Feature | Trigger | What it does |
|---|---|---|
| **emoji-picker** | see `man emoji-picker` | Tabbed emoji picker with keyword aliases. `man emoji-picker` |

> The man pages (`~/.local/share/man/man1/`) are the source of truth per feature — when a detail isn't here, `man <name>` has it.
