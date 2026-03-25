# swayimg Configuration Reference

The swayimg configuration file is a Lua script. All configuration is done by calling functions on the global `swayimg` table — there are no INI keys or static options.

## Config file locations (searched in order)

1. `$XDG_CONFIG_HOME/swayimg/init.lua`
2. `~/.config/swayimg/init.lua`
3. `$XDG_CONFIG_DIRS/swayimg/init.lua`
4. `/etc/xdg/swayimg/init.lua`

LSP type definitions: `/usr/share/swayimg/swayimg.lua`
Example config: `/usr/share/swayimg/example.lua`

## Quick example

```lua
swayimg.text.set_size(18)
swayimg.text.set_foreground(0xffffffff)
swayimg.text.set_background(0xa0000000)

swayimg.viewer.set_default_scale("optimal")
swayimg.imagelist.enable_recursive(true)
swayimg.imagelist.set_order("alpha")

swayimg.gallery.on_key("Delete", function()
  local image = swayimg.gallery.current_image()
  os.remove(image["path"])
end)
```

## Color format

All colors are specified as 32-bit ARGB hex numbers: `0xAARRGGBB`

Examples:
- `0xffffffff` — opaque white
- `0xff000000` — opaque black
- `0xa0000000` — semi-transparent black (alpha=0xa0)
- `0x00000000` — fully transparent

---

## General functionality

### swayimg.exit
```lua
swayimg.exit(code?: number)
```
Exit from application. `code` defaults to `0`.

### swayimg.set_title
```lua
swayimg.set_title(title: string)
```
Set window title text.

### swayimg.set_status
```lua
swayimg.set_status(status: string)
```
Show a temporary status message in the text layer.

### swayimg.set_mode
```lua
swayimg.set_mode(mode: "viewer"|"slideshow"|"gallery")
```
Switch to the specified mode at runtime.

### swayimg.get_mode
```lua
swayimg.get_mode() -> "viewer"|"slideshow"|"gallery"
```
Get the currently active mode.

### swayimg.get_window_size
```lua
swayimg.get_window_size() -> table  -- { width, height }
```
Get application window size in pixels.

### swayimg.get_mouse_pos
```lua
swayimg.get_mouse_pos() -> table  -- { x, y }
```
Get current mouse pointer coordinates.

### swayimg.enable_antialiasing
```lua
swayimg.enable_antialiasing(enable: boolean)
```
Enable or disable antialiasing for image rendering.

### swayimg.enable_decoration
```lua
swayimg.enable_decoration(enable: boolean)
```
Enable or disable window decoration (title bar, border, buttons).
Requires compositor support for the relevant Wayland protocol.
Default: disabled in Sway, enabled in other compositors.

### swayimg.enable_overlay
```lua
swayimg.enable_overlay(enable: boolean)
```
Enable or disable overlay mode (Sway and Hyprland only).
Creates a floating window matching the focused window's position and size.
Can only be set once. Default: enabled in Sway, disabled elsewhere.

---

## Image list

Controls the list of images being browsed and their order.

### swayimg.imagelist.size
```lua
swayimg.imagelist.size() -> number
```
Get the number of entries in the image list.

### swayimg.imagelist.get
```lua
swayimg.imagelist.get() -> table[]
```
Get all entries in the image list as an array.

### swayimg.imagelist.add
```lua
swayimg.imagelist.add(path: string)
```
Add a file path to the image list.

### swayimg.imagelist.remove
```lua
swayimg.imagelist.remove(path: string)
```
Remove a file path from the image list.

### swayimg.imagelist.mark
```lua
swayimg.imagelist.mark(state?: boolean)
```
Set, clear, or toggle the mark on the currently viewed/selected image.
If `state` is omitted, the mark is toggled.

### swayimg.imagelist.set_order
```lua
swayimg.imagelist.set_order(order: string)
```
Set sort order for the image list.

| Value | Description |
|---|---|
| `"none"` | Unsorted (system-dependent) |
| `"alpha"` | Lexicographic: 1, 10, 2, 20, a, b, c |
| `"numeric"` | Numeric: 1, 2, 3, 10, 100, a, b, c |
| `"mtime"` | Modification time |
| `"size"` | File size |
| `"random"` | Random order |

### swayimg.imagelist.enable_reverse
```lua
swayimg.imagelist.enable_reverse(enable: boolean)
```
Reverse the image list order.

