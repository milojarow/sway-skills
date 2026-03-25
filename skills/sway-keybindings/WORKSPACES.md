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
