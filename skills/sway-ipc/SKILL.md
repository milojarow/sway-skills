---
name: sway-ipc
description: "Runtime control, state querying, and event subscription via swaymsg and the IPC socket protocol. Use when running swaymsg commands, querying the current workspace or active window, writing scripts that control sway, sending commands programmatically, subscribing to window/workspace events, parsing get_tree output, or troubleshooting sway state."
---
# Sway IPC — Runtime Control and State Querying

`swaymsg` is the standard CLI tool for communicating with a running sway instance over its UNIX socket. Every command you can put in `~/.config/sway/config` can be sent at runtime via `swaymsg`. Queries return JSON. The underlying protocol is the i3 IPC protocol, described in detail in `IPC_PROTOCOL.md`. For the full swaymsg option reference and all query types with examples, see `SWAYMSG.md`.

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

## Reference Files

- `SWAYMSG.md` — all CLI options, all 15 query types with example output, jq pipelines
- `IPC_PROTOCOL.md` — raw socket protocol, message format, byte layout, event types, Python and socat examples