### swayimg.imagelist.enable_recursive
```lua
swayimg.imagelist.enable_recursive(enable: boolean)
```
Recursively load images from subdirectories.

### swayimg.imagelist.enable_adjacent
```lua
swayimg.imagelist.enable_adjacent(enable: boolean)
```
Load adjacent files from the same directory as the opened file.

---

## Text layer

The text layer displays overlaid info (filename, scale, EXIF data, etc.) at the four corners of the window.

### swayimg.text.set_font
```lua
swayimg.text.set_font(name: string)
```
Set the font face name.

### swayimg.text.set_size
```lua
swayimg.text.set_size(size: number)
```
Set font size in pixels.

### swayimg.text.set_padding
```lua
swayimg.text.set_padding(size: number)
```
Set padding from window edges in pixels.

### swayimg.text.set_foreground
```lua
swayimg.text.set_foreground(color: number)
```
Set foreground (text) color in ARGB format.

### swayimg.text.set_background
```lua
swayimg.text.set_background(color: number)
```
Set background color behind text in ARGB format.

### swayimg.text.set_shadow
```lua
swayimg.text.set_shadow(color: number)
```
Set text shadow color in ARGB format.

### swayimg.text.set_overall_timer
```lua
swayimg.text.set_overall_timer(seconds: number)
```
Set timeout in seconds after which the entire text layer auto-hides.

### swayimg.text.set_status_timer
```lua
swayimg.text.set_status_timer(seconds: number)
```
Set timeout in seconds after which the status message auto-hides.

### swayimg.text.show
```lua
swayimg.text.show()
```
Show the text layer and stop any running hide timer.

### swayimg.text.hide
```lua
swayimg.text.hide()
```
Hide the text layer and stop any running timer.

---

## Viewer mode

All viewer functions are under `swayimg.viewer.*`. The slideshow namespace (`swayimg.slideshow.*`) has an identical API — see the Slideshow section for the additional `set_time` function.

### Navigation

#### swayimg.viewer.open
```lua
swayimg.viewer.open(dir: string)
```
Open the next/previous image in the given direction.

| Value | Description |
|---|---|
| `"first"` | First file in image list |
| `"last"` | Last file in image list |
| `"next"` | Next file |
| `"prev"` | Previous file |
| `"next_dir"` | First file in next directory |
| `"prev_dir"` | Last file in previous directory |
| `"random"` | Random file in image list |

#### swayimg.viewer.current_image
```lua
swayimg.viewer.current_image() -> table
```
Get a dictionary with properties of the currently viewed image: `path`, `size`, meta data (EXIF), etc.

### Scale

#### swayimg.viewer.get_scale
```lua
swayimg.viewer.get_scale() -> number
```
Get current scale. `1.0` = 100%.

#### swayimg.viewer.set_abs_scale
```lua
swayimg.viewer.set_abs_scale(scale: number, x?: number, y?: number)
```
Set absolute scale (`1.0` = 100%). Optional `x`/`y` set the zoom center point; defaults to window center.

#### swayimg.viewer.set_fix_scale
```lua
swayimg.viewer.set_fix_scale(scale: string)
```
Set a named scale mode for the current image.

| Value | Description |
|---|---|
| `"optimal"` | 100% or less to fit window |
| `"width"` | Fit image width to window |
| `"height"` | Fit image height to window |
| `"fit"` | Fit entire image in window |
| `"fill"` | Crop to fill window |
| `"real"` | 100% actual size |
| `"keep"` | Same scale as previously viewed image |

#### swayimg.viewer.reset_scale
```lua
swayimg.viewer.reset_scale()
```
Reset scale to the configured default.

#### swayimg.viewer.set_default_scale
```lua
swayimg.viewer.set_default_scale(scale: number|string)
```
Set the default scale applied to newly opened images. Accepts the same named values as `set_fix_scale`, or a numeric absolute value.

### Position

#### swayimg.viewer.get_position
```lua
swayimg.viewer.get_position() -> table  -- { x, y }
```

#### swayimg.viewer.set_abs_position
```lua
swayimg.viewer.set_abs_position(x: number, y: number)
```
Set image position in pixels relative to window.

#### swayimg.viewer.set_fix_position
```lua
swayimg.viewer.set_fix_position(pos: string)
```
Set a named position.

