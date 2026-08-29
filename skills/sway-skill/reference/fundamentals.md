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

#### Half-screen snap for a workspace's ONLY window, without floating it

A lone tiled window always fills its workspace — `resize set width 50ppt` does
nothing because there is no sibling to give the space to, and the sway layout
model has no empty containers to reserve room in. Floating it (`floating
enable` + `resize set` + `move position`) works but is the wrong tool whenever
anything else on the machine also places or remembers floating geometry — two
writers fighting over one window.

The tiled way is to grow an **outer gap of the workspace** on the side meant
to stay empty. The full runtime form:

```sway
gaps inner|outer|horizontal|vertical|top|right|bottom|left  all|current
     set|plus|minus <amount>
```

```sway
gaps right  current plus 930    # window keeps the LEFT half
gaps left   current plus 930    # right half
gaps bottom current plus 510    # top half
gaps top    current plus 510    # bottom half
```

Measured on a 1920x1080 output with `gaps inner 25px` / `gaps outer 5px`
(usable workspace 1860x1020): baseline rect `1860x1020+30+30`,
`gaps right current plus 930` → `930x1020+30+30`. The container stays
`type: "con"` — tiled — so it keeps SwayFX corner_radius/dim_inactive/
animations, and there is no floating state to undo afterward.

Four traps, all measured:

1. **`gaps ... current` only ever addresses the FOCUSED workspace.** There is
   no IPC form that targets another one — `workspace <ws> gaps ...` is
   config-time only. Anything that has to correct a non-focused workspace has
   to wait for a `workspace::focus` event and fix it as it becomes visible.
2. **Real fullscreen ignores gaps entirely.** A container in `fullscreen
   enable` renders at the full output rect no matter what the outer gaps say.
   Leave fullscreen before snapping; the gap survives the round trip
   (disabling fullscreen returns to the snapped rect).
3. **A gap belongs to the WORKSPACE, not the window.** Opening a second window
   while snapped splits *inside* the half. If the feature promises
   "multi-window behaviour is untouched," something has to release the gap on
   `window::new` / `close` / `move` / `floating`.
4. **Undo by recomputing, never by replaying a stored delta.** `sway reload`
   resets gaps to the config defaults; a stored "subtract 930" replayed after
   that drives the outer gap negative and the workspace ends up WIDER than the
   output. Store the pre-snap size instead and subtract
   `stored_full - current_size`, which is naturally 0 once the gap is already
   gone.

`{"success": true}` from a `gaps` command only means it parsed. To confirm the
snap actually happened, read the rect back from `get_tree` and compare it to
the expected `w x h + x + y`.

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

#### A sticky floating window breaks any "is this workspace single-window?" test

Any feature gated on a workspace's window count (snap-to-half, auto-layout,
"hide the bar when only one window," an autotiling heuristic) has to decide
what counts. Counting *leaf windows* — tiled plus floating — looks like the
conservative choice, and it is the one that breaks: `sticky` makes a window
show on every workspace, and sway re-attaches it to whichever workspace is
currently focused. It is therefore present in the focused workspace's
`floating_nodes` at all times. One sticky window (a shelf, a HUD, a pinned
notepad, a picture-in-picture) is enough to make
`count(leaf windows) == 1` false on every workspace, forever — the feature
never fires, with no error and no log line, because the code silently takes
the fall-through branch that runs the original command. The symptom reads as
"my new keybinding does nothing," indistinguishable from a binding that was
never installed.

**The fix: count tiled leaves only, and never let the recursion enter
`.floating_nodes`:**

```sh
jq '[ $ws | recurse(.nodes[]?)
    | select(.type? == "con")
    | select((.nodes|length) == 0 and (.floating_nodes|length) == 0) ] | length'
```

`recurse(.nodes[]?)` from a workspace node never descends into
`.floating_nodes`, so a floating container's own children are excluded too.
Justification, not just convenience: an outer gap and the tiling layout do not
act on a floating window, so it neither occupies the space being freed nor has
any say in whether the operation makes sense — a workspace holding only
floating windows should count as zero and fall through.

**Method note: a nested headless sway cannot surface this.** The nested
instance is a bare sway — no shelf, no HUD, no tray app, none of a real
session's always-on furniture — so a feature that passes every test there can
still do nothing in the real session. When a nested harness says PASS and the
real session says nothing happened, the first suspect is a window that exists
only in the real session: dump the focused workspace's `nodes` AND
`floating_nodes` with `app_id` and `sticky` before touching anything else:

```sh
swaymsg -t get_tree | jq -r '.. | objects | select(.type?=="workspace")
  | select([recurse(.nodes[]?,.floating_nodes[]?)|.focused?==true]|any)
  | {ws:.name,
     tiled:[recurse(.nodes[]?)|select(.type=="con" and (.nodes|length)==0)|.app_id],
     floating:[recurse(.floating_nodes[]?,.nodes[]?)|select(.type=="floating_con")|{app_id,sticky}]}'
```

