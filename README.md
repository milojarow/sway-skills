# sway-skills

**Expert Claude Code skills for the [sway](https://swaywm.org/) Wayland compositor**

## What is this?

This repository contains **11 Claude Code skills** covering the sway window manager and its companion tools — swaylock, swayidle, swayr, swaybg, and swayimg.

### Why These Skills Exist

Configuring sway and its ecosystem involves:
- Complex config syntax with variables, includes, and modes
- IPC protocol for scripting and event-driven automation
- Multiple companion tools with their own config formats
- Wayland-specific concepts (layer-shell, output management, XKB)

These skills teach Claude the entire sway ecosystem so it can help effectively with configuration, scripting, and troubleshooting.

## The 11 Skills

| Skill | Description |
|-------|-------------|
| **sway-config** | Core config syntax, variables, includes, exec/exec_always |
| **sway-keybindings** | Bindsym, modes, window criteria, layout, workspaces |
| **sway-ipc** | swaymsg, event subscription, get_tree, scripting |
| **sway-inputs** | Keyboard layout (XKB), touchpad, pointer, tablet, cursor |
| **sway-outputs** | Monitors, resolution, scaling, wallpaper, DPMS |
| **sway-bar** | swaybar config, JSON status protocol, click events |
| **swaylock** | Screen locking, indicator, per-output backgrounds |
| **swayidle** | Idle timeouts, lock-before-sleep, resume actions |
| **swayr** | Window switching, MRU order, fuzzy search |
| **swaybg** | Desktop background, scaling modes, per-monitor |
| **swayimg** | Image viewer, gallery mode, overlay integration |

## Installation

Add this marketplace in Claude Code:

```
/plugin → Marketplaces → Add Marketplace → milojarow/sway-skills
```

Then install:

```
/plugin → Discover → sway-skills → Install
```

## Requirements

- [sway](https://swaywm.org/) window manager
- Claude Code

## License

MIT
