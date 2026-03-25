# swaymsg — Comprehensive Usage Guide

`swaymsg` sends messages to a running sway instance over the IPC socket and
prints the response. It is the primary tool for scripting sway at runtime.

---

## All CLI Options

| Flag | Long form | Description |
|------|-----------|-------------|
| `-h` | `--help` | Show help and quit |
| `-s <path>` | `--socket <path>` | Use the specified socket path. Otherwise swaymsg asks sway for `$SWAYSOCK`, then falls back to `$I3SOCK` |
| `-t <type>` | `--type <type>` | Specify the IPC message type (see Query Types below). Default is `run_command` |
| `-p` | `--pretty` | Pretty-print output even when stdout is not a tty |
| `-r` | `--raw` | Raw JSON output even when stdout is a tty |
| `-q` | `--quiet` | Send the message but suppress the response output |
| `-m` | `--monitor` | Stay connected and print events until killed. Only valid with `subscribe`. Exits on malformed response or invalid event type |
| `-v` | `--version` | Print the swaymsg version and quit |
| `-d` | `--debug` | Enable debug logging |

---

## Query Types

### Type 0 — run_command (default)

Runs the payload as one or more sway commands. This is the default when no
`-t` flag is given. Multiple commands can be separated by `,`.

```bash
swaymsg reload
swaymsg 'workspace 3'
swaymsg 'exec alacritty'
swaymsg 'floating enable, border pixel 2'
```

Reply: array of result objects, one per parsed command.

```json
[{"success": true}]

[
  {"success": true},
  {"success": false, "parse_error": true, "error": "Invalid/unknown command"}
]
```

### Type 1 — get_workspaces

Returns all workspaces and their status.

```bash
swaymsg -t get_workspaces
swaymsg -t get_workspaces -r   # raw JSON
```

Example reply:

```json
[
  {
    "num": 1,
    "name": "1",
    "visible": true,
    "focused": true,
    "urgent": false,
    "rect": {"x": 0, "y": 23, "width": 1920, "height": 1057},
    "output": "eDP-1"
  }
]
```

Key fields:
- `num` — workspace number, or `-1` if the name does not start with a number
- `name` — workspace name as a string
- `focused` — focused by seat0 (the default seat)
- `visible` — currently visible on any output
- `urgent` — a window on this workspace has the urgent flag
- `output` — which output the workspace lives on

### Type 2 — subscribe

Subscribe to one or more event types. The payload must be a JSON array of
event name strings. Use with `-m` to keep reading events.

```bash
swaymsg -t subscribe '["workspace"]'
swaymsg -t subscribe -m '["workspace", "window"]'
swaymsg -t subscribe -m '["workspace", "window", "binding", "mode", "shutdown"]'
```

Reply on success:

```json
{"success": true}
```

After the success reply, events are sent as they occur. Each event has the
same header format as a reply (see `IPC_PROTOCOL.md`). The `-m` flag keeps
reading until killed or a malformed event arrives.

Valid event type strings: `workspace`, `output`, `mode`, `window`,
`barconfig_update`, `binding`, `shutdown`, `tick`, `bar_state_update`, `input`.

### Type 3 — get_outputs

Returns all connected outputs.

```bash
swaymsg -t get_outputs
```

Key fields per output object:
- `name` — connector name (e.g. `eDP-1`, `HDMI-A-1`)
- `active` — whether the output is enabled
- `power` — whether the display is powered on
- `scale` — current scaling factor, `-1` for disabled outputs
- `transform` — rotation: `normal`, `90`, `180`, `270`, `flipped-90`, etc.
- `current_workspace` — name of visible workspace, or `null`
- `current_mode` — `{width, height, refresh}` object
- `modes` — array of all supported modes
- `make`, `model`, `serial` — display identification
- `rect` — absolute bounds: `{x, y, width, height}`
- `hdr` — whether HDR is enabled

Example reply (abbreviated):

```json
[
  {
    "name": "eDP-1",
    "make": "Unknown",
    "model": "0x38ED",
    "active": true,
    "power": true,
    "scale": 1.0,
    "transform": "normal",
    "current_workspace": "1",
    "current_mode": {"width": 1920, "height": 1080, "refresh": 60052},
    "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080}
  }
]
```

### Type 4 — get_tree

Returns the full node layout tree as a single root object. The tree hierarchy
is: root -> output -> workspace -> containers/windows.

```bash
swaymsg -t get_tree
```

Node types (`type` field): `root`, `output`, `workspace`, `con`, `floating_con`.