Running the script itself under `sh -x` in the live session is what actually
names the culprit fastest — a `COUNT=2` in the trace where a separate count
called the same workspace 1 points straight at what's being missed.

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

---

# Workspace Management in Sway

Workspaces are the primary way to organize windows in sway. They live on outputs (monitors) and can be named, numbered, or both. Windows can be assigned to workspaces automatically using `assign` and criteria.

---

## Workspace Switching

```sway
# Switch to a numbered workspace
workspace 1
workspace 3

# Switch by name (quotes required if name contains spaces)
workspace "email"
workspace "1: browser"

# Switch using the "number" keyword
# If workspace with that number exists, use it (regardless of full name)
workspace number 1
workspace number 5

# Navigate relative to current
workspace prev              # Previous workspace (wraps to next output)
workspace next              # Next workspace (wraps to next output)
workspace prev_on_output    # Previous workspace on same output only (wraps)
workspace next_on_output    # Next workspace on same output only (wraps)

# Return to previously active workspace
workspace back_and_forth
```

```sway
# Typical bindings (Super + number)
bindsym $mod+1 workspace number 1
bindsym $mod+2 workspace number 2
bindsym $mod+3 workspace number 3
bindsym $mod+4 workspace number 4
bindsym $mod+5 workspace number 5
bindsym $mod+6 workspace number 6
bindsym $mod+7 workspace number 7
bindsym $mod+8 workspace number 8
bindsym $mod+9 workspace number 9
bindsym $mod+0 workspace number 10

bindsym $mod+Tab         workspace back_and_forth
bindsym $mod+bracketleft  workspace prev
bindsym $mod+bracketright workspace next
```

---

## Named Workspaces

Workspaces can have purely numeric names, purely string names, or a combined `num:name` format. The `num:` prefix is used for ordering.

```sway
# Pure number (name IS the number, used for ordering)
workspace 1

# Pure name (no ordering prefix; ordered by creation time)
workspace "email"
workspace "work"

# Combined: num for ordering, descriptive name for display
workspace "1:browser"
workspace "2:terminal"
workspace "3:email"

# Switch to combined-name workspace
bindsym $mod+1 workspace "1:browser"

# The "number" keyword: find workspace by its numeric prefix
bindsym $mod+1 workspace number 1   # Matches "1", "1:browser", "1:any"
```

### Variable-based naming (recommended pattern)

```sway
set $ws1  "1"
set $ws2  "2"
set $ws3  "3:mail"
set $ws9  "9:music"
set $ws10 "10"

bindsym $mod+1 workspace $ws1
bindsym $mod+3 workspace $ws3
bindsym $mod+Shift+3 move container to workspace $ws3
```

---

## Moving Containers to Workspaces

```sway
# Move to a numbered workspace
move container to workspace 3
move container to workspace number 3

# Move to a named workspace
move container to workspace "email"

# Move to workspaces relative to current
move container to workspace next
move container to workspace prev
move container to workspace next_on_output
move container to workspace prev_on_output

# Move to the previously active workspace
move container to workspace back_and_forth

# Move to the current workspace (useful in for_window to override auto-assign)
move container to workspace current

# Prevent auto-back-and-forth when moving
move --no-auto-back-and-forth container to workspace 2
```

```sway
# Typical bindings
bindsym $mod+Shift+1 move container to workspace number 1
bindsym $mod+Shift+2 move container to workspace number 2
bindsym $mod+Shift+3 move container to workspace number 3
# ... and so on

# Move and follow (switch to the workspace after moving)
bindsym $mod+Shift+1 move container to workspace number 1; workspace number 1
```

---

## Assigning Windows to Workspaces

`assign` routes new windows matching a criteria to a specific workspace or output. It is equivalent to `for_window <criteria> move container to workspace <ws>` but only runs once when the window first opens.

```sway
# assign [criteria] workspace <name or number>
assign [app_id="firefox"]             workspace 2
assign [app_id="foot"]                workspace 1
assign [app_id="org.telegram.desktop"] workspace 3
assign [class="Spotify"]              workspace 9
assign [class="discord"]              workspace 8

# Assign by number keyword (matches workspace by numeric prefix)
assign [app_id="firefox"] workspace number 2

# Named workspace
assign [app_id="thunderbird"] workspace "email"

# Combined name
assign [app_id="firefox"] workspace "2:browser"

# Assign to output instead of workspace
assign [app_id="firefox"] output HDMI-A-1
assign [app_id="foot"]    output eDP-1
```

The `→` character (U+2192) is optional and cosmetic — the following are identical:

```sway
assign [app_id="firefox"] workspace 2
assign [app_id="firefox"] → workspace 2
```

---

