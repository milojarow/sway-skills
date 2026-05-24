# Sway Output Configuration


The `output` directive in sway controls everything about physical displays: resolution, refresh rate, position in the global coordinate space, rotation, scaling, wallpaper, power management, and advanced rendering. Multiple options can be chained on a single line or written as a block. Output names are hardware identifiers like `HDMI-A-1` or `eDP-1`; use `swaymsg -t get_outputs` to discover them.

---

## Output Identification

**Finding output names:**

```sh
swaymsg -t get_outputs
```

This returns each connected output's name, make, model, serial, current mode, position, scale, and available modes.

**Matching by name:**

```
output HDMI-A-1 ...          # exact connector name
output eDP-1 ...             # built-in laptop panel
output DP-1 ...              # DisplayPort
output *  ...                # wildcard — matches ALL outputs
output -  ...                # matches the currently focused output (by name)
output -- ...                # matches the currently focused output (by identifier)
```

**Matching by make/model/serial** (useful for outputs that change connector names on reconnect):

```
output "Dell Inc. U2722D 12AB34CD" pos 1920 0
```

The string is `make model serial` separated by single spaces, exactly as reported by `swaymsg -t get_outputs`.

---

## Basic Config Pattern

Options can be written inline (one line) or as a block with braces. Both forms are equivalent.

**Inline:**

```
output HDMI-A-1 mode 1920x1080@60Hz pos 1920 0 scale 1 bg ~/Pictures/wallpaper.jpg fill
```

**Block (recommended for readability):**

```
output HDMI-A-1 {
    mode 1920x1080@60Hz
    position 1920 0
    scale 1
    background ~/Pictures/wallpaper.jpg fill
}
```

**Complete real-world laptop + external monitor example:**

```
# Built-in display — HiDPI panel, 2x scaling
output eDP-1 {
    mode 2560x1600@120Hz
    position 0 0
    scale 2
    background ~/Pictures/wallpaper.jpg fill #000000
}

# External monitor — placed to the right in logical coordinates
# eDP-1 is 2560px wide at scale 2, so logical width = 1280
output DP-1 {
    mode 1920x1080@60Hz
    position 1280 0
    scale 1
    background ~/Pictures/wallpaper.jpg fill #000000
}
```

---

## Common Quick Reference

| Goal | Directive |
|---|---|
| Set resolution | `output NAME mode 1920x1080` |
| Set resolution + refresh rate | `output NAME mode 1920x1080@144Hz` |
| Place display at coordinate | `output NAME position 1920 0` |
| Integer scaling (HiDPI) | `output NAME scale 2` |
| Fractional scaling | `output NAME scale 1.5` |
| Set wallpaper (fill mode) | `output NAME background /path/img.png fill` |
| Solid color background | `output NAME background #1a1a2e solid_color` |
| Disable an output | `output NAME disable` |
| Power off (keeps workspaces) | `output NAME power off` |
| Rotate 90 degrees clockwise | `output NAME transform 90` |
| Enable adaptive sync (VRR) | `output NAME adaptive_sync on` |
| Enable HDR | `output NAME hdr on` |
| All outputs same wallpaper | `output * background /path/img.png fill` |

---

---

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

**Note:** `disable`/`enable` removes the output's workspaces and reassigns windows. For temporarily blanking a display while preserving workspaces, use `power` instead (see this document).

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

---

# Rendering Options

## Scaling

**Integer scaling** (recommended — pixel-perfect, no blurring):

```
output eDP-1 scale 2    # 2560x1600 display behaves as 1280x800 logical
output eDP-1 scale 3
```

**Fractional scaling** (supported but may cause slight visual artifacts):

```
output eDP-1 scale 1.5
output eDP-1 scale 1.25
```

The man page notes: "A fractional scale may be slightly adjusted to match requirements of the protocol." Integer scaling is generally preferred; if text is too small at `scale 2`, consider adjusting font sizes in applications rather than using fractional scaling. Xwayland clients do not support HiDPI — they will appear blurry at scale > 1.

---

## Scale Filter

Controls how application buffers rendered at a lower scale than the output are upscaled (e.g., a 1x app on a 2x HiDPI screen):

```
output eDP-1 scale_filter linear    # smooth/blurry upscaling
output eDP-1 scale_filter nearest   # sharp/blocky upscaling (nearest-neighbor)
output eDP-1 scale_filter smart     # nearest on integer scale, linear otherwise (default)
```

| Filter | Result | Best for |
|---|---|---|
| `linear` | smooth, slightly blurry | general use on fractional scales |
| `nearest` | sharp, pixelated | pixel art, integer scales |
| `smart` | automatic selection | default; good general choice |

---

## Adaptive Sync (VRR)

Enables Variable Refresh Rate — the display refreshes only when a new frame is ready, reducing latency and eliminating tearing during frame rate fluctuations. Known by vendor names FreeSync (AMD) and G-Sync (NVIDIA).

