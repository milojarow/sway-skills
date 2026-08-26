# Sway IPC — Runtime Control and State Querying


`swaymsg` is the standard CLI tool for communicating with a running sway instance over its UNIX socket. Every command you can put in `~/.config/sway/config` can be sent at runtime via `swaymsg`. Queries return JSON. The underlying protocol is the i3 IPC protocol, described in detail in `this document`. For the full swaymsg option reference and all query types with examples, see `this document`.

---

## swaymsg Basics

```bash
# Run any sway command immediately
swaymsg <command>

# Examples
swaymsg reload
swaymsg 'workspace 2'
swaymsg 'exec alacritty'
swaymsg 'focus left'
swaymsg 'move container to workspace 3'
swaymsg 'floating toggle'
swaymsg 'fullscreen toggle'
swaymsg 'layout tabbed'
swaymsg 'gaps inner all set 10'

# Query sway state (returns JSON)
swaymsg -t get_workspaces
swaymsg -t get_tree
swaymsg -t get_outputs
swaymsg -t get_inputs
```

Commands with multi-word quoted strings must be wrapped in single quotes to
prevent double-expansion (once by swaymsg, once by sway):

```bash
# Correct
swaymsg 'output "Dell U2720Q" enable'

# Wrong — the inner quotes get stripped before sway sees them
swaymsg output "Dell U2720Q" enable
```

If a command starts with a hyphen, use `--` to stop swaymsg option parsing:

```bash
swaymsg -- mark --add mymark
```

---

## Key Flags

| Flag | Long form | Purpose |
|------|-----------|---------|
| `-t <type>` | `--type` | Specify query type (default: `run_command`) |
| `-p` | `--pretty` | Pretty-printed human-readable output |
| `-r` | `--raw` | Raw JSON output even on a tty |
| `-q` | `--quiet` | Send the message but suppress output |
| `-m` | `--monitor` | Stay connected and stream events (only with `subscribe`) |
| `-s <path>` | `--socket` | Use a specific socket path instead of `$SWAYSOCK` |
| `-v` | `--version` | Print swaymsg version and exit |
| `-d` | `--debug` | Enable debug output |

---

## Quick Reference

| Query | Type flag | Returns |
|-------|-----------|---------|
| `swaymsg -t get_tree` | 4 | Full container tree (JSON object) |
| `swaymsg -t get_workspaces` | 1 | Array of workspace objects |
| `swaymsg -t get_outputs` | 3 | Array of output objects |
| `swaymsg -t get_inputs` | 100 | Array of input device objects |
| `swaymsg -t get_seats` | 101 | Array of seat objects |
| `swaymsg -t get_version` | 7 | Version and config path |
| `swaymsg -t get_config` | 9 | Currently loaded config text |
| `swaymsg -t get_binding_state` | 12 | Active binding mode name |
| `swaymsg -t get_marks` | 5 | Array of mark strings |
| `swaymsg -t get_binding_modes` | 8 | Array of configured mode names |
| `swaymsg -t get_bar_config` | 6 | Bar IDs (no payload) or bar config (with ID payload) |

---

## Common Patterns

### Get the focused window's app_id

```bash
swaymsg -t get_tree | jq -r '.. | select(.focused?) | .app_id // .name'
```

### Get the current workspace name

```bash
swaymsg -t get_workspaces | jq -r '.[] | select(.focused) | .name'
```

### Get the current workspace number

```bash
swaymsg -t get_workspaces | jq '.[] | select(.focused) | .num'
```

### Move focused window to a workspace

```bash
swaymsg 'move container to workspace 5'
swaymsg 'move container to workspace next'
swaymsg 'move container to workspace prev'
```

### Switch to a workspace

```bash
swaymsg 'workspace 3'
swaymsg 'workspace next'
swaymsg 'workspace back_and_forth'
```

### Reload config without restarting sway

```bash
swaymsg reload
```

### Check the active binding mode

```bash
swaymsg -t get_binding_state | jq -r '.name'
```

### Get PID of the focused window

```bash
swaymsg -t get_tree | jq '.. | select(.focused?) | .pid'
```

### List all open window titles

```bash
swaymsg -t get_tree | jq -r '.. | select(.type? == "con") | .name'
```

