---
name: sway-outputs
description: "Display and monitor configuration for sway including resolution, scaling, positioning, wallpaper, and power management. Use when configuring monitors, setting resolution or refresh rate, arranging a multi-display setup, enabling fractional scaling, setting a desktop background, controlling display power (DPMS), or configuring advanced rendering options like adaptive sync or HDR."
---
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

## Reference Files

- **DISPLAY_CONFIG.md** — resolution, mode, custom modelines, position, rotation, multi-monitor layout, enable/disable
- **RENDERING.md** — scaling, adaptive sync, max render time, tearing, bit depth, color profiles, HDR, subpixel
- **POWER_BG.md** — wallpaper modes, swaybg, DPMS power management, swayidle integration
