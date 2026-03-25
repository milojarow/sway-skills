---
name: swaybg
description: Wallpaper and background color utility for Wayland compositors implementing the wlr-layer-shell protocol. Use when setting a desktop background image, applying a solid color background, configuring per-monitor wallpapers, choosing image scaling mode, using swaybg from the command line, or customizing the swaybg_command in sway config.
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
