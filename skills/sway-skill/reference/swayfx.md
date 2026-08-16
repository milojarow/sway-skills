# SwayFX effects

This system runs **SwayFX 0.6** (fork of **sway 1.12**, on wlroots 0.20 / scenefx 0.5). Everything in vanilla sway works, **plus** these visual-effect directives (authoritative source on this machine: `man 5 sway`, which the `swayfx` package ships extended). This machine's config uses `corner_radius 15` and a per-window `dim_inactive 0.2`.

> 0.6 rebased the fork from sway 1.11 → 1.12 (wlroots 0.19 → 0.20, scenefx 0.4 → 0.5), added **animations** (below), and refactored the blur node — the refactor only affects configs that actually use `blur`.

## Rounded corners
- `corner_radius <radius>` — round window corners (px). Set globally in config. (This machine: `corner_radius 15`.)
- `smart_corner_radius enable|disable` — skip rounding when a container has a single visible child (single window / tabbed). Default enabled.

## Blur (behind transparent windows)
- `blur enable|disable`
- `blur_xray enable|disable` — blur sees through to the wallpaper, ignoring windows below.
- `blur_ignore_transparent enable|disable`
- `blur_passes <value>` — more passes = stronger/smoother (cost). Typical 2–3.
- `blur_radius <value>` — kernel size.
- `blur_noise <value>` · `blur_brightness <value>` · `blur_contrast <value>` · `blur_saturation <value>` — tune the blurred result.
- Per-window: `for_window [app_id="..."] blur enable`.

## Shadows
- `shadows enable|disable`
- `shadows_on_csd enable|disable` — also draw on client-side-decorated (GTK/CSD) windows.
- `shadow_blur_radius <value>`
- `shadow_color <hex with alpha>` (e.g. `#0000007F`) · `shadow_inactive_color <hex with alpha>`
- `shadow_offset <x offset> <y offset>`

## Dim inactive
- `dim_inactive <value 0.0–1.0>` — dim unfocused windows. Per-window via `for_window [app_id=".*"] dim_inactive 0.2` (this machine dims all inactive windows by 0.2).
- `default_dim_inactive <value>` — global default for every window.
- `dim_inactive_colors.unfocused <hex>` · `dim_inactive_colors.urgent <hex>` — tint of the dim overlay.

## Layer effects (waybar, wofi, notification daemons…)
Apply blur / shadows / corner_radius to **layer-shell surfaces** by namespace:

```
layer_effects "waybar" {
    blur enable;
    blur_xray enable;
    blur_ignore_transparent enable;
    shadows enable;
    corner_radius 6;
}
```

One-line form: `layer_effects <layer-namespace> <effects...>`. Find a surface's namespace via `swaymsg -t get_tree` / the layer-shell tree (see ipc.md).

## Animations (SwayFX 0.6+)
Native animations ship **disabled by default** and are enabled by a single directive:

```
animation_duration_ms 250          # range 0–5000; 0 = off (default), 250 = upstream's suggestion
```

That one setting covers resize, window movement, window open/close, and workspace switching — three separate upstream changes behind one knob, even though the man page only mentions open/close. If nothing animates, the first thing to check is that the directive is present at all — absence, not misconfiguration, is the default state.

### What the knob actually animates — measured inventory

One global knob, but the compositor does **not** animate everything. Measured on 0.6 with the headless frame-counting harness ([visual-verification.md](visual-verification.md)): a fixed choreography, every event repeated, 250 ms vs 0 ms. An animated event produces a burst of ~15 frames at 60 Hz; a non-animated one produces 1–2 isolated frames, indistinguishable from the 0 ms take.

| Action | Animates? | Frames @250 ms | Frames @0 ms |
|---|---|---:|---:|
| Open window | yes | 15 | 1 |
| Close window | yes | 16 | 1 |
| Resize / move (incl. tiled→floating) | yes | 15 | 1 |
| Workspace switch | yes | 15 | 1 |
| Layout change (`layout tabbed`, `toggle split`) | yes | 15–16 | 1–2 |
| **Fullscreen on/off** | **no** | 1–2 | 1–2 |
| **Scratchpad hide/show** | **no** | 1–2 | 1–2 |
| Focus change | no (border repaint only) | 0–2 | 0–1 |

The two surprises: **fullscreen does not animate** despite being the largest geometry change there is, and **layout change does** — it enters through the resize/move path because the containers change geometry.

**Why scratchpad is flat, mechanically.** `move scratchpad` does not unmap the window; it moves it to the hidden `__i3_scratch` workspace. That is neither open/close nor a user workspace switch (the workspace animation is for the user changing workspace, not for moving a container between them), so it enters through no animated path.

Do not confuse this with `scratchpad_minimize enable|disable` (`man 5 sway`) — that governs how app minimize requests are treated, not animation.

