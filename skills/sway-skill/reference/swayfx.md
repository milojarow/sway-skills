# SwayFX effects

This system runs **SwayFX 0.5.3** (fork of sway 1.11). Everything in vanilla sway works, **plus** these visual-effect directives (authoritative source on this machine: `man 5 sway`, which the `swayfx` package ships extended). This machine's config uses `corner_radius 15` and a per-window `dim_inactive 0.2`.

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

## Misc
- `titlebar_separator enable|disable` — line between titlebar and content.
- `scratchpad_minimize enable|disable` — integrate scratchpad with window minimize requests.

> When in doubt about a directive or its default on this machine, check `man 5 sway` (the swayfx-extended sway(5)) — it is the source of truth for the installed version.
