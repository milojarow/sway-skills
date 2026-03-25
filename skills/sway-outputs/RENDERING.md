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