```
output HDMI-A-1 adaptive_sync on
output HDMI-A-1 adaptive_sync off
output HDMI-A-1 adaptive_sync toggle
```

**Note:** Can cause flickering on some hardware/display combinations. Test before committing to config.

---

## Max Render Time

Controls when sway composites the frame relative to the display's next refresh cycle.

```
output HDMI-A-1 max_render_time off   # composite immediately after refresh (default behavior; maximizes compositing budget)
output HDMI-A-1 max_render_time 1     # composite 1ms before refresh (lowest latency)
output HDMI-A-1 max_render_time 4     # composite 4ms before refresh
```

**Tuning for minimum latency:**

1. Run a fullscreen application that renders continuously (e.g., `glxgears`).
2. Set `max_render_time 1`.
3. If frame drops occur, increment by 1 until stable.

**Note:** Only effective on Wayland and DRM backends. For per-application render time, see `max_render_time` in `sway(5)`.

When `allow_tearing yes` is set, it is recommended to also set `max_render_time off`.

---

## Allow Tearing

Allows immediate page flips, presenting frames as soon as they are ready rather than waiting for vblank. This can reduce latency at the cost of visible screen tearing.

```
output HDMI-A-1 allow_tearing yes
output HDMI-A-1 allow_tearing no    # default
```

**Constraints:**

- Only takes effect when a window is **fullscreen** on the output.
- Tearing is only enabled when allowed by **both** the output (`allow_tearing yes` here) and the application (`allow_tearing` in `sway(5)`).
- Recommended pairing: `max_render_time off` for immediate page flips.

---

## Render Bit Depth

Controls the maximum color channel bit depth for rendered frames. Default is 8 bits per channel.

```
output HDMI-A-1 render_bit_depth 8    # default
output HDMI-A-1 render_bit_depth 10   # 10-bit color
output HDMI-A-1 render_bit_depth 6    # 6-bit (rarely useful)
```

**Notes:**

- Higher bit depth requires hardware and software support. Has no effect if unsupported.
- 10-bit improves gradient rendering and screenshot color precision.
- Can break screenshot/screencast tools not updated for non-8-bit depths.
- When `hdr on` is set, `render_bit_depth 10` is implicitly applied unless explicitly set otherwise.
- This command is **experimental** and may be changed or removed.

---

## Color Profiles

**Built-in profiles:**

```
output HDMI-A-1 color_profile gamma22         # default
output HDMI-A-1 color_profile srgb
output HDMI-A-1 color_profile --device-primaries gamma22   # use display's EDID primaries
output HDMI-A-1 color_profile --device-primaries srgb
```

**ICC profile:**

```
output HDMI-A-1 color_profile icc /path/to/display.icc
```

**Constraints on color profiles:**

- Only supported by the **Vulkan renderer**. Has no effect with other renderers.
- ICC profile application may be inaccurate.
- Not compatible with HDR features (`hdr on`).
- Both `color_profile` variants are **experimental**.

---

## HDR

Enables High Dynamic Range output — larger color gamut and brightness range using BT.2020 primaries and the PQ transfer function.

```
output HDMI-A-1 hdr on
output HDMI-A-1 hdr off
output HDMI-A-1 hdr toggle
```

**When HDR is enabled:**

- `render_bit_depth` is implicitly set to 10 unless explicitly configured lower.
- Using less than 10-bit may cause color banding.
- Requires display and renderer support.
- Not compatible with `color_profile` directives.

**SDR content appearance tuning** (used alongside `hdr on`):

```
# These directives are not in the man page but are referenced in sway source;
# usage may vary by sway version — verify with swaymsg -t get_outputs.
output HDMI-A-1 sdr_max_brightness 203    # nits for SDR white (default 203 nits)
output HDMI-A-1 sdr_gamut_wideness 0      # 0.0 = sRGB gamut, 1.0 = wide gamut
```

---

## Subpixel Hinting

Manually overrides the subpixel geometry used for text rendering. Usually auto-detected correctly; only change if text appears blurry or wrongly colored.

```
output HDMI-A-1 subpixel rgb     # most common (horizontal RGB strip, left to right)
output HDMI-A-1 subpixel bgr     # horizontal BGR strip (some Samsung panels)
output HDMI-A-1 subpixel vrgb    # vertical RGB strip (some phone/tablet panels)
output HDMI-A-1 subpixel vbgr    # vertical BGR strip
output HDMI-A-1 subpixel none    # no subpixel hinting (OLED, rotated displays)
```

After changing this via `swaymsg`, some applications must be restarted to apply the new value.

---

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

---

# swaybg


