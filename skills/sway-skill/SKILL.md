---
name: sway-skill
description: Use for anything about sway / SwayFX on this machine (the Wayland window manager). Covers window management (spawning, tiling, floating, tabbed, stacking, fullscreen, focus, move, workspaces), config syntax/includes/exec, keybindings and binding modes, SwayFX visual effects (rounded corners, blur, shadows, dim-inactive, layer effects, animations), swaybar/status protocol, swaylock + swayidle, inputs (keyboard/XKB, pointer/libinput, seat), outputs (displays, scaling, wallpaper, DPMS, rendering), swaymsg/IPC, screen sharing / screencast via xdg-desktop-portal-wlr, the swayr window switcher, writing small GTK4 tools for sway (launcher/popup startup cost, app_id via prgname, single-instance locking, GTK4 CSS and text-rendering gotchas), the live palette-theming system, and this machine's custom functionalities (resize/swap/scratchpad modes, screenshots, recording, power menu, clipboard, gamma, emoji picker, lock/idle). This system runs SwayFX 0.6 (sway 1.12 base). Talking to this skill = talking to this machine's own sway. Not for: non-sway tooling on this machine (ssh-tmux, generic shell scripts), other Wayland compositors (Hyprland/river), or X11/i3 specifics that diverge from sway.
metadata:
  priority: 5
  pathPatterns: ["**/sway/config", "**/sway/config.d/**", "**/sway/definitions.d/**", "**/sway/modes/**", "**/sway/scripts/**", "**/sway/themes/**", "**/swaylock/**", "**/swayidle/**", "**/swayimg/config", "**/swayr/config.toml", "**/waybar/**"]
  bashPatterns: ["swaymsg", "swaylock", "swayidle", "swayimg", "swaybg", "swayr", "theme-(selector|toggle|apply-foot|waybar|rofi|wofi|eww)"]
---

# sway-skill

The complete expert on **this machine's window manager**. It runs **SwayFX 0.6** (a fork of sway 1.12 with visual effects), so everything in vanilla sway applies **plus** the FX layer — and this skill also knows this machine's bespoke theming system and custom functionalities.

> **🔰 ACTIVE-SKILL MARKER:** Prefix your reply with 🔰 **only on turns where the work touches the `sway-skill` domain** — sway / SwayFX on this machine: editing `~/.config/sway/`, `swaymsg`, keybind/mode scripts, SwayFX directives, theming — regardless of the layer/project (frontend, backend, a local script — all count); what matters is whether *this turn* touches the domain. On turns that do NOT touch it (typecheck, build, deploy, git ops, editing or curl in other domains), **omit 🔰** even if the skill loaded earlier in the session. If other active skills also apply to the same turn, **stack their emojis** in the prefix.

## Overview

Sway is an i3-compatible Wayland compositor: a **tree of containers** (workspaces → splits → windows) you drive with keybindings and `swaymsg`. SwayFX adds rounded corners, blur, shadows, dim-inactive, layer effects and (0.6+) animations on top. This machine layers a live **palette-theming** system and a set of custom **binding modes + waybar tools** on that base.

When in doubt, the installed man pages are authoritative: `man 5 sway` (config + SwayFX directives), `man 1 sway`, `man swaymsg`, and `man <feature>` for the custom functionalities (see this-system.md).

## Where things live