| Value | Description |
|---|---|
| `"center"` | Center of window |
| `"topcenter"` | Top edge, horizontally centered |
| `"bottomcenter"` | Bottom edge, horizontally centered |
| `"leftcenter"` | Left edge, vertically centered |
| `"rightcenter"` | Right edge, vertically centered |
| `"topleft"` | Top-left corner |
| `"topright"` | Top-right corner |
| `"bottomleft"` | Bottom-left corner |
| `"bottomright"` | Bottom-right corner |

#### swayimg.viewer.set_default_position
```lua
swayimg.viewer.set_default_position(pos: string)
```
Set the default position for newly opened images. Same values as `set_fix_position`.

### Transforms

#### swayimg.viewer.flip_vertical / flip_horizontal
```lua
swayimg.viewer.flip_vertical()
swayimg.viewer.flip_horizontal()
```

#### swayimg.viewer.rotate
```lua
swayimg.viewer.rotate(angle: 90|180|270)
```

#### swayimg.viewer.next_frame / prev_frame
```lua
swayimg.viewer.next_frame() -> number   -- returns current frame index
swayimg.viewer.prev_frame() -> number
```
Step through frames of animated images. Also stops animation.

#### swayimg.viewer.animation_stop / animation_resume
```lua
swayimg.viewer.animation_stop()
swayimg.viewer.animation_resume()
```

### Background appearance

#### swayimg.viewer.set_window_background
```lua
swayimg.viewer.set_window_background(bkg: number|"extend"|"mirror"|"auto")
```
Set the window background (the area outside the image).

| Value | Description |
|---|---|
| `0xAARRGGBB` | Solid color |
| `"extend"` | Blurred version of the current image |
| `"mirror"` | Blurred mirrored version of the current image |
| `"auto"` | `extend` or `mirror` depending on image aspect ratio |

#### swayimg.viewer.set_image_background
```lua
swayimg.viewer.set_image_background(color: number)
```
Set solid background color shown behind transparent images. Disables the checkerboard grid.

#### swayimg.viewer.set_image_grid
```lua
swayimg.viewer.set_image_grid(size: number, color1: number, color2: number)
```
Set the checkerboard grid shown behind transparent images.
- `size`: cell size in pixels
- `color1`, `color2`: alternating cell colors in ARGB format

#### swayimg.viewer.set_mark_color
```lua
swayimg.viewer.set_mark_color(color: number)
```
Set the color of the mark icon (shown on marked images).

### Export

#### swayimg.viewer.export
```lua
swayimg.viewer.export(path: string)
```
Export the currently viewed frame to a PNG file.

### Meta info

#### swayimg.viewer.set_meta
```lua
swayimg.viewer.set_meta(key: string, value: string)
```
Add, replace, or remove a meta field for the current image. Pass an empty string to remove.

### Text layer overlay schemes

Text overlay templates can reference fields with `{field}` syntax.

Available fields:
- `{name}` — filename
- `{dir}` — parent directory name
- `{path}` — absolute path
- `{size}` — file size in bytes
- `{sizehr}` — file size human-readable
- `{time}` — modification time
- `{format}` — image format description
- `{scale}` — current scale percentage
- `{list.index}` — current index in image list
- `{list.total}` — total images in list
- `{frame.width}` — current frame width in pixels
- `{frame.height}` — current frame height in pixels
- `{meta.*}` — EXIF/image metadata (e.g. `{meta.Exif.Photo.ExposureTime}`)

#### swayimg.viewer.set_text_tl / set_text_tr / set_text_bl / set_text_br
```lua
swayimg.viewer.set_text_tl(scheme: string[])
swayimg.viewer.set_text_tr(scheme: string[])
swayimg.viewer.set_text_bl(scheme: string[])
swayimg.viewer.set_text_br(scheme: string[])
```
Set the text overlay for each corner (top-left, top-right, bottom-left, bottom-right). Each element in the array is one line.

```lua
-- Example: filename top-left, scale and dimensions bottom-right
swayimg.viewer.set_text_tl({ "{name}" })
swayimg.viewer.set_text_br({ "{scale}%", "{frame.width}x{frame.height}" })
```

### Behavior options

#### swayimg.viewer.enable_freemove
```lua
swayimg.viewer.enable_freemove(enable: boolean)
```
Enable free move mode (allows panning image outside window bounds).

#### swayimg.viewer.enable_loop
```lua
swayimg.viewer.enable_loop(enable: boolean)
```
Enable looping at end/start of image list.

