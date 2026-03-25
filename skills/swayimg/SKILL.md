---
name: swayimg
description: "Image viewer for Wayland with viewer and gallery modes. Use when viewing images from the terminal, browsing a directory of images in gallery mode, configuring swayimg appearance or keybindings, using the sway/Hyprland overlay integration mode, viewing animated GIFs or slideshows, or loading images from pipes."
---
# swayimg

swayimg is an image viewer for Wayland/DRM with Lua-based configuration. It supports a wide range of formats (JPEG, PNG, GIF, WebP, HEIF, AVIF, TIFF, SVG, RAW, EXR, BMP, QOI, and more), offers both viewer and gallery modes, can load images from files or pipes, and integrates with Sway and Hyprland to display images as an overlay above the currently focused window — giving the illusion of opening an image directly inside a terminal.

---

## Basic Usage

```
swayimg [OPTIONS]... [FILE]...
```

View specific files:
```bash
swayimg photo.jpg logo.png
```

View from a pipe (use `-` as the filename):
```bash
wget -qO- https://example.com/image.png | swayimg -
```

Load from external commands with the `exec://` prefix:
```bash
swayimg "exec://wget -qO- https://example.com/img.png" \
        "exec://curl -so- https://example.com/img2.png"
```

Browse all images in a directory (pass the directory as the argument):
```bash
swayimg /path/to/photos/
```

Open in gallery mode immediately:
```bash
swayimg --gallery /path/to/photos/
```

## Modes

swayimg has three modes:

| Mode | Description |
|---|---|
| **viewer** | Default mode. Displays one image at a time with zoom/pan/rotate. |
| **gallery** | Grid of thumbnails. Navigate with arrow keys, open selected image by pressing Enter or switching to viewer mode. |
| **slideshow** | Auto-advances through images at a configurable interval. |

Switch modes at runtime via keybinding (default: `g` toggles gallery/viewer) or programmatically:
```lua
swayimg.set_mode("gallery")   -- switch to gallery
swayimg.set_mode("viewer")    -- switch to viewer
swayimg.set_mode("slideshow") -- switch to slideshow
```

## Sway Integration

In Sway, overlay mode is **enabled by default**. swayimg creates a floating window with the same position and size as the currently focused window, so the image appears directly inside whatever terminal window is active.

- In Hyprland, overlay mode is available but must be enabled manually.
- On other compositors, overlay mode is disabled by default.

To control overlay mode from config:
```lua
swayimg.enable_overlay(true)   -- enable (Sway default)
swayimg.enable_overlay(false)  -- disable (shows normal window)
```

Window decoration (title bar, border, buttons) is disabled by default in Sway and enabled on other compositors:
```lua
swayimg.enable_decoration(false)
```

## Key CLI Options

| Option | Description |
|---|---|
| `--gallery` | Start in gallery mode |
| `--slideshow` | Start in slideshow mode |
| `--recursive` | Recursively load images from directories |
| `--order=ORDER` | Sort order: `none`, `alpha`, `numeric`, `mtime`, `size`, `random` |
| `--reverse` | Reverse the image list order |
| `--scale=SCALE` | Initial scale: `optimal`, `fit`, `fill`, `width`, `height`, `real`, `keep` |
| `--no-overlay` | Disable Sway/Hyprland overlay mode |
| `-` | Read image from stdin (pipe) |

## Navigation Keybindings

These are the defaults set in the built-in Lua configuration. All can be rebound.

### Viewer mode

| Key | Action |
|---|---|
| `Arrow keys` / `hjkl` | Pan image |
| `PageUp` / `PageDown` | Previous / next image |
| `Backspace` / `Space` | Previous / next image |
| `Home` / `End` | First / last image |
| `+` / `=` | Zoom in |
| `-` | Zoom out |
| `0` | Reset zoom to default |
| `1` ... `9` | Set zoom to 10%...90% (or 100%...900% with Shift) |
| `w` | Fit to window width |
| `h` | Fit to window height (note: conflicts with vim-left if rebound) |
| `f` | Toggle fullscreen |
| `r` | Rotate 90 degrees clockwise |
| `Shift-r` | Rotate 90 degrees counter-clockwise |
| `m` | Flip horizontal |
| `Shift-m` | Flip vertical |
| `a` | Toggle animation (GIF/animated images) |
| `s` | Toggle slideshow mode |
| `g` | Switch to gallery mode |
| `i` | Toggle info overlay (text layer) |
| `Escape` / `q` | Quit |
| `Delete` | Remove current image from list |
| `MouseLeft` drag | Pan image |
| `MouseScrollUp/Down` | Zoom in/out |

### Gallery mode

| Key | Action |
|---|---|
| `Arrow keys` / `hjkl` | Navigate thumbnails |
| `Enter` / `MouseLeft` | Open selected image in viewer mode |
| `PageUp` / `PageDown` | Previous / next page of thumbnails |
| `Home` / `End` | First / last thumbnail |
| `+` / `-` | Increase / decrease thumbnail size |
| `f` | Toggle fullscreen |
| `Escape` / `q` | Quit |

## Configuration

The config file is a Lua script. swayimg searches for it in this order:

1. `$XDG_CONFIG_HOME/swayimg/init.lua`
2. `~/.config/swayimg/init.lua`
3. `$XDG_CONFIG_DIRS/swayimg/init.lua`
4. `/etc/xdg/swayimg/init.lua`

An example config is installed at `/usr/share/swayimg/example.lua`. The Lua type definitions for LSP support are at `/usr/share/swayimg/swayimg.lua`.

All configuration is done by calling functions on the `swayimg` global table. There are no INI keys or TOML values — just Lua function calls:

```lua
-- Set font size and text colors
swayimg.text.set_size(18)
swayimg.text.set_foreground(0xffffffff)
swayimg.text.set_background(0xa0000000)
swayimg.text.set_shadow(0x80000000)

-- Set default scale mode
swayimg.viewer.set_default_scale("optimal")

-- Enable recursive directory loading
swayimg.imagelist.enable_recursive(true)

-- Sort images by modification time
swayimg.imagelist.set_order("mtime")

-- Custom keybinding in viewer
swayimg.viewer.on_key("Ctrl-d", function()
  local img = swayimg.viewer.current_image()
  os.remove(img["path"])
  swayimg.imagelist.remove(img["path"])
  swayimg.viewer.open("next")
end)

-- Custom keybinding in gallery
swayimg.gallery.on_key("Delete", function()
  local image = swayimg.gallery.current_image()
  os.remove(image["path"])
end)
```

Key binding format: `"Key"`, `"Shift-Key"`, `"Ctrl-Key"`, `"Alt-Key"`, `"Ctrl-Alt-Key"`, etc.
Mouse binding format: `"MouseLeft"`, `"MouseRight"`, `"MouseMiddle"`, `"Ctrl-MouseLeft"`, etc.

## Slideshow

Start in slideshow mode from the CLI:
```bash
swayimg --slideshow /path/to/photos/
```

Configure the interval and behavior in Lua:
```lua
-- Advance every 5 seconds
swayimg.slideshow.set_time(5)

-- Set scale for slideshow
swayimg.slideshow.set_default_scale("fill")

-- Enable looping
swayimg.slideshow.enable_loop(true)

-- Randomize order
swayimg.imagelist.set_order("random")
```

Switch into slideshow mode from viewer with the default `s` keybinding, or programmatically:
```lua
swayimg.viewer.on_key("s", function()
  swayimg.set_mode("slideshow")
end)
```
