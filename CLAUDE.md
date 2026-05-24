# CLAUDE.md

Guidance for Claude Code when working with this repository.

## Project Overview

**sway-skills** — a single Claude Code skill, `sway-skill`, that is the complete expert on this machine's window manager: **SwayFX 0.5.3** (fork of sway 1.11) plus this machine's theming system and custom functionalities.

**Repository**: https://github.com/milojarow/sway-skills

Consolidated 2026-05-24 from 11 separate sub-skills into one — one broad trigger ("anything sway"), all depth in progressive-disclosure reference files, to avoid inter-sub-skill trigger competition.

## Repository Structure

```
sway-skills/
├── .claude-plugin/       # marketplace.json, plugin.json (v2.0.0)
├── CLAUDE.md  ·  README.md  ·  LICENSE
├── hooks/                # pretooluse-inject.py + hooks.json — auto-injects sway-skill on sway files/commands
└── skills/sway-skill/
    ├── SKILL.md          # router + overview; frontmatter `metadata` drives the inject hook
    └── reference/        # fundamentals, keybindings, config, swayfx, ipc, inputs,
                          # outputs, bar, lock-and-idle, images, swayr, theming, this-system
```

## The skill

### sway-skill (marker 🔰)
Window management (tiling/floating/tabbed/stacking, workspaces, focus/move), config syntax/includes/exec, keybindings + binding modes, **SwayFX effects** (corner_radius / blur / shadows / dim_inactive / layer_effects — authoritative in `man 5 sway`), swaybar + status protocol, swaylock + swayidle, inputs (XKB / libinput / seat), outputs (displays / scaling / DPMS / wallpaper), swaymsg / IPC, swayr, the **palette-theming** system ($mod+t), and this machine's **custom functionalities** (each with a `man <name>` page under `~/.local/share/man/man1/`). System base: SwayFX 0.5.3.

## Updating this skill

After any change to this machine's sway setup (new functionality, theme, FX directive). Reference files hold the depth; SKILL.md is the lean router; its frontmatter `metadata` patterns drive the auto-inject hook. The custom functionalities are sourced from the man pages — keep them in sync. **Keep it public-safe**: no secrets, hostnames, or client names (the non-sway tooling like `ssh-tmux` deliberately stays out of this skill). The git log is the diary.
