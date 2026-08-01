---
name: sway-skill
description: Use for anything about sway / SwayFX on this machine (the Wayland window manager). Covers window management (spawning, tiling, floating, tabbed, stacking, fullscreen, focus, move, workspaces), config syntax/includes/exec, keybindings and binding modes, SwayFX visual effects (rounded corners, blur, shadows, dim-inactive, layer effects), swaybar/status protocol, swaylock + swayidle, inputs (keyboard/XKB, pointer/libinput, seat), outputs (displays, scaling, wallpaper, DPMS, rendering), swaymsg/IPC, screen sharing / screencast via xdg-desktop-portal-wlr, the swayr window switcher, writing small GTK4 tools for sway (launcher/popup startup cost, app_id via prgname, single-instance locking, GTK4 CSS and text-rendering gotchas), the live palette-theming system, and this machine's custom functionalities (resize/swap/scratchpad modes, screenshots, recording, power menu, clipboard, gamma, emoji picker, lock/idle). This system runs SwayFX 0.5.3 (sway 1.11 base). Talking to this skill = talking to this machine's own sway. Not for: non-sway tooling on this machine (ssh-tmux, generic shell scripts), other Wayland compositors (Hyprland/river), or X11/i3 specifics that diverge from sway.
metadata:
  priority: 5
  pathPatterns: ["**/sway/config", "**/sway/config.d/**", "**/sway/definitions.d/**", "**/sway/modes/**", "**/sway/scripts/**", "**/sway/themes/**", "**/swaylock/**", "**/swayidle/**", "**/swayimg/config", "**/swayr/config.toml", "**/waybar/**"]
  bashPatterns: ["swaymsg", "swaylock", "swayidle", "swayimg", "swaybg", "swayr", "theme-(selector|toggle|apply-foot|waybar|rofi|wofi|eww)"]
---

# sway-skill

The complete expert on **this machine's window manager**. It runs **SwayFX 0.5.3** (a fork of sway 1.11 with visual effects), so everything in vanilla sway applies **plus** the FX layer — and this skill also knows this machine's bespoke theming system and custom functionalities.

> **🔰 ACTIVE-SKILL MARKER:** Prefix your reply with 🔰 **only on turns where the work touches the `sway-skill` domain** — sway / SwayFX on this machine: editing `~/.config/sway/`, `swaymsg`, keybind/mode scripts, SwayFX directives, theming — regardless of the layer/project (frontend, backend, a local script — all count); what matters is whether *this turn* touches the domain. On turns that do NOT touch it (typecheck, build, deploy, git ops, editing or curl in other domains), **omit 🔰** even if the skill loaded earlier in the session. If other active skills also apply to the same turn, **stack their emojis** in the prefix.

## Overview

Sway is an i3-compatible Wayland compositor: a **tree of containers** (workspaces → splits → windows) you drive with keybindings and `swaymsg`. SwayFX adds rounded corners, blur, shadows, dim-inactive, and layer effects on top. This machine layers a live **palette-theming** system and a set of custom **binding modes + waybar tools** on that base.

When in doubt, the installed man pages are authoritative: `man 5 sway` (config + SwayFX directives), `man 1 sway`, `man swaymsg`, and `man <feature>` for the custom functionalities (see this-system.md).

## Where things live

| Topic | Reference |
|---|---|
| Window management — tiling/floating/tabbed/stacking, fullscreen, focus, move, **workspaces** | [reference/fundamentals.md](reference/fundamentals.md) |
| Keybindings — `bindsym`/`bindcode`, **launching apps (`exec`)**, binding modes, window criteria | [reference/keybindings.md](reference/keybindings.md) |
| Config — syntax, variables, includes, `exec`/daemon, gotchas | [reference/config.md](reference/config.md) |
| **SwayFX effects** — corner_radius, blur, shadows, dim_inactive, layer_effects | [reference/swayfx.md](reference/swayfx.md) |
| IPC — `swaymsg`, protocol, `get_tree`, event subscriptions | [reference/ipc.md](reference/ipc.md) |
| Inputs — keyboard/XKB, pointer/libinput, seat/multiseat | [reference/inputs.md](reference/inputs.md) |
| Outputs — displays, scaling, rendering, DPMS, wallpaper (swaybg) | [reference/outputs.md](reference/outputs.md) |
| Bar — swaybar config, status JSON protocol, colors | [reference/bar.md](reference/bar.md) |
| **Screen sharing** — xdg-desktop-portal-wlr, the slurp chooser, PipeWire, layer-by-layer diagnosis | [reference/screen-sharing.md](reference/screen-sharing.md) |
| **Writing GTK4 tools for sway** — launcher/popup startup cost, `app_id` via prgname, single-instance, CSS gotchas | [reference/gtk4-tools.md](reference/gtk4-tools.md) |
| Lock & idle — swaylock (appearance), swayidle | [reference/lock-and-idle.md](reference/lock-and-idle.md) |
| Image viewer — swayimg (viewer + gallery) | [reference/images.md](reference/images.md) |
| Window switcher — swayr (MRU) | [reference/swayr.md](reference/swayr.md) |
| **Live theming** — the palette system ($mod+t), foot/waybar/rofi/wofi/eww recolor | [reference/theming.md](reference/theming.md) |
| **This machine's custom functionalities** — resize/swap/scratchpad, screenshots, recording, power menu, clipboard, gamma, emoji, etc. | [reference/this-system.md](reference/this-system.md) |

## Quick orientation

- **"Float / tile / move windows, switch workspaces?"** → fundamentals.md. **Launch an app or bind a key?** → keybindings.md.
- **"Rounded corners / blur / shadows / dim look?"** → swayfx.md (this is SwayFX, not vanilla sway).
- **"Change the color theme / it recolors everything?"** → theming.md (`$mod+t`).
- **"What does `$mod+r` / `$mod+Shift+r` / `Print` / the power menu do here?"** → this-system.md, then `man <feature>`.
- **"An app can't share my screen / the picker cancels itself?"** → screen-sharing.md (portal chain; output-only selection is by design).
- **Writing a GTK4 launcher/popup for a keybind — slow to appear, `app_id` won't match, CSS silently ignored?** → gtk4-tools.md.
- **Scripting sway / querying state?** → ipc.md (`swaymsg -t get_tree`, events).

This machine's custom features each have a man page (`~/.local/share/man/man1/`) — this-system.md is the index; `man <name>` is the full doc.
