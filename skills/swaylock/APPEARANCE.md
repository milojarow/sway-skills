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