Key fields per node:
- `id` — unique internal integer ID
- `name` — output name, workspace name, or window title
- `type` — node type string
- `focused` — focused by seat0
- `focus` — array of child node IDs in focus order
- `nodes` — array of tiling child nodes
- `floating_nodes` — array of floating child nodes
- `app_id` — (windows only) xdg-shell application ID, or `null`
- `pid` — (windows only) process ID
- `shell` — (windows only) `xdg_shell` or `xwayland`
- `visible` — (windows only) whether currently visible
- `fullscreen_mode` — 0=none, 1=workspace fullscreen, 2=global fullscreen
- `marks` — array of mark strings
- `rect` — absolute geometry including borders
- `window_rect` — content geometry relative to node (excludes decorations)
- `border` — `normal`, `none`, `pixel`, `csd`
- `layout` — `splith`, `splitv`, `stacked`, `tabbed`, `output`
- `percent` — fraction of parent taken, or `null` for root/special nodes
- `sticky` — appears on all workspaces
- `urgent` — node or any descendant has the urgent hint
- `inhibit_idle` — (windows only) whether inhibiting idle
- `window_properties` — (xwayland only) `{class, instance, title, transient_for}`

### Type 5 — get_marks

Returns a JSON array of all currently set mark strings. Each mark is unique
(one container per mark).

```bash
swaymsg -t get_marks
```

```json
["one", "test"]
```

### Type 6 — get_bar_config

Without a payload: returns an array of configured bar ID strings.

```bash
swaymsg -t get_bar_config
```

```json
["bar-0"]
```

With a bar ID as payload: returns the full config object for that bar.

```bash
swaymsg -t get_bar_config bar-0
```

### Type 7 — get_version

Returns version information for the running sway process.

```bash
swaymsg -t get_version
```

```json
{
  "human_readable": "1.9-dev (branch 'master')",
  "major": 1,
  "minor": 9,
  "patch": 0,
  "loaded_config_file_name": "/home/milo/.config/sway/config"
}
```

### Type 8 — get_binding_modes

Returns an array of all configured binding mode names. Always includes at
least `"default"`.

```bash
swaymsg -t get_binding_modes
```

```json
["default", "resize", "system"]
```

### Type 9 — get_config

Returns the raw text of the currently loaded config (does not expand
`include` directives).

```bash
swaymsg -t get_config
swaymsg -t get_config | jq -r '.config'
```

```json
{"config": "set $mod Mod4\nbindsym $mod+q exit\n"}
```

### Type 10 — send_tick

Sends a tick event to all clients subscribed to the `tick` event. The payload
(if any) is included in the event.

```bash
swaymsg -t send_tick
swaymsg -t send_tick 'my-payload-string'
```

```json
{"success": true}
```

### Type 11 — sync

i3 compatibility stub. Always returns `{"success": false}` in sway. Do not use.

### Type 12 — get_binding_state

Returns the currently active binding mode name.

```bash
swaymsg -t get_binding_state
```

```json
{"name": "default"}
```

### Type 100 — get_inputs

Returns all input devices currently available.

```bash
swaymsg -t get_inputs
```

Key fields per input:
- `identifier` — unique device identifier string (e.g. `1267:5:Elan_Touchpad`)
- `name` — human-readable device name
- `vendor`, `product` — vendor/product codes
- `type` — `keyboard`, `pointer`, `touch`, `tablet_tool`, `tablet_pad`, `switch`
- `xkb_active_layout_name` — (keyboards) active XKB layout name
- `xkb_layout_names` — (keyboards) all configured layout names
- `xkb_active_layout_index` — (keyboards) index of active layout
- `libinput` — (libinput devices) object with current libinput settings

### Type 101 — get_seats

Returns all configured seats. There is always at least `seat0`.

```bash
swaymsg -t get_seats
```

Key fields per seat:
- `name` — seat name (e.g. `seat0`)
- `capabilities` — integer count of capabilities
- `focus` — ID of the focused node, or `0` if a layer surface or unmanaged X11 surface has focus
- `devices` — array of input device objects (same format as get_inputs)

---

## Practical jq Pipelines

### Get the focused window's app_id (Wayland native)

```bash
swaymsg -t get_tree | jq -r '.. | select(.focused?) | .app_id // empty'
```

### Get the focused window's title

```bash
swaymsg -t get_tree | jq -r '.. | select(.focused?) | .name'
```

### Get the focused window's PID

```bash
swaymsg -t get_tree | jq '.. | select(.focused?) | .pid'
```

### Get the focused window's WM_CLASS (xwayland)