| Topic | Reference |
|---|---|
| Window management — tiling/floating/tabbed/stacking, fullscreen, focus, move, **workspaces** | [reference/fundamentals.md](reference/fundamentals.md) |
| Keybindings — `bindsym`/`bindcode`, **launching apps (`exec`)**, binding modes, window criteria | [reference/keybindings.md](reference/keybindings.md) |
| Config — syntax, variables, includes, `exec`/daemon, gotchas | [reference/config.md](reference/config.md) |
| **SwayFX effects** — corner_radius, blur, shadows, dim_inactive, layer_effects, animations, checking the running version | [reference/swayfx.md](reference/swayfx.md) |
| IPC — `swaymsg`, protocol, `get_tree`, event subscriptions | [reference/ipc.md](reference/ipc.md) |
| **"What is under the pointer?"** — no `get_cursor` in the IPC, `focus_follows_mouse` fires on crossing not motion, resolving it client-side from GTK + `get_tree` | [reference/pointer-resolution.md](reference/pointer-resolution.md) |
| Inputs — keyboard/XKB, pointer/libinput, seat/multiseat | [reference/inputs.md](reference/inputs.md) |
| Outputs — displays, scaling, rendering, DPMS, wallpaper (swaybg) | [reference/outputs.md](reference/outputs.md) |
| Bar — swaybar config, status JSON protocol, colors | [reference/bar.md](reference/bar.md) |
| **Screen sharing** — xdg-desktop-portal-wlr, the slurp chooser, PipeWire, layer-by-layer diagnosis | [reference/screen-sharing.md](reference/screen-sharing.md) |
| **Writing GTK4 tools for sway** — launcher/popup startup cost, `app_id` via prgname, single-instance, CSS gotchas | [reference/gtk4-tools.md](reference/gtk4-tools.md) |
| **Drag and drop between clients** — file vs link/text as the deciding axis, Chromium/Electron never inserting dropped text, mime traps, reading the drop target at write time, safely erasing what a drop inserted, testing synthetic drags without wrecking a live session, dragging across workspaces | [reference/drag-and-drop.md](reference/drag-and-drop.md) |
| **Proving a visual change renders** — nested headless sway, scripted A/B takes, frame counting, sync-flash alignment | [reference/visual-verification.md](reference/visual-verification.md) |
| **Synthetic input** — wtype vs ydotool, the wtype→slurp SIGSEGV and its repair, unicode typing traps | [reference/synthetic-input.md](reference/synthetic-input.md) |
| **Start/stop toggle scripts** — where a "recording just finished" hook belongs (the starting instance, never the stop branch), guarding with `-s`, testing a `slurp`-driven toggle by stubbing `slurp` on `PATH`, a launch/show/hide toggle needing a `flock` around the launch to survive an impatient double-click, and matching `--app` windows by stable `app_id` suffix instead of the literal string | [reference/toggle-script-hooks.md](reference/toggle-script-hooks.md) |
| **Self-placing windows** — why no `window` event fires for a floating move/resize in place (poll `get_tree` instead), `resize set` being center-anchored, the constant gap/border offset on `move position`, why a self-correcting move must verify instead of trusting one correction, and excluding a self-placer from every other placement daemon | [reference/self-placing-windows.md](reference/self-placing-windows.md) |
| **Stuck pointer button** — a click that stays "held" (rubber-band on just moving the mouse): probing the REAL kernel button state passively with `EVIOCGKEY` (no `get_cursor` in IPC, and injecting a test click moves the operator's real pointer), telling kernel/seat-stuck from client-state-stuck apart | [reference/stuck-pointer-button.md](reference/stuck-pointer-button.md) |
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
- **"An app can't share my screen / the picker cancels itself / can I share just one window?"** → screen-sharing.md (portal chain; a one-click monitor pick is correct, and per-window capture exists — it needs a dmenu chooser, not slurp).
- **Writing a GTK4 launcher/popup for a keybind — slow to appear, `app_id` won't match, CSS silently ignored?** → gtk4-tools.md.
- **"Dragging a file/link between two windows drops nothing"?** → drag-and-drop.md (ask what the *payload* is first: files land in Chromium/Electron, links and text never get inserted no matter the source).
- **Scripting sway / querying state?** → ipc.md (`swaymsg -t get_tree`, events).
- **"Which window is the pointer over?" / a nudge to re-trigger `focus_follows_mouse` does nothing?** → pointer-resolution.md — there is no `get_cursor`; resolve it client-side from the GTK window that still holds focus.
- **"Did that animation / blur / corner_radius actually do anything?"** → visual-verification.md (a `{"success": true}` only means it parsed).
- **"Is the config valid? `sway --validate` came back clean."** → config.md — it returns exit 0 and empty output on unclosed blocks, missing `include` targets and nonexistent commands. A green `--validate` is not evidence; only a real (nested headless) load is.
- **"`Print` / a screenshot binding stopped working, no error"?** → synthetic-input.md — a recent `wtype` call likely SIGSEGV'd the next `slurp`; check exit status (139), not coredump counts, and repair with one `ydotool key` event.
- **"A self-placing widget/panel vanished after launch"?** → self-placing-windows.md — likely parked past the output edge by the constant gap/border offset on `move position`, doubled down by another placement daemon racing the same window.
- **"A click feels stuck down / rubber-band starts from just moving the mouse"?** → stuck-pointer-button.md — probe `EVIOCGKEY` passively instead of injecting a test click; tells kernel/seat-stuck from client-stuck apart.

This machine's custom features each have a man page (`~/.local/share/man/man1/`) — this-system.md is the index; `man <name>` is the full doc.