#### swayimg.viewer.set_preload_limit
```lua
swayimg.viewer.set_preload_limit(size: number)
```
Number of images to preload in a background thread.

#### swayimg.viewer.set_history_limit
```lua
swayimg.viewer.set_history_limit(size: number)
```
Number of previously viewed images to keep in memory cache.

### Event bindings

#### swayimg.viewer.on_key
```lua
swayimg.viewer.on_key(key: string, fn: function)
```
Bind a key to a handler. Key format: `"a"`, `"Shift-a"`, `"Ctrl-a"`, `"Alt-a"`, `"Ctrl-Shift-a"`, `"F1"`, `"Escape"`, `"Delete"`, `"space"`, etc.

#### swayimg.viewer.on_mouse
```lua
swayimg.viewer.on_mouse(button: string, fn: function)
```
Bind a mouse button to a handler. Button format: `"MouseLeft"`, `"MouseRight"`, `"MouseMiddle"`, `"Ctrl-MouseLeft"`, etc.

#### swayimg.viewer.bind_drag
```lua
swayimg.viewer.bind_drag(button: string)
```
Bind a mouse button to the image pan/drag operation.

#### swayimg.viewer.on_signal
```lua
swayimg.viewer.on_signal(signal: string, fn: function)
```
Bind a UNIX signal to a handler. `signal` is `"USR1"` or `"USR2"`.

#### swayimg.viewer.on_change_image
```lua
swayimg.viewer.on_change_image(fn: function)
```
Register a callback called whenever a new image is opened.

#### swayimg.viewer.on_window_resize
```lua
swayimg.viewer.on_window_resize(fn: function)
```
Register a callback called whenever the window is resized.

#### swayimg.viewer.bind_reset
```lua
swayimg.viewer.bind_reset()
```
Remove all existing key, mouse, and signal bindings for viewer mode.

---

## Slideshow mode

The slideshow namespace (`swayimg.slideshow.*`) has the same API as viewer, plus one additional function:

### swayimg.slideshow.set_time
```lua
swayimg.slideshow.set_time(seconds: number)
```
Set the interval in seconds before advancing to the next image automatically.

All other slideshow functions (`open`, `current_image`, `get_scale`, `set_abs_scale`, `set_fix_scale`, `set_default_scale`, `get_position`, `set_abs_position`, `set_fix_position`, `set_default_position`, `next_frame`, `prev_frame`, `flip_vertical`, `flip_horizontal`, `rotate`, `animation_stop`, `animation_resume`, `set_window_background`, `set_image_background`, `set_image_grid`, `set_mark_color`, `set_meta`, `export`, `on_change_image`, `on_window_resize`, `on_key`, `on_mouse`, `bind_drag`, `on_signal`, `bind_reset`, `enable_freemove`, `enable_loop`, `set_preload_limit`, `set_history_limit`, `set_text_tl`, `set_text_tr`, `set_text_bl`, `set_text_br`) are identical to their viewer counterparts.

---

## Gallery mode

### swayimg.gallery.select
```lua
swayimg.gallery.select(dir: string)
```
Move the selection to the next thumbnail.

| Value | Description |
|---|---|
| `"first"` | First thumbnail |
| `"last"` | Last thumbnail |
| `"up"` | Thumbnail above |
| `"down"` | Thumbnail below |
| `"left"` | Thumbnail to the left |
| `"right"` | Thumbnail to the right |
| `"pgup"` | Previous page |
| `"pgdown"` | Next page |

### swayimg.gallery.current_image
```lua
swayimg.gallery.current_image() -> table
```
Get a dictionary with properties of the currently selected image: `path`, `size`, etc.

### Thumbnail appearance

#### swayimg.gallery.set_aspect
```lua
swayimg.gallery.set_aspect(aspect: "fit"|"fill"|"keep")
```
| Value | Description |
|---|---|
| `"fit"` | Fit image into a square thumbnail |
| `"fill"` | Crop image to fill a square thumbnail |
| `"keep"` | Adjust thumbnail size to match the image's aspect ratio |

#### swayimg.gallery.get_thumb_size / set_thumb_size
```lua
swayimg.gallery.get_thumb_size() -> number
swayimg.gallery.set_thumb_size(size: number)
```
Get or set thumbnail size in pixels.

#### swayimg.gallery.set_padding_size
```lua
swayimg.gallery.set_padding_size(size: number)
```
Set padding between thumbnails in pixels.

