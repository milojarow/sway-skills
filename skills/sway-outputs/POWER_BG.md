# Power Management and Wallpaper

## Wallpaper / Background

**Image file with scaling mode:**

```
output NAME background /path/to/image.jpg fill
output NAME bg ~/Pictures/wallpaper.png fill
```

`background` and `bg` are aliases.

**All scaling modes:**

| Mode | Behavior |
|---|---|
| `stretch` | Scale image to exactly fill the output, ignoring aspect ratio |
| `fill` | Scale image to fill output, cropping to maintain aspect ratio |
| `fit` | Scale image to fit entirely within output, letterboxing if needed |
| `center` | Center image at its original resolution, no scaling |
| `tile` | Tile the image repeatedly to fill the output |
| `solid_color` | Not a mode for images — use separate `solid_color` form (see below) |

**With fallback color** (covers uncovered pixels when mode leaves gaps, e.g. `fit`, `center`, `tile`):

```
output NAME background ~/Pictures/wallpaper.png fit #1a1a2e
output NAME background ~/Pictures/wallpaper.png center #000000
```

Color must be `#RRGGBB` format. Alpha is not supported.

**Solid color background** (no image):

```
output NAME background #1e1e2e solid_color
output * background #000000 solid_color
```

**Apply same wallpaper to all outputs:**

```
output * background ~/Pictures/wallpaper.jpg fill #000000
```

---

## Using swaybg

Sway uses `swaybg` as the default program for rendering backgrounds. It is invoked automatically when `background` directives are present in the config.

**Override the background program:**

```
swaybg_command swaybg          # default
swaybg_command /path/to/custom-bg-program
swaybg_command -               # disable swaybg entirely (manage bg externally)
```

If you want to manage wallpaper with a tool like `swww` or `wpaperd`, set `swaybg_command -` and launch your tool via `exec` or `exec_always`.

---

## Display Power Management

### power vs dpms

```
output NAME power on|off|toggle    # preferred command
output NAME dpms on|off|toggle     # deprecated alias for power
```

**Key difference from `disable`/`enable`:**

| Command | Workspaces preserved | Windows preserved |
|---|---|---|
| `output NAME power off` | Yes | Yes |
| `output NAME disable` | No | No (reassigned) |

Use `power off` for blanking a display temporarily. Use `disable` only when you want to permanently stop using an output and reclaim its workspaces.

**At runtime:**

```sh
swaymsg output HDMI-A-1 power off
swaymsg output HDMI-A-1 power on
swaymsg output HDMI-A-1 power toggle
```

### Automatic DPMS with swayidle

`swayidle` monitors idle time and runs commands when thresholds are crossed. The canonical pattern for display power management:

```
exec swayidle -w \
    timeout 300  'swaymsg "output * power off"' \
    resume       'swaymsg "output * power on"'  \
    before-sleep 'swaymsg "output * power off"'
```

**Common extended pattern** with screen lock:

```
exec swayidle -w \
    timeout 300  'swaylock -f' \
    timeout 360  'swaymsg "output * power off"' \
    resume       'swaymsg "output * power on"'  \
    before-sleep 'swaylock -f'
```

- `timeout 300` — lock screen after 5 minutes of idle
- `timeout 360` — turn off displays 1 minute after locking
- `resume` — turn displays back on when activity resumes
- `before-sleep` — lock before system suspends (requires `swayidle -w` flag, which waits for the command to finish before allowing sleep)
- Times are in seconds

**Targeting a specific output instead of all:**

```sh
swaymsg "output eDP-1 power off"
```

---

## Disabling an Output at Runtime

Two distinct operations — choose based on whether you want to preserve the workspaces:

```sh
# Blank display, keep workspaces and windows (can restore with power on)
swaymsg output HDMI-A-1 power off

# Remove output entirely, workspaces move to remaining outputs
swaymsg output HDMI-A-1 disable

# Re-enable after disable (workspaces must be manually moved back)
swaymsg output HDMI-A-1 enable
```

**Practical difference:** If you unplug and replug a monitor, sway handles it as a disconnect/reconnect and re-applies config. `power off` is the correct choice for "I want to blank this screen temporarily without disrupting my layout."
