# Window Management in Sway

Window management commands operate on the focused container unless prefixed with a criteria expression. Criteria allow targeting any window by its properties — app ID, class, title, marks, workspace, and more.

---

## Window Criteria Syntax

A criteria expression is placed immediately before a command, enclosed in square brackets:

```
[attribute="value" attribute2="value2"] command
```

All listed attributes must match for the criteria to apply (logical AND). Values are strings; most support PCRE2 regular expressions.

```sway
# Single attribute
[app_id="firefox"] focus

# Multiple attributes (all must match)
[app_id="foot" title="^nvim"] floating enable

# Regex value
[title="[Ss]way"] move workspace 1

# Special token: matches any window
[all] floating disable
```

Find attribute values in practice with:
```bash
swaymsg -t get_tree
```

---

## Available Criteria

| Attribute | Regex | Notes |
|---|---|---|
| `all` | — | Matches every window |
| `app_id` | yes | Wayland app ID (native Wayland apps only) |
| `class` | yes | X11 window class (XWayland only) |
| `instance` | yes | X11 window instance (XWayland only) |
| `title` | yes | Window title |
| `window_role` | yes | X11 WM_WINDOW_ROLE (XWayland only) |
| `window_type` | yes | X11 _NET_WM_WINDOW_TYPE (XWayland only) |
| `workspace` | yes | Name of the workspace the window is on |
| `con_id` | no | Internal sway container ID (numeric) |
| `con_mark` | yes | Window mark (arbitrary label) |
| `floating` | — | Matches floating windows (no value) |
| `tiling` | — | Matches tiling windows (no value) |
| `urgent` | — | `first`, `last`, `latest`, `newest`, `oldest`, `recent` |
| `shell` | yes | Protocol: `"xdg_shell"` or `"xwayland"` |
| `pid` | no | Process ID (numeric) |
| `id` | no | X11 window ID (XWayland only, numeric) |
| `tag` | yes | Wayland tag (Wayland apps only) |
| `sandbox_engine` | yes | Associated sandbox engine |
| `sandbox_app_id` | yes | App ID from sandbox engine |
| `sandbox_instance_id` | yes | Instance ID from sandbox engine |

### Special value: `__focused__`

For attributes that support it (`app_id`, `class`, `instance`, `title`, `shell`, `window_role`, `workspace`, `sandbox_engine`, `sandbox_app_id`, `sandbox_instance_id`), the value `__focused__` matches windows with the same value as the currently focused window:

```sway
# Focus all windows with the same app_id as the current window
[app_id="__focused__"] focus
```

### `window_type` values (XWayland)

`normal`, `dialog`, `utility`, `toolbar`, `splash`, `menu`, `dropdown_menu`, `popup_menu`, `tooltip`, `notification`

---

## Regex in Criteria

Criteria values that support regex use PCRE2 (Perl-compatible). The match is not automatically anchored — use `^` and `$` to anchor:

```sway
# Matches "nvim", "nvim-qt", "neovim" — unanchored
[app_id="nvim"]

# Matches exactly "nvim" only — anchored
[app_id="^nvim$"]

# Case-insensitive with inline flag
[title="(?i)firefox"]

# Title ending with "sway" or "Sway"
[title="[Ss]way$"]
```

---

## Using Criteria with Commands

Criteria can be used inline (ad-hoc) or with `for_window` / `assign`.

```sway
# Inline: act on matching windows right now (via swaymsg or bindsym)
bindsym $mod+Shift+f [floating] focus

# for_window: runs command whenever a matching window is created
for_window [app_id="pavucontrol"]  floating enable, resize set 800 500
for_window [app_id="nm-applet"]    floating enable
for_window [window_type="dialog"]  floating enable
for_window [window_type="splash"]  floating enable, border pixel 0
for_window [title="^Picture-in-Picture$"] floating enable, sticky enable

# assign: move new windows to a workspace automatically
assign [app_id="firefox"]          workspace 2
assign [app_id="org.telegram.*"]   workspace 3
assign [class="Spotify"]           workspace 9

# assign to output instead of workspace
assign [app_id="firefox"] output HDMI-A-1
```

### Multiple commands with `,` vs `;`

- `,` — criteria are retained across the command boundary
- `;` — criteria are reset (next command needs its own criteria or targets focused)

```sway
# Both commands use [app_id="pavucontrol"] criteria
for_window [app_id="pavucontrol"] floating enable, resize set 800 500

# First command uses criteria; second acts on focused window
for_window [app_id="pavucontrol"] floating enable; focus
```

