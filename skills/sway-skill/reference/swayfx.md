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
animation_duration_ms 250
```

That one setting covers resize, window movement, window open/close, and workspace switching. If nothing animates, the first thing to check is that the directive is present at all — absence, not misconfiguration, is the default state.

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