#### swayimg.gallery.set_border_size
```lua
swayimg.gallery.set_border_size(size: number)
```
Set border thickness (in pixels) around the selected thumbnail.

#### swayimg.gallery.set_border_color
```lua
swayimg.gallery.set_border_color(color: number)
```
Set border color for the selected thumbnail (ARGB).

#### swayimg.gallery.set_selected_scale
```lua
swayimg.gallery.set_selected_scale(scale: number)
```
Scale factor applied to the selected thumbnail (`1.0` = normal size).

#### swayimg.gallery.set_selected_color
```lua
swayimg.gallery.set_selected_color(color: number)
```
Background color behind the selected thumbnail (ARGB).

#### swayimg.gallery.set_background_color
```lua
swayimg.gallery.set_background_color(color: number)
```
Background color behind unselected thumbnails (ARGB).

#### swayimg.gallery.set_window_color
```lua
swayimg.gallery.set_window_color(color: number)
```
Window background color (ARGB).

#### swayimg.gallery.set_mark_color
```lua
swayimg.gallery.set_mark_color(color: number)
```
Color of the mark icon shown on marked images (ARGB).

### Cache and preload

#### swayimg.gallery.set_cache_size
```lua
swayimg.gallery.set_cache_size(size: number)
```
Maximum number of decoded thumbnails to keep in memory.

#### swayimg.gallery.enable_preload
```lua
swayimg.gallery.enable_preload(enable: boolean)
```
Enable or disable background preloading of off-screen thumbnails.

#### swayimg.gallery.enable_pstore
```lua
swayimg.gallery.enable_pstore(enable: boolean)
```
Enable or disable persistent thumbnail storage (disk cache). Speeds up reopening large directories.

#### swayimg.gallery.set_pstore_path
```lua
swayimg.gallery.set_pstore_path(path: string)
```
Set a custom directory path for the persistent thumbnail cache.

### Event bindings

#### swayimg.gallery.on_key
```lua
swayimg.gallery.on_key(key: string, fn: function)
```
Bind a key press to a handler.

#### swayimg.gallery.on_mouse
```lua
swayimg.gallery.on_mouse(button: string, fn: function)
```
Bind a mouse button press to a handler.

#### swayimg.gallery.on_signal
```lua
swayimg.gallery.on_signal(signal: string, fn: function)
```
Bind a UNIX signal (`"USR1"` or `"USR2"`) to a handler.

#### swayimg.gallery.on_change_image
```lua
swayimg.gallery.on_change_image(fn: function)
```
Callback fired when the selected image changes.

#### swayimg.gallery.on_window_resize
```lua
swayimg.gallery.on_window_resize(fn: function)
```
Callback fired when the window is resized.

#### swayimg.gallery.bind_reset
```lua
swayimg.gallery.bind_reset()
```
Remove all existing key, mouse, and signal bindings for gallery mode.

---

## Keybinding patterns

### Bind a key in all modes
```lua
for _, mode in ipairs({ swayimg.viewer, swayimg.slideshow, swayimg.gallery }) do
  mode.on_key("q", function() swayimg.exit() end)
end
```

### Reset defaults and define custom bindings from scratch
```lua
swayimg.viewer.bind_reset()
swayimg.viewer.on_key("j", function() swayimg.viewer.open("next") end)
swayimg.viewer.on_key("k", function() swayimg.viewer.open("prev") end)
swayimg.viewer.on_key("q", function() swayimg.exit() end)
swayimg.viewer.bind_drag("MouseLeft")
```

### Delete file from disk in gallery
```lua
swayimg.gallery.on_key("Delete", function()
  local image = swayimg.gallery.current_image()
  os.remove(image["path"])
  swayimg.imagelist.remove(image["path"])
end)
```

### Toggle gallery/viewer with Tab
```lua
swayimg.viewer.on_key("Tab", function()
  swayimg.set_mode("gallery")
end)
swayimg.gallery.on_key("Tab", function()
  swayimg.set_mode("viewer")
end)
```

### Export current frame on keypress
```lua
swayimg.viewer.on_key("Ctrl-s", function()
  local img = swayimg.viewer.current_image()
  local out = img["path"]:gsub("%.%w+$", "_export.png")
  swayimg.viewer.export(out)
  swayimg.set_status("Exported: " .. out)
end)
```