### Subscribe to events and print them as they arrive

```bash
swaymsg -t subscribe -m '["workspace","window"]'
```

---

## Return Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | swaymsg error — invalid syntax, cannot connect to socket, or cannot parse reply |
| `2` | Sway returned an error processing the command — invalid command, command failed, or invalid subscription |

Always check the `success` field in the JSON reply for `run_command` results:

```bash
result=$(swaymsg -r 'workspace 99')
if echo "$result" | jq -e '.[0].success' > /dev/null; then
    echo "Command succeeded"
else
    echo "Command failed: $(echo "$result" | jq -r '.[0].error')"
fi
```

---

## SWAYSOCK

Sway sets `$SWAYSOCK` in the environment of all child processes. Scripts
launched from sway (via `exec` or `exec_always`) will have it set automatically.

```bash
# Inspect the socket path
echo "$SWAYSOCK"
# Example: /run/user/1000/sway-ipc.1000.12345.sock

# Get it programmatically from outside a sway session
sway --get-socketpath

# Connect to a specific sway instance (useful when multiple sessions exist)
swaymsg -s /run/user/1000/sway-ipc.1000.12345.sock -t get_version
```

`$I3SOCK` is also set for i3 compatibility and accepted by swaymsg. If
`$SWAYSOCK` is not set (e.g., a systemd service launched outside of sway's
process tree), set it explicitly:

```bash
export SWAYSOCK=$(sway --get-socketpath)
swaymsg reload
```

---

---

# Sway IPC Protocol — Low-Level Socket Reference

This documents the raw IPC protocol for scripts and programs that connect
directly to the sway socket without using `swaymsg`. The protocol is
compatible with i3's IPC protocol.

---

## Socket Location

Sway sets `$SWAYSOCK` in the environment of all child processes. For
i3 compatibility, it also sets `$I3SOCK`.

```bash
# From inside a sway session
echo "$SWAYSOCK"
# Example: /run/user/1000/sway-ipc.1000.2847.sock

# From outside a sway session (e.g. a systemd service)
sway --get-socketpath
# Prints the path and exits

# Typical path pattern
/run/user/<UID>/sway-ipc.<UID>.<PID>.sock
```

