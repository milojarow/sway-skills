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

Key fields (see SWAYMSG.md for the full list):

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