```bash
swaymsg -t get_tree | jq -r '.. | select(.focused?) | .window_properties.class // empty'
```

### Get the current workspace name

```bash
swaymsg -t get_workspaces | jq -r '.[] | select(.focused) | .name'
```

### Get the current workspace number

```bash
swaymsg -t get_workspaces | jq '.[] | select(.focused) | .num'
```

### List all workspace names

```bash
swaymsg -t get_workspaces | jq -r '.[].name'
```

### List all output names

```bash
swaymsg -t get_outputs | jq -r '.[].name'
```

### Get the active output (output showing the focused workspace)

```bash
swaymsg -t get_outputs | jq -r '.[] | select(.focused?) | .name'
```

### List all app_ids of open windows

```bash
swaymsg -t get_tree | jq -r '.. | select(.type? == "con") | .app_id // .window_properties?.class // .name' | sort -u
```

### Get all floating windows

```bash
swaymsg -t get_tree | jq '[.. | select(.floating_nodes?) | .floating_nodes[]]'
```

### Find a window by app_id and get its ID

```bash
swaymsg -t get_tree | jq '.. | select(.app_id? == "firefox") | .id'
```

### Check if any window is fullscreen

```bash
swaymsg -t get_tree | jq 'any(.. | select(.type? == "con"); .fullscreen_mode > 0)'
```

### Get the active keyboard layout

```bash
swaymsg -t get_inputs | jq -r '.[] | select(.type == "keyboard") | .xkb_active_layout_name' | head -1
```

### Get the current binding mode

```bash
swaymsg -t get_binding_state | jq -r '.name'
```

### Check sway version and config path

```bash
swaymsg -t get_version | jq -r '"\(.human_readable) — \(.loaded_config_file_name)"'
```

---

## Sending Commands at Runtime

### Workspace operations

```bash
swaymsg 'workspace 1'
swaymsg 'workspace next'
swaymsg 'workspace prev'
swaymsg 'workspace back_and_forth'
swaymsg 'workspace next_on_output'
swaymsg 'rename workspace 2 to dev'
```

### Window movement

```bash
swaymsg 'move container to workspace 3'
swaymsg 'move container to output HDMI-A-1'
swaymsg 'move left'
swaymsg 'move right 100 px'
```

### Layout changes

```bash
swaymsg 'layout tabbed'
swaymsg 'layout stacking'
swaymsg 'layout toggle split'
swaymsg 'split h'
swaymsg 'split v'
```

### Window properties

```bash
swaymsg 'floating toggle'
swaymsg 'fullscreen toggle'
swaymsg 'sticky toggle'
swaymsg 'border pixel 2'
swaymsg 'border toggle'
swaymsg 'resize set width 800 px'
swaymsg 'resize grow height 50 px'
```

### Marks

```bash
swaymsg 'mark mymark'
swaymsg 'mark --add mymark'
swaymsg 'unmark mymark'
swaymsg '[con_mark="mymark"] focus'
```

### Exec

```bash
swaymsg 'exec alacritty'
swaymsg 'exec --no-startup-id some-script.sh'
```

### Config reload and restart

```bash
swaymsg reload          # reload config file
swaymsg restart         # restart sway in-place (preserves layout)
```

### Output control

```bash
swaymsg 'output eDP-1 disable'
swaymsg 'output eDP-1 enable'
swaymsg 'output HDMI-A-1 resolution 2560x1440 position 1920 0'
swaymsg 'output * dpms off'
swaymsg 'output * dpms on'
```

### Gaps

```bash
swaymsg 'gaps inner all set 10'
swaymsg 'gaps outer current plus 5'
swaymsg 'gaps inner all set 0'
```

---

## Monitor Mode

`-m` keeps swaymsg connected and prints events as they arrive. It only works
with type `subscribe`. swaymsg exits if it receives a malformed response or
an invalid event type was requested.

```bash
# Print all workspace and window events
swaymsg -t subscribe -m '["workspace", "window"]'

# Print all events
swaymsg -t subscribe -m '["workspace","output","mode","window","barconfig_update","binding","shutdown","tick","bar_state_update","input"]'

# Use in a script — process each event line
swaymsg -t subscribe -m '["window"]' | while IFS= read -r line; do
    app=$(echo "$line" | jq -r '.container.app_id // .container.window_properties.class // "unknown"')
    change=$(echo "$line" | jq -r '.change')
    echo "Window event: $change — $app"
done
```

Each event is printed as a single line of JSON with the event payload. The
payload structure depends on the event type (see `IPC_PROTOCOL.md` for event
formats).
