# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

This is the **sway-skills** repository — a collection of Claude Code skills for the sway Wayland compositor and its companion tools.

**Repository**: https://github.com/milojarow/sway-skills

**Purpose**: 11 skills covering every aspect of sway — from core config syntax to IPC scripting, keybindings, display configuration, and companion utilities (swaylock, swayidle, swayr, swaybg, swayimg).

## Repository Structure

```
sway-skills/
├── .claude-plugin/        # Claude Code plugin configuration
├── CLAUDE.md              # This file
├── README.md              # Project overview
├── LICENSE                # MIT License
└── skills/                # Individual skill implementations
    ├── sway-bar/          # swaybar config and JSON status protocol
    ├── sway-config/       # Core config syntax, variables, includes
    ├── sway-inputs/       # Keyboard, touchpad, tablet, cursor config
    ├── sway-ipc/          # swaymsg, event subscription, get_tree
    ├── sway-keybindings/  # Bindsym, modes, criteria, layout, workspaces
    ├── sway-outputs/      # Monitors, scaling, wallpaper, DPMS, HDR
    ├── swaybg/            # Desktop background utility
    ├── swayidle/          # Idle management daemon
    ├── swayimg/           # Image viewer for Wayland
    ├── swaylock/          # Screen locking utility
    └── swayr/             # Window switcher and MRU manager
```

## The 11 Skills

### Core sway
1. **sway-config** — Config syntax, file structure, variables, includes, exec/exec_always
2. **sway-keybindings** — Bindsym/bindcode, modes, criteria, layout, workspaces
3. **sway-ipc** — swaymsg commands, event subscription, get_tree parsing
4. **sway-inputs** — Keyboard layout (XKB), touchpad, pointer, tablet, cursor
5. **sway-outputs** — Monitor config, resolution, scaling, positioning, DPMS
6. **sway-bar** — swaybar appearance, JSON protocol, click events, pango markup

### Companion tools
7. **swaylock** — Screen locking, indicator customization, per-output backgrounds
8. **swayidle** — Idle timeouts, lock-before-sleep, resume actions
9. **swayr** — Window switching, MRU order, fuzzy search, workspace management
10. **swaybg** — Wallpaper, solid colors, scaling modes, per-monitor setup
11. **swayimg** — Image viewing, gallery mode, overlay integration

## Skill Activation

Skills activate automatically when queries match their description triggers:
- Editing sway config files → sway-config
- Defining keybindings → sway-keybindings
- Running swaymsg commands → sway-ipc
- Configuring monitors → sway-outputs
- Setting up swaylock → swaylock