> **Measuring one of these yourself: make sure the event does not drag another animatable event with it.** The first `scratchpad show` *does* produce a burst — sway returns the window **floating**, so that first show carries a tiled→floating conversion, and what animated was that geometry change. Run `floating enable` before sending it to the scratchpad and all four scratchpad events go flat, with the burst appearing earlier on the `floating enable` instead. See the compound-event rule in [visual-verification.md](visual-verification.md).

**It is config-or-runtime.** `swaymsg animation_duration_ms 250` applies to the live session (measured: `{"success": true}`) with no reload and no restart — so A/B-ing a duration costs nothing.

### Do NOT set the duration to 0 at runtime as a workaround

The workaround circulating for the 0.6 bug where a workspace comes back **black after leaving fullscreen** is `animation_duration_ms 0`. Applied **live** with `swaymsg`, it makes the damage worse and irreversible — measured on 0.6:

- The block that animates the workspace switch is also the **only** code that returns a workspace's alpha to 1, and the whole block is gated on `animation_duration_ms > 0`.
- Leaving a workspace parks it at alpha 0. That is normal: entering it restores it.
- Setting the duration to 0 does not "turn the animation off" — it turns off the **restorer** and leaves the zeros in place. Every already-faded workspace stays invisible **permanently**, with no recovery path, not even the one the original bug still had.

The same knob is the switch for both the fault and the repair, so turning it off freezes the broken state instead of clearing it.

**Before disabling any effect as a workaround, ask whether that feature is also what repairs the state it leaves behind.** The concrete alert shape: the state in question is a field rewritten on every transition (alpha, position, z-order, visibility flags) and its rewrite path sits behind the same `if` as the feature. Grep the guard before touching the knob.

If it has to be disabled anyway, **edit the config and let the next start come up clean** — that is where the workaround is safe. In a live session, first walk through every affected workspace with the feature still on so the state is left healthy, and disable last.

> Report the dangerous workaround next to the bug, not separately: whoever reads the old issue will copy it. Upstream this went in as a second repro mode (`MODE=runtime-zero`) on `wlrfx/swayfx#569`.

**There is exactly one knob.** No easing/curve, no `for_window … animate`, no per-animation-type duration. Anyone looking for those is looking for something that does not exist in 0.6.

To settle the same question on a *future* version without guessing, ask the binary — config tokens live in it as literals:

```bash
strings $(readlink -f $(command -v sway)) | grep -iE "^animation|animate" | sort -u
```

In 0.6 that returns only `animation_duration_ms` plus its two error strings and `animation_manager.tick`, which is what "one global knob" looks like from the outside.

> A `{"success": true}` from `swaymsg` means the directive parsed — **not** that a pixel moved. To prove a visual directive actually renders, see [visual-verification.md](visual-verification.md).

## What the sway 1.12 base changed under the fork
0.6 inherits upstream sway 1.12, and a few of those changes alter behaviour regardless of any FX directive:

- **An unsupported GPU no longer refuses to start.** Where the compositor used to abort on the proprietary NVIDIA driver, it now starts and shows an informational swaynag. `--unsupported-gpu` / `SWAY_UNSUPPORTED_GPU` still exist, but all they do now is silence the message.
- **`output color_profile srgb` applies the piecewise sRGB transfer function**, not gamma 2.2. Pass `gamma22` for the old behaviour. The effective default did not change.
- **New protocols are advertised**: `ext_workspace_manager_v1`, `xdg_toplevel_tag_manager_v1`, `color_manager_v1`, `wl_fixes`. `ext-workspace-v1` is the one that matters for bars and widgets — it is the standard workspace protocol, so a status bar no longer has to speak sway-specific IPC to track workspaces.
- **HDR10** is available with the Vulkan renderer.
- **Display managers** are now officially supported for starting the session.

## Misc
- `titlebar_separator enable|disable` — line between titlebar and content.
- `scratchpad_minimize enable|disable` — integrate scratchpad with window minimize requests.

## Telling which version is actually RUNNING
Package metadata and the live compositor disagree routinely — ask the binary and the session, never the package manager:

```
swaymsg -t get_version        # what the LIVE session runs: "human_readable" + "sway_original_version"
ldd $(command -v sway) | grep -E 'wlroots|scenefx'   # what the binary is really linked against
```

Two traps, both measured:

- **`pacman -Qi swayfx` lists a stale `Depends On`.** A build linked against `libwlroots-0.20.so` can still declare `wlroots0.19` in its dependency list; the packaging leaves the old dep dangling. Anyone reading only the package metadata concludes the wrong base version. `ldd` on the binary is the answer.
- **Package version ≠ running version.** `pacman -Q swayfx` reports what is on disk; `swaymsg -t get_version` reports what the live session started with. After an upgrade without re-login they differ, and every directive you test is judged by the *running* one.

> When in doubt about a directive or its default on this machine, check `man 5 sway` (the swayfx-extended sway(5)) — it is the source of truth for the installed version.