swaybg displays a background image or solid color on all outputs (monitors) of a Wayland session. It works with any compositor that implements the wlr-layer-shell protocol, including sway, Hyprland, and others. In sway specifically, the `output * bg` directive calls swaybg under the hood, but swaybg can also be invoked directly for more control or use outside of sway.

---

## Synopsis & Basic Usage

```bash
swaybg [options...]

# Set a background image with fill scaling on all outputs
swaybg -i /path/to/image.png -m fill

# Set a solid color background
swaybg -c 1e1e2e

# Run in the background (typical usage in autostart)
swaybg -i ~/wallpaper.jpg -m fill &
```

## Options

| Flag | Long form | Argument | Description |
|------|-----------|----------|-------------|
| `-c` | `--color` | `[#]rrggbb` | Set the background color (hex). The `#` prefix is optional. |
| `-i` | `--image` | `<path>` | Set the background image. |
| `-m` | `--mode` | `<mode>` | Scaling mode for the image. Default: `stretch`. |
| `-o` | `--output` | `<name>` | Apply subsequent options to a specific output. Use `*` for all outputs. |
| `-v` | `--version` | — | Print version and exit. |
| `-h` | `--help` | — | Show help message and exit. |

## Scaling Modes

| Mode | Description |
|------|-------------|
| `stretch` | Scales the image to fill the output exactly, ignoring aspect ratio. May distort the image. |
| `fill` | Scales the image to fill the output while preserving aspect ratio. Crops edges if the image and output aspect ratios differ. |
| `fit` | Scales the image to fit entirely within the output while preserving aspect ratio. May leave gaps filled by the background color (`-c`). |
| `center` | Centers the image at its original resolution. Does not scale. Gaps filled by background color. |
| `tile` | Tiles the image at its original resolution, repeating it to fill the output. |
| `solid_color` | Ignores any specified image and displays only the background color set with `-c`. |

`fill` is the most common choice for photos. Pair `fit` or `center` with `-c` to control the letterbox/pillarbox color.

## Per-Output Configuration

Pass `-o <output_name>` before the options that should apply to that output. Options after `-o` apply only to that output until the next `-o` flag. Use `*` to target all outputs.

Get output names with `swaymsg -t get_outputs` or `wlr-randr`.

```bash
# Different wallpaper per monitor
swaybg \
  -o DP-1 -i ~/walls/ultrawide.png -m fill \
  -o HDMI-A-1 -i ~/walls/portrait.png -m fit -c 000000

# One output gets an image, another gets a solid color
swaybg \
  -o DP-1 -i ~/walls/forest.jpg -m fill \
  -o DP-2 -c 1e1e2e -m solid_color
```

## Solid Color Background

Use `-c` alone (no `-i`) for a pure solid color background. The hex value can include or omit the leading `#`.

```bash
swaybg -c 1e1e2e       # Catppuccin Mocha base
swaybg -c "#282828"    # Gruvbox dark bg
```

If both `-i` and `-c` are given with mode `solid_color`, the image is ignored and only the color is shown. With `fit` or `center`, `-c` sets the background behind the unscaled image.

## Integration with sway

### output ... bg syntax (sway config)

The `output * bg` directive is the standard way to set wallpapers in `~/.config/sway/config`. Sway calls swaybg internally to implement it.

```
# sway config
output * bg /path/to/image.png fill
output DP-1 bg /path/to/image.png fill
output HDMI-A-1 bg #1e1e2e solid_color
```

Scaling mode names and color syntax are identical to swaybg's CLI options.

### swaybg_command override

`swaybg_command` tells sway which binary to use when processing `output ... bg` directives. The default is `swaybg`.

```
# sway config — use a custom/patched binary
swaybg_command /usr/local/bin/my-swaybg

# Disable swaybg entirely (manage wallpaper yourself)
swaybg_command -
```

When `swaybg_command -` is set, sway will not launch any wallpaper process, so you manage it entirely via `exec` or an external script.

### Running swaybg directly from sway exec

Useful when you need per-output config that `output ... bg` cannot express, or when using `swaybg_command -`:

```
# sway config
swaybg_command -
exec swaybg -o DP-1 -i ~/walls/main.jpg -m fill -o HDMI-A-1 -c 1e1e2e -m solid_color
```

## Practical Examples

```bash
# Simple fill wallpaper on all outputs
swaybg -i ~/Pictures/wallpaper.jpg -m fill

# Fit image with black letterbox bars
swaybg -i ~/Pictures/wallpaper.jpg -m fit -c 000000

# Tiled texture
swaybg -i ~/Pictures/grain.png -m tile

# Pure solid color (no image)
swaybg -c 2d2d2d

# Per-monitor: main gets image, secondary gets matching color
swaybg -o DP-1 -i ~/walls/photo.jpg -m fill -o DP-2 -c 1a1a2e -m solid_color

# Run in background from a script or exec line
swaybg -i ~/walls/current.png -m fill &
```
