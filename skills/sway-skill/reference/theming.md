# Theming — the live palette system

This machine has a **bespoke live color-palette theming system** (documented in `man palette-theming`). One theme switch recolors, in a coordinated way: sway window borders, the **foot terminal (live, no restart)**, waybar, rofi, wofi, the eww widget toolkit, plus GTK, Qt/Kvantum, icon, and cursor themes.

## Switching themes
- **`$mod+t`** → wofi theme picker listing `~/.config/sway/themes/`; calls `theme-selector.sh menu`.
- **waybar `custom/theme` module** — left-click toggles light↔dark (`theme-toggle.sh toggle`); right-click enables/disables automatic solar switching (`theme-toggle.sh auto-toggle`, sunrise/sunset via `geoip.sh`).

## The theme set
The installed themes are exactly the subdirectories of `~/.config/sway/themes/` — discover the current set with `ls ~/.config/sway/themes/` or the `$mod+t` picker. **Don't assume a fixed roster; it grows as themes are added.** Light vs dark is per-theme (not a hardcoded list): read each theme's `theme.conf` `color-scheme` (`prefer-light` / `prefer-dark`) or its `$gtk-theme`.

## What a switch does (`theme-selector.sh` → `apply_theme`)
1. Symlinks the theme's `theme.conf` → `~/.config/sway/definitions.d/theme.conf` (sway color vars + `client.*` decoration rules).
2. Copies its `foot-theme.ini` → `~/.config/foot/`, then `theme-apply-foot.sh` writes **OSC 10/11/4 escape sequences to every `/dev/pts/*`** so running foot terminals recolor instantly (foot has no SIGHUP config reload — OSC is the only live path).
3. Writes `$icon-theme` into `qt6ct.conf`; for catppuccin themes runs `papirus-folders`.
4. `swaymsg reload` → sway re-reads `theme.conf` (borders update) and `config.d/90-enable-theme.conf` applies GTK / icon / cursor / font / Kvantum themes.
5. `theme-{waybar,rofi,wofi,eww}.sh` regenerate their outputs (waybar `theme.css`, rofi `cachyos.rasi`, wofi `style.css`, eww `styles/theme.scss` — eww hot-reloads via filesystem watch).
6. `pkill -SIGUSR2 waybar` (reload CSS) + `pkill -RTMIN+17 waybar` (refresh the theme icon).

## Theme data — `~/.config/sway/themes/<name>/`
- `theme.conf` — `$color0–15` (or catppuccin-named vars), `$background-color`, `$text-color`, `$accent-color`, `$selection-color`, `$gtk-theme`, `$icon-theme`, `$cursor-theme`, `$kvantum-theme`, fonts + `client.*` rules.
- `foot-theme.ini` — 16-color foot palette (includes shared `~/.config/sway/templates/foot.ini`).
- `packages` — required AUR/pacman packages (documentation only).

## Runtime files (auto-generated — do NOT edit or track in git)
`definitions.d/theme.conf` (symlink) · `~/.config/foot/foot-theme.ini` (copy) · `waybar/theme.css` · `rofi/cachyos.rasi` · `wofi/style.css` · `eww/styles/theme.scss` · `~/.config/wob.ini`.

## Scripts — `~/.config/sway/scripts/`
`theme-selector.sh` (orchestrator: `menu` + `status`) · `theme-apply-foot.sh` (OSC live recolor) · `theme-{waybar,rofi,wofi,eww}.sh` (regenerate outputs) · `theme-toggle.sh` (solar light/dark) · `wob.sh` (on-screen volume/brightness bar colors, fed via the `$onscreen_bar` sway var).

## Gotchas
- Foot recolors live (OSC → PTY). GTK apps update instantly via gsettings (GTK4/libadwaita may need a restart).
- **Qt/Kvantum themes and Qt6 icon themes require an app restart** — `kvantummanager --set` / `qt6ct.conf` update on disk but running Qt processes don't reload.
- Cursor theme applies to newly launched apps only.
- The eww SCSS (`theme-eww.sh` → `styles/theme.scss`) defines `$theme-bg/$theme-fg/$theme-accent/$theme-selection`; eww watches and reloads automatically.

> Full per-feature detail: `man palette-theming`.