---

## Layout Commands

Controls how containers are arranged in the focused workspace or container.

```sway
# Set layout of focused container
layout splith       # Horizontal split (side by side)
layout splitv       # Vertical split (stacked vertically)
layout stacking     # Stacking: only focused visible, list on top
layout tabbed       # Tabbed: only focused visible, tabs across top
layout default      # Reset to workspace default

# Cycle through layouts
layout toggle split         # Cycles splith <-> splitv
layout toggle               # Cycles stacking -> tabbed -> last split
layout toggle all           # Cycles through every layout

# Custom cycle (specify which layouts to rotate through)
layout toggle splith splitv tabbed
```

### Split commands (shorthand)

```sway
split h         # Split horizontally (or: splith)
split v         # Split vertically (or: splitv)
split toggle    # Toggle (or: splitt)
split none      # Remove split if only child of parent

splith          # Equivalent to: split horizontal
splitv          # Equivalent to: split vertical
splitt          # Equivalent to: split toggle
```

Splitting sets the direction new windows open relative to the current one.

---

## Focus Commands

```sway
# Directional focus
focus left
focus right
focus up
focus down

# Navigate container tree
focus parent        # Focus the parent container
focus child         # Focus last-focused child of focused container

# Cycle through siblings
focus prev          # Previous container in current layout
focus next          # Next container in current layout
focus prev sibling  # Previous sibling (don't auto-focus child)
focus next sibling  # Next sibling

# Toggle between tiling and floating layer
focus mode_toggle

# Focus the last-focused tiling container
focus tiling

# Focus the last-focused floating container
focus floating

# Focus a specific output
focus output HDMI-A-1
focus output up
focus output right
focus output down
focus output left
```

```sway
# Common bindings
bindsym $mod+h     focus left
bindsym $mod+j     focus down
bindsym $mod+k     focus up
bindsym $mod+l     focus right
bindsym $mod+a     focus parent
bindsym $mod+space focus mode_toggle
```

---

## Move Commands

```sway
# Move focused tiling container (direction, ignores px for tiling)
move left
move right
move up
move down

# Move floating container by pixels
move left 20px
move right 20px
move up 20px
move down 20px

# Move to absolute position (floating)
move position 100 200
move position 100px 200px
move position 50ppt 25ppt

# Move to center of workspace (floating)
move position center

# Move to absolute center of all outputs (floating)
move absolute position center

# Move to where the cursor is (floating)
move position cursor

# Move to a workspace
move container to workspace 3
move container to workspace number 3
move container to workspace "workspace name"
move container to workspace next
move container to workspace prev
move container to workspace next_on_output
move container to workspace prev_on_output
move container to workspace back_and_forth
move container to workspace current   # Move to current (useful in for_window)

# Move to an output
move container to output HDMI-A-1
move container to output right
move container to output left
move container to output up
move container to output down

# Move to scratchpad
move container to scratchpad

# Move to a marked container
move container to mark "my-mark"

# Move focused workspace to an output
move workspace to output HDMI-A-1
move workspace to output right
```

```sway
# Common bindings
bindsym $mod+Shift+h move left
bindsym $mod+Shift+j move down
bindsym $mod+Shift+k move up
bindsym $mod+Shift+l move right
bindsym $mod+Shift+1 move container to workspace number 1
```

---

## Floating Windows

```sway
# Enable / disable / toggle floating
floating enable
floating disable
floating toggle

bindsym $mod+Shift+space floating toggle
```

### `floating_modifier`

Hold the modifier and drag with left-click to move floating windows; right-click to resize them. The `inverse` option swaps the buttons.

```sway
floating_modifier $mod normal    # Left = move, Right = resize
floating_modifier $mod inverse   # Left = resize, Right = move
floating_modifier none           # Disable
```

### Floating size limits

```sway
floating_minimum_size 75 x 50        # Default: 75x50
floating_maximum_size 1920 x 1080    # Default: 0x0 (no limit; -1 x -1 removes limit)
```

---

## Resize Commands

```sway
# Grow/shrink in a direction
resize grow   width  10px
resize shrink width  10px
resize grow   height 10px
resize shrink height 10px

# grow/shrink left/right/up/down = shrink/grow in the named direction's space
resize grow   right  10px     # Same as: resize grow width 10px
resize shrink left   10px     # Same as: resize grow width 10px (takes from left)
resize grow   down   10px     # Same as: resize grow height 10px
resize shrink up     10px     # Same as: resize grow height 10px

# Set exact size
resize set width  800px
resize set height 600px
resize set width  800px height 600px

# Tiling containers: use ppt (percentage points of parent)
resize grow   width  5ppt
resize shrink height 5ppt
resize set    width  50ppt
```

