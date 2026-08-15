# sway-skills

**One expert Claude Code skill for this machine's window manager — [SwayFX](https://github.com/WillPower3309/swayfx) 0.6 (a fork of [sway](https://swaywm.org/) 1.12).**

## What is this?

A single skill, `sway-skill`, that makes Claude a complete expert on this machine's sway: window management, config, keybindings, **SwayFX visual effects** (rounded corners, blur, shadows, dim-inactive, layer effects, animations), swaybar, swaylock/swayidle, inputs, outputs, IPC, swayr — plus this machine's **live palette-theming system** and its **custom functionalities** (resize/swap/scratchpad modes, screenshots, recording, power menu, clipboard, gamma, emoji picker, …).

Talking to the skill = talking to this machine's own sway. It consolidates what used to be 11 separate sub-skills into one (no inter-skill trigger competition) with progressive-disclosure reference files.

## Structure

```
skills/sway-skill/
  SKILL.md            # router + overview (SwayFX 0.6)
  reference/
    fundamentals.md   keybindings.md   config.md   swayfx.md
    ipc.md            inputs.md        outputs.md  bar.md
    lock-and-idle.md  images.md        swayr.md
    theming.md        this-system.md
```

A PreToolUse hook auto-injects the skill when you edit sway config / scripts / themes or run `swaymsg` / `swaylock` / etc.

## Install

```
/plugin marketplace add milojarow/sway-skills
/plugin install sway-skills
```

## Requirements

- [SwayFX](https://github.com/WillPower3309/swayfx) (or vanilla sway — the `swayfx.md` reference simply won't apply). Companion tools: swaylock, swayidle, swaybg, swayimg, swayr.
- The custom-functionality docs assume this machine's setup (man pages under `~/.local/share/man/man1/`).

## License

MIT