## Workspace on Output

Bind a workspace to a specific output so it always opens there. Multiple outputs can be specified; the first available is used.

```sway
# Basic: workspace N lives on output-name
workspace 1 output eDP-1
workspace 2 output HDMI-A-1
workspace 3 output HDMI-A-1

# Multiple outputs (fallback order)
workspace 1 output eDP-1 HDMI-A-1

# Named workspaces
workspace "email" output HDMI-A-1
```

Find output names with:
```bash
swaymsg -t get_outputs
```

This setting only affects new workspaces. To move an existing workspace to a different output:

```sway
# Move focused workspace to an output
move workspace to output HDMI-A-1
move workspace to output right
```

### Per-workspace gaps

```sway
# Set gaps for a specific workspace when it is first created
workspace 1 gaps inner 0
workspace 1 gaps outer 0
workspace "coding" gaps inner 8 outer 4
```

---

## workspace_auto_back_and_forth

When enabled, running the `workspace N` command while already on workspace N switches back to the previously active workspace. Effectively makes every workspace switch a toggle.

```sway
# Enable in config
workspace_auto_back_and_forth yes   # Default: no

# With this enabled:
# You're on ws 1. You press $mod+2 -> go to ws 2.
# You press $mod+2 again -> return to ws 1.
```

To switch without triggering back-and-forth (when the option is on):

```sway
workspace --no-auto-back-and-forth number 2
```

---

## focus_on_window_activation

Controls what happens when an application requests to be focused (urgency hint).

```sway
focus_on_window_activation smart    # Default: focus if visible, else set urgent
focus_on_window_activation urgent   # Set urgent flag (don't steal focus)
focus_on_window_activation focus    # Always steal focus
focus_on_window_activation none     # Do nothing
```

Note: urgency hints are an X11 concept. Native Wayland apps do not support urgency — this primarily applies to XWayland windows.

```sway
# Delay the reset of urgency decoration (so you can see which window triggered)
force_display_urgency_hint 500 ms
```

---

## Renaming Workspaces

```sway
# Rename the focused workspace
rename workspace to "new name"

# Rename a specific workspace by its current name
rename workspace "old name" to "new name"
```

---

## Scratchpad as a Special Workspace

The scratchpad is a hidden workspace. Windows sent there are available globally across all outputs.

```sway
# Send focused window to scratchpad
move container to scratchpad
bindsym $mod+Shift+minus move container to scratchpad

# Show/cycle scratchpad windows (shows one at a time; hides if already shown)
scratchpad show
bindsym $mod+minus scratchpad show

# Target specific scratchpad window by criteria
[app_id="foot" title="^scratchpad$"] scratchpad show
```

---

## Common Multi-Monitor Patterns

```sway
# Two-monitor setup: internal (eDP-1) and external (HDMI-A-1)
# Workspaces 1-5 on primary; 6-10 on secondary
workspace 1  output eDP-1
workspace 2  output eDP-1
workspace 3  output eDP-1
workspace 4  output eDP-1
workspace 5  output eDP-1
workspace 6  output HDMI-A-1
workspace 7  output HDMI-A-1
workspace 8  output HDMI-A-1
workspace 9  output HDMI-A-1
workspace 10 output HDMI-A-1

# Move focused workspace to next output (useful binding)
bindsym $mod+Shift+o move workspace to output right
```

---

# Binding Modes in Sway

Binding modes let you define a completely separate set of keybindings that become active when you enter that mode. While in a non-default mode, only the keys defined for that mode are recognized — everything else is silently ignored. This prevents accidental key conflicts and enables modal workflows similar to Vim.

---

## What are Modes

When sway starts, it is in the `"default"` mode. All keybindings defined at the top level of your config are part of `"default"`. You can define additional named modes and switch into them. Once in a non-default mode, none of the default bindings fire until you explicitly return to `"default"`.

Use cases:
- Resize mode (avoid conflicting with h/j/k/l for focus)
- System mode (lock, logout, reboot behind a second keypress)
- Launcher mode (dedicated keys for specific apps)
- Passthrough mode (send all keypresses to a nested compositor or VM)

---

## Defining a Mode

```sway
mode [--pango_markup] "<mode-name>" {
    bindsym <key> <command>
    bindcode <code> <command>
    # set is also valid inside a mode block
    set $var value
}
```

The `--pango_markup` flag allows the mode name to contain Pango markup, which is displayed in the status bar.

Only `bindsym`, `bindcode`, `bindswitch`, and `set` are valid inside a mode block. Every other command must go outside.

```sway
# Minimal valid mode definition
mode "resize" {
    bindsym h resize shrink width 10px
    bindsym Escape mode "default"
}
```

---

## Mode Switching

### Entering a mode

From within `"default"` (or any other mode), use `mode "<name>"` as the command for a binding:

```sway
bindsym $mod+r mode "resize"
bindsym $mod+Shift+e mode "system"
```

### Exiting a mode

Always define at least two exit keys: `Escape` and `Return`. This matches user expectations and provides a reliable bail-out:

```sway
mode "resize" {
    bindsym h resize shrink width 10px
    bindsym l resize grow width 10px

    bindsym Return mode "default"
    bindsym Escape mode "default"
}
```

You can also exit to a different mode (nested entry), but this is unusual.

---

## Complete Resize Mode Example

The canonical resize mode — supports both vim-style (h/j/k/l) and arrow keys, with pixel and percentage-point variants:

```sway
mode "resize" {
    # Shrink/grow width and height with vim keys
    bindsym h resize shrink width 10px
    bindsym j resize grow height 10px
    bindsym k resize shrink height 10px
    bindsym l resize grow width 10px

    # Same with arrow keys (convenience)
    bindsym Left  resize shrink width 10px
    bindsym Down  resize grow height 10px
    bindsym Up    resize shrink height 10px
    bindsym Right resize grow width 10px

    # Larger steps with Shift held
    bindsym Shift+h resize shrink width 50px
    bindsym Shift+j resize grow height 50px
    bindsym Shift+k resize shrink height 50px
    bindsym Shift+l resize grow width 50px

    # For tiling containers: use ppt (percentage points) instead of px
    # (px is used for floating containers; tiling ignores px and uses ppt)
    # Uncomment to use ppt:
    # bindsym h resize shrink width 5ppt
    # bindsym l resize grow width 5ppt

    # Exit resize mode
    bindsym Return mode "default"
    bindsym Escape mode "default"
    bindsym $mod+r mode "default"
}

bindsym $mod+r mode "resize"
```

Resize command syntax:

```
resize shrink|grow width|height [<amount> [px|ppt]]
resize set [width] <width> [px|ppt] [height] <height> [px|ppt]
```

- `px` — pixels (default for floating windows)
- `ppt` — percentage points (default for tiling windows)
- Amount defaults to 10 if omitted

---

## Named Modes vs Default

`"default"` is the built-in starting mode. The name is literal — the string must be exactly `"default"` to return to it.

```sway
# Correct: returns to the default mode
bindsym Escape mode "default"

# Wrong: creates a new mode named "Default" (capital D)
bindsym Escape mode "Default"
```

You can switch between any two modes, not just to/from default:

```sway
mode "launcher" {
    bindsym b exec firefox; mode "default"
    bindsym t exec foot;    mode "default"
    bindsym Escape mode "default"
}

mode "system" {
    bindsym l exec swaylock; mode "default"
    bindsym Escape mode "default"
}

# Jump from system to launcher (unusual but valid)
mode "system" {
    bindsym Return mode "launcher"
}
```

---

## Practical Mode Patterns

### System mode (lock / logout / reboot)

Shows a mode indicator in the bar. Each action returns to default after executing.

```sway
set $mode_system "System: [l] lock  [e] logout  [s] suspend  [r] reboot"

mode $mode_system {
    bindsym l exec swaylock,                    mode "default"
    bindsym e exec swaymsg exit,                mode "default"
    bindsym s exec systemctl suspend,           mode "default"
    bindsym r exec systemctl reboot,            mode "default"

    bindsym Return mode "default"
    bindsym Escape mode "default"
}

bindsym $mod+Shift+e mode $mode_system
```

Note: use `,` (comma) to chain `mode "default"` after the exec — criteria are retained across `,` so the mode switch happens in the same command sequence.

### Launcher mode (open specific apps)

```sway
set $mode_launch "Launch: [b] browser  [f] files  [t] terminal  [m] music"

mode $mode_launch {
    bindsym b exec firefox,                 mode "default"
    bindsym f exec thunar,                  mode "default"
    bindsym t exec foot,                    mode "default"
    bindsym m exec foot -e ncmpcpp,         mode "default"

    bindsym Return mode "default"
    bindsym Escape mode "default"
}

bindsym $mod+o mode $mode_launch
```

### Passthrough mode (send all keys to nested session)

Define only the exit binding. Every other key passes through unfiltered.

```sway
mode "passthrough" {
    bindsym $mod+Shift+F12 mode "default"
}

bindsym $mod+Shift+F12 mode "passthrough"
```

Useful for: QEMU/KVM, nested Sway/Wayland, VNC sessions.

### Pango markup in mode name (displays in bar)

```sway
mode --pango_markup "<b>Resize</b> | h/j/k/l or arrows | Esc to exit" {
    bindsym h resize shrink width 10px
    bindsym l resize grow width 10px
    bindsym j resize grow height 10px
    bindsym k resize shrink height 10px
    bindsym Return mode "default"
    bindsym Escape mode "default"
}
```

The mode name string (with markup) appears in the sway bar while the mode is active.