Default unit when omitted: `px` for floating, `ppt` for tiling.

---

## Borders

```sway
# Set border style on focused window (runtime command)
border none             # No border, no title bar
border normal           # Border + title bar (default thickness: 2px)
border normal 3         # Border + title bar, 3px border
border pixel            # Border only, no title bar (default: 2px)
border pixel 1          # Border only, 1px
border csd              # Client-side decorations (app draws its own)
border toggle           # Cycle through available styles

# Set defaults for new windows (config command)
default_border normal
default_border pixel 2
default_border none

default_floating_border normal
default_floating_border pixel 2
```

### Gaps

```sway
# Config: set default gaps for new workspaces
gaps inner 8            # Between windows
gaps outer 4            # Between windows and screen edge
gaps outer left 0
gaps outer right 0
gaps outer top 4
gaps outer bottom 4

# Runtime: change gaps for all workspaces or current
gaps inner all set 10
gaps inner current plus 5
gaps inner current minus 5
gaps outer all set 0
gaps inner all toggle 10   # Toggle between 0 and 10

# Per-workspace gaps (config only, before workspace is created)
workspace 1 gaps inner 0
workspace 1 gaps outer 0
```

### Hide edge borders

```sway
hide_edge_borders none              # Default: show all borders
hide_edge_borders vertical          # Hide borders touching vertical screen edges
hide_edge_borders horizontal        # Hide borders touching horizontal screen edges
hide_edge_borders both              # Hide all screen-adjacent borders
hide_edge_borders smart             # Hide borders when only one window on workspace
hide_edge_borders smart_no_gaps     # Same as smart, also removes gaps
```

---

## Other Window Commands

### kill

```sway
kill    # Close focused window and all its children
bindsym $mod+Shift+q kill
```

### fullscreen

```sway
fullscreen                  # Toggle fullscreen (same as toggle)
fullscreen toggle           # Toggle on/off for current output
fullscreen enable           # Force fullscreen
fullscreen disable          # Force exit fullscreen
fullscreen toggle global    # Fullscreen across all outputs

bindsym $mod+f fullscreen toggle
```

### sticky

Makes a floating window appear on all workspaces (sticks to the output).

```sway
sticky enable
sticky disable
sticky toggle

# Common use: picture-in-picture
for_window [title="^Picture-in-Picture$"] floating enable, sticky enable
```

### opacity

```sway
opacity 0.9             # Same as: opacity set 0.9
opacity set 0.85        # Set to 85% opacity
opacity plus 0.05       # Increase by 5%
opacity minus 0.05      # Decrease by 5%
```

Range: `0` (fully transparent) to `1` (fully opaque).

### title_format

```sway
# Default: just the window title
title_format "%title"

# Show app ID alongside title (useful for debugging)
for_window [all] title_format "%title (%app_id)"

# Pango markup (requires pango font)
for_window [title="."] title_format "<b>%title</b> (%app_id)"
```

Placeholders: `%title`, `%app_id`, `%class`, `%instance`, `%shell`, `%sandbox_engine`, `%sandbox_app_id`, `%sandbox_instance_id`

### Marks

Marks are named labels that let you target or jump to specific windows.

```sway
# Assign a mark to the focused window
mark "terminal"
mark --add "secondary"     # Add without removing existing marks
mark --toggle "pinned"     # Add if absent, remove if present

# Remove marks
unmark "terminal"
unmark               # Remove all marks from focused window

# Jump to a marked window
[con_mark="terminal"] focus

# Move to a marked container
move container to mark "terminal"
```

### Scratchpad

```sway
# Send focused window to scratchpad (hidden floating pool)
move container to scratchpad

# Show/cycle through scratchpad windows
scratchpad show

# Typical binding
bindsym $mod+Shift+minus move container to scratchpad
bindsym $mod+minus       scratchpad show
```

### inhibit_idle

```sway
# Prevent idle/suspend while this window is focused
inhibit_idle focus

# Prevent idle while visible on any output
inhibit_idle visible

# Prevent idle while fullscreen and visible
inhibit_idle fullscreen

# Prevent idle until window is closed
inhibit_idle open

# Remove idle inhibitor
inhibit_idle none

# Via for_window
for_window [app_id="firefox"] inhibit_idle fullscreen
```