If `$SWAYSOCK` is unset (script running outside sway's process tree):

```bash
export SWAYSOCK=$(sway --get-socketpath)
```

---

## Message Format

Every message and reply uses the same frame format:

```
[ magic (6 bytes) ][ payload_length (4 bytes) ][ payload_type (4 bytes) ][ payload ]
```

| Field | Size | Value |
|-------|------|-------|
| magic string | 6 bytes | `i3-ipc` (ASCII: `69 33 2d 69 70 63`) |
| payload_length | uint32, little-endian | byte length of the payload |
| payload_type | uint32, little-endian | message type number |
| payload | N bytes | UTF-8 JSON string (can be empty) |

Both integers are **32-bit unsigned, native byte order** (little-endian on
x86/ARM). The payload is always a JSON-encoded string. Replies always contain
valid JSON as the payload.

### Example: sending the `exit` command

Payload: `exit` (4 bytes), type: 0 (RUN_COMMAND)

```
Offset  Hex                                    ASCII
000000  69 33 2d 69 70 63                      i3-ipc
000006  04 00 00 00                            length = 4
00000a  00 00 00 00                            type = 0 (RUN_COMMAND)
00000e  65 78 69 74                            exit
```

### Example: sending GET_WORKSPACES

Payload: empty (0 bytes), type: 1

```
Offset  Hex                                    ASCII
000000  69 33 2d 69 70 63                      i3-ipc
000006  00 00 00 00                            length = 0
00000a  01 00 00 00                            type = 1 (GET_WORKSPACES)
```

---

## Message Types Table

| Type | Name | Payload | Reply |
|------|------|---------|-------|
| 0 | RUN_COMMAND | Sway command string | Array of `{success}` objects |
| 1 | GET_WORKSPACES | (empty) | Array of workspace objects |
| 2 | SUBSCRIBE | JSON array of event name strings | `{success: bool}` |
| 3 | GET_OUTPUTS | (empty) | Array of output objects |
| 4 | GET_TREE | (empty) | Root node object (recursive) |
| 5 | GET_MARKS | (empty) | Array of mark strings |
| 6 | GET_BAR_CONFIG | (empty) or bar ID string | Array of IDs or bar config object |
| 7 | GET_VERSION | (empty) | Version object |
| 8 | GET_BINDING_MODES | (empty) | Array of mode name strings |
| 9 | GET_CONFIG | (empty) | `{config: string}` |
| 10 | SEND_TICK | Optional payload string | `{success: bool}` |
| 11 | SYNC | (i3 compat, unused) | `{success: false}` |
| 12 | GET_BINDING_STATE | (empty) | `{name: string}` |
| 100 | GET_INPUTS | (empty) | Array of input device objects |
| 101 | GET_SEATS | (empty) | Array of seat objects |

---

## Event Types

Events are sent by sway when subscribed via SUBSCRIBE (type 2). Event replies
use the **same frame format** as regular replies, but the payload_type field
has **bit 31 set** (i.e., the value is `0x80000000 + event_number`).

| Event Type Value | Name | Trigger |
|-----------------|------|---------|
| 0x80000000 | workspace | Workspace created, destroyed, focused, moved, renamed, or urgency changed; also on config reload |
| 0x80000001 | output | Output added, removed, or reconfigured |
| 0x80000002 | mode | Binding mode changed |
| 0x80000003 | window | Window created, closed, focused, title changed, fullscreen toggled, moved, floating changed, urgency changed, or mark added/removed |
| 0x80000004 | barconfig_update | Bar configuration changed |
| 0x80000005 | binding | A configured key/mouse binding was executed |
| 0x80000006 | shutdown | IPC is shutting down (sway is exiting) |
| 0x80000007 | tick | A SEND_TICK message was received, or initial subscription confirmation |
| 0x80000014 | bar_state_update | Bar visibility toggled by modifier key |
| 0x80000015 | input | Input device added, removed, or its config changed |

When reading events from the socket: read the 14-byte header, extract the
payload length from bytes 6-9, read that many bytes, parse as JSON. Check
whether bit 31 of the type field is set to identify it as an event vs. a
reply.

---

## Subscribe Mechanism

1. Connect to `$SWAYSOCK`.
2. Send a SUBSCRIBE message (type 2) with a JSON array of event name strings as payload.
3. Read one reply frame — it will be `{"success": true}` if the subscription was accepted.
4. Loop: read frames. Each frame is an event payload. Parse the JSON and act on it.

The connection stays open until you close it or sway exits. Sway sends a
SHUTDOWN event (0x80000006) before closing the socket.

---

## Python Example — Minimal Socket Client

```python
#!/usr/bin/env python3
"""Connect to sway IPC, send GET_WORKSPACES, print the reply."""

import os
import socket
import struct
import json

MAGIC = b'i3-ipc'
HEADER_SIZE = 14  # 6 (magic) + 4 (length) + 4 (type)

MSG_TYPES = {
    'RUN_COMMAND':    0,
    'GET_WORKSPACES': 1,
    'SUBSCRIBE':      2,
    'GET_OUTPUTS':    3,
    'GET_TREE':       4,
    'GET_MARKS':      5,
    'GET_BAR_CONFIG': 6,
    'GET_VERSION':    7,
    'GET_BINDING_MODES': 8,
    'GET_CONFIG':     9,
    'SEND_TICK':      10,
    'GET_BINDING_STATE': 12,
    'GET_INPUTS':     100,
    'GET_SEATS':      101,
}


def pack_message(msg_type: int, payload: str = '') -> bytes:
    """Build a raw IPC message frame."""
    payload_bytes = payload.encode('utf-8')
    header = MAGIC + struct.pack('<II', len(payload_bytes), msg_type)
    return header + payload_bytes


def read_message(sock: socket.socket) -> tuple[int, dict]:
    """Read one IPC frame from the socket. Returns (type, parsed_json)."""
    header = b''
    while len(header) < HEADER_SIZE:
        chunk = sock.recv(HEADER_SIZE - len(header))
        if not chunk:
            raise ConnectionError('Socket closed by sway')
        header += chunk

    assert header[:6] == MAGIC, f'Bad magic: {header[:6]!r}'
    payload_len, msg_type = struct.unpack('<II', header[6:14])

    payload = b''
    while len(payload) < payload_len:
        chunk = sock.recv(payload_len - len(payload))
        if not chunk:
            raise ConnectionError('Socket closed during payload read')
        payload += chunk

    return msg_type, json.loads(payload.decode('utf-8'))


def get_socket_path() -> str:
    """Return $SWAYSOCK, or run sway --get-socketpath if not set."""
    path = os.environ.get('SWAYSOCK')
    if path:
        return path
    import subprocess
    result = subprocess.run(
        ['sway', '--get-socketpath'],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def main():
    sock_path = get_socket_path()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)

        # Send GET_WORKSPACES
        sock.sendall(pack_message(MSG_TYPES['GET_WORKSPACES']))

        # Read reply
        msg_type, data = read_message(sock)

        print(f'Reply type: {msg_type}')
        for ws in data:
            marker = '*' if ws['focused'] else ' '
            print(f'  {marker} [{ws["num"]}] {ws["name"]} on {ws["output"]}')


if __name__ == '__main__':
    main()
```

### Subscribing to events in Python

```python
#!/usr/bin/env python3
"""Subscribe to window focus events and print the app_id."""

import os
import socket
import struct
import json

MAGIC = b'i3-ipc'
HEADER_SIZE = 14
EVENT_MASK = 0x80000000


def pack_message(msg_type: int, payload: str = '') -> bytes:
    payload_bytes = payload.encode('utf-8')
    return MAGIC + struct.pack('<II', len(payload_bytes), msg_type) + payload_bytes


def read_message(sock: socket.socket) -> tuple[int, dict]:
    header = b''
    while len(header) < HEADER_SIZE:
        chunk = sock.recv(HEADER_SIZE - len(header))
        if not chunk:
            raise ConnectionError('Socket closed')
        header += chunk
    payload_len, msg_type = struct.unpack('<II', header[6:14])
    payload = b''
    while len(payload) < payload_len:
        chunk = sock.recv(payload_len - len(payload))
        if not chunk:
            raise ConnectionError('Socket closed during payload')
        payload += chunk
    return msg_type, json.loads(payload.decode('utf-8'))


sock_path = os.environ.get('SWAYSOCK', '')
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(sock_path)

    # Subscribe to window events
    sock.sendall(pack_message(2, '["window"]'))
    msg_type, reply = read_message(sock)
    assert reply.get('success'), f'Subscribe failed: {reply}'

    # Read events until killed
    while True:
        msg_type, event = read_message(sock)
        if msg_type & EVENT_MASK:
            change = event.get('change', '')
            container = event.get('container', {})
            app_id = container.get('app_id') or \
                     (container.get('window_properties') or {}).get('class') or \
                     container.get('name', 'unknown')
            print(f'{change}: {app_id}')
```

---

## Shell / socat Example

You can send raw IPC messages from the shell using `printf` and `socat`. This
is fragile for anything complex (use Python instead), but useful for quick
one-liners.

```bash
# GET_WORKSPACES: magic + length=0 + type=1 + empty payload
# Header bytes: i3-ipc (6) + \x00\x00\x00\x00 (length=0) + \x01\x00\x00\x00 (type=1)
printf 'i3-ipc\x00\x00\x00\x00\x01\x00\x00\x00' | socat - UNIX-CONNECT:"$SWAYSOCK"

# RUN_COMMAND with payload "reload": length=6, type=0
printf 'i3-ipc\x06\x00\x00\x00\x00\x00\x00\x00reload' | socat - UNIX-CONNECT:"$SWAYSOCK"
```

Note: `socat` reads the reply but does not close cleanly on its own for
queries — use `swaymsg` for reliable scripting.

---

## JSON Reply Structures

### Workspace object (from GET_WORKSPACES or workspace events)

```json
{
  "num": 1,
  "name": "1",
  "visible": true,
  "focused": true,
  "urgent": false,
  "rect": {"x": 0, "y": 23, "width": 1920, "height": 1057},
  "output": "eDP-1"
}
```

| Field | Type | Notes |
|-------|------|-------|
| `num` | int | Workspace number; `-1` if name does not start with a digit |
| `name` | string | Workspace name |
| `visible` | bool | Visible on any output |
| `focused` | bool | Focused by seat0 |
| `urgent` | bool | A window on this workspace has the urgent hint |
| `rect` | object | `{x, y, width, height}` |
| `output` | string | Output name |

### Output object (from GET_OUTPUTS)

```json
{
  "name": "eDP-1",
  "make": "Unknown",
  "model": "0x38ED",
  "serial": "0x00000000",
  "active": true,
  "power": true,
  "primary": false,
  "scale": 1.0,
  "subpixel_hinting": "rgb",
  "transform": "normal",
  "current_workspace": "1",
  "current_mode": {"width": 1920, "height": 1080, "refresh": 60052},
  "modes": [{"width": 1920, "height": 1080, "refresh": 60052}],
  "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
  "hdr": false
}
```

### Node / container object (from GET_TREE, window events)

Key fields (see this document for the full list):

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Internal unique node ID |
| `name` | string | Output name / workspace name / window title |
| `type` | string | `root`, `output`, `workspace`, `con`, `floating_con` |
| `focused` | bool | Focused by seat0 |
| `focus` | array | Child IDs in focus order |
| `nodes` | array | Tiling children |
| `floating_nodes` | array | Floating children |
| `app_id` | string\|null | (windows) xdg-shell app ID |
| `pid` | int | (windows) process ID |
| `shell` | string | (windows) `xdg_shell` or `xwayland` |
| `visible` | bool | (windows) currently visible |
| `fullscreen_mode` | int | 0=none, 1=workspace, 2=global |
| `marks` | array | Assigned mark strings |
| `rect` | object | Absolute geometry `{x, y, width, height}` |
| `window_rect` | object | Content geometry relative to node |
| `border` | string | `normal`, `none`, `pixel`, `csd` |
| `layout` | string | `splith`, `splitv`, `stacked`, `tabbed`, `output` |
| `percent` | float\|null | Fraction of parent; null for root/special |
| `sticky` | bool | Shown on all workspaces |
| `urgent` | bool | Urgent hint set on this node or a descendant |
| `inhibit_idle` | bool | (windows) inhibiting idle |
| `window_properties` | object | (xwayland) `{class, instance, title, transient_for}` |

### Event: workspace

```json
{
  "change": "focus",
  "current": { /* workspace node */ },
  "old": { /* previous workspace node, or null */ }
}
```

Change values: `init`, `empty`, `focus`, `move`, `rename`, `urgent`, `reload`.

### Event: window

```json
{
  "change": "focus",
  "container": { /* node object */ }
}
```

Change values: `new`, `close`, `focus`, `title`, `fullscreen_mode`, `move`, `floating`, `urgent`, `mark`.

**`move` fires on a container changing parents** (moving between workspaces/
outputs/split containers) — measured, it does **not** fire when a floating
window's position or size changes while it stays in the same container
(`swaymsg '[app_id="x"] move position …'` / `resize set …` against a live
subscription: zero events). A guard that needs to notice a floating
reposition/resize in place has no event to subscribe to and must poll
`get_tree` instead. See
[self-placing-windows.md](self-placing-windows.md#no-window-event-fires-for-a-floating-moveresize-in-place--poll-instead).

### Event: mode

```json
{
  "change": "resize",
  "pango_markup": false
}
```

### Event: binding

```json
{
  "change": "run",
  "binding": {
    "command": "workspace 2",
    "event_state_mask": ["Mod4"],
    "input_code": 0,
    "symbol": "2",
    "input_type": "keyboard"
  }
}
```

### Event: input

```json
{
  "change": "xkb_layout",
  "input": { /* input device object */ }
}
```

Change values: `added`, `removed`, `xkb_keymap`, `xkb_layout`, `libinput_config`.

### Event: shutdown

```json
{"change": "exit"}
```

### Event: tick

```json
{"first": true, "payload": ""}
```

`first` is true when the event is the initial confirmation of subscribing to
tick events, false for subsequent ticks from SEND_TICK.

---

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
same header format as a reply (see `this document`). The `-m` flag keeps
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
  "loaded_config_file_name": "~/.config/sway/config"
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
payload structure depends on the event type (see `this document` for event
formats).
