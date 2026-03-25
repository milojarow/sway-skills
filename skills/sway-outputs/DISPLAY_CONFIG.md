# Display Configuration

## Resolution and Refresh Rate

The `mode` (aliases: `resolution`, `res`) directive sets the pixel dimensions and optionally the refresh rate.

```
output HDMI-A-1 mode 1920x1080
output HDMI-A-1 mode 1920x1080@60Hz
output HDMI-A-1 mode 2560x1440@144Hz
output HDMI-A-1 resolution 1920x1080@60Hz   # same as mode
output HDMI-A-1 res 1920x1080@60Hz          # same as mode
```

Available modes for each output are listed by `swaymsg -t get_outputs` under the `modes` key.

**Custom modes** — use `--custom` for modes not listed by the display:

```
output HDMI-A-1 mode --custom 1920x1080@75Hz
```

Only use `--custom` if you know the display can actually handle the mode.

---

## Custom Modelines

For complete manual timing control (DRM backend only). Generate values with `cvt(1)` or `gtf(1)`.

**Generate a modeline with cvt:**

```sh
cvt 1920 1080 60
# Output: 1920x1080 59.96 Hz (CVT) hsync: 67.16 kHz; pclk: 173.00 MHz
# Modeline "1920x1080_60.00"  173.00  1920 2048 2248 2576  1080 1083 1088 1120 -hsync +vsync
```

**Use in sway config:**

```
output HDMI-A-1 modeline 173.00 1920 2048 2248 2576 1080 1083 1088 1120 -hsync +vsync
```

Format: `modeline <clock_MHz> <hdisplay> <hsync_start> <hsync_end> <htotal> <vdisplay> <vsync_start> <vsync_end> <vtotal> <hsync_polarity> <vsync_polarity>`

Polarity values: `+hsync`, `-hsync`, `+vsync`, `-vsync`

---

## Position

`output NAME position X Y` (alias: `pos`) places the output at coordinates in the global pixel space. The reference point is the top-left corner of the output.

**Important:** When an output has a scale factor, its logical size (used for positioning) is `physical_pixels / scale`. You must account for this when placing adjacent outputs.

```
# Two monitors side by side, same resolution, no scaling
output HDMI-A-1 position 0 0
output DP-1     position 1920 0

# Two monitors stacked vertically
output HDMI-A-1 position 0 0
output DP-1     position 0 1080
```

**Example with scaling** (from the man page):

```
output HDMI1 scale 2
output HDMI1 pos 0 1020    res 3200x1800
output eDP1  pos 1600 0    res 1920x1080
```

- HDMI1 physical size: 3200x1800, scale 2 → logical size: 1600x900
- eDP1 left edge x=1600 = HDMI1 logical width (3200/2)
- HDMI1 top edge y=1020, logical height 900 → bottom at 1020+900=1920
- eDP1 bottom at 0+1920=1920 → bottoms are aligned

**Rule:** `position X Y` always uses logical (post-scale) coordinates.

---

## Rotation / Transform

```
output NAME transform normal         # no rotation (default)
output NAME transform 90             # 90 degrees clockwise
output NAME transform 180            # 180 degrees
output NAME transform 270            # 270 degrees clockwise (= 90 anticlockwise)
output NAME transform flipped        # horizontal flip, no rotation
output NAME transform flipped-90     # flip then 90 degrees clockwise
output NAME transform flipped-180    # flip then 180 degrees
output NAME transform flipped-270    # flip then 270 degrees clockwise
```

**Incremental rotation** (runtime only, not valid in config file):

```sh
swaymsg output HDMI-A-1 transform 90 clockwise      # add 90 to current
swaymsg output HDMI-A-1 transform 90 anticlockwise  # subtract 90 from current
```

Common use case: portrait monitor:

```
output DP-1 {
    mode 1080x1920@60Hz
    transform 270
    position 2560 0
}
```

---

## Disabling and Enabling an Output

```
output HDMI-A-1 disable   # disable output (loses workspaces and windows)
output HDMI-A-1 enable    # re-enable
output HDMI-A-1 toggle    # toggle between enabled and disabled
```

**Note:** `disable`/`enable` removes the output's workspaces and reassigns windows. For temporarily blanking a display while preserving workspaces, use `power` instead (see POWER_BG.md).

**At runtime via swaymsg:**

```sh
swaymsg output HDMI-A-1 disable
swaymsg output HDMI-A-1 enable
```

---

## Full Multi-Monitor Example

Two monitors: a HiDPI internal display and a 1080p external monitor, side by side.

```
# Internal HiDPI display (2560x1600, 2x scale → 1280x800 logical)
output eDP-1 {
    mode 2560x1600@120Hz
    position 0 0
    scale 2
    background ~/Pictures/wallpaper.jpg fill #000000
}

# External 1080p monitor — placed to the right of eDP-1's logical width (1280)
# Vertically centered: eDP-1 logical height = 800, (1080-800)/2 = 140
output HDMI-A-1 {
    mode 1920x1080@60Hz
    position 1280 0
    scale 1
    background ~/Pictures/wallpaper.jpg fill #000000
}
```

To place them so the tops align, both use `position Y=0`. To align their centers, offset the shorter display by `(taller_logical - shorter_logical) / 2`.
