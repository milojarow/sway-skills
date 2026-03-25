# exec and exec_always — Daemon Management

---

## exec vs exec_always

Both commands execute a shell command at sway startup. The difference is what happens on `swaymsg reload`:

| Command | At startup | On `swaymsg reload` |
|---------|-----------|---------------------|
| `exec` | Runs once | Does NOT run again |
| `exec_always` | Runs | Runs again every reload |

```sway
# Runs once when sway starts — will NOT re-run on reload
exec /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1

# Runs at startup AND every time you do swaymsg reload
exec_always $my_daemon
```

Use `exec` for things that should start once and keep running untouched (authentication agents, one-time environment setup).

Use `exec_always` for daemons that need to pick up config changes on reload (clipboard managers, notification daemons, bar processes, kanshi for output profiles).

---

## How sway spawns processes

Sway does not exec the command directly. It calls:

```sh
/bin/sh -c '<your command>'
```

This has two important consequences:

**1. Shell expansion happens.** `~`, `$HOME`, `&&`, `;`, `|`, `$()` are all interpreted by sh before your program receives them. This is a feature — it means you can use shell constructs in exec commands.

**2. Inside a launched script, `$0` is `sh`, not the script path.**

When sway runs `exec_always /path/to/script.sh`, the actual process is:
```
sh -c '/path/to/script.sh'
```

The shell that runs the script has `$0 = sh`. This is standard POSIX behavior for `sh -c`. Any attempt to find the script's own directory using `$0` will fail silently:

```sh
# BROKEN — $0 is "sh", dirname "sh" returns "."
SCRIPT_DIR="$(dirname "$0")"
FILTER="$SCRIPT_DIR/clipboard-filter.py"   # resolves to ./clipboard-filter.py
```

```sh
# CORRECT — use $HOME-relative or absolute paths
FILTER="$HOME/.config/sway/scripts/clipboard-filter.py"
```

**Rule:** Never use `dirname "$0"` or `$0`-relative paths in any script launched by sway's exec or exec_always.

---

## exec_always block vs standalone

Sway supports a block syntax that prepends a command to every line inside the block:

```sway
# Block syntax — looks clean but is UNRELIABLE for daemons
exec_always {
    $cliphist_store
    $cliphist_watch
    $kanshi
}
```

```sway
# Standalone syntax — RELIABLE for daemons
exec_always $cliphist_store
exec_always $cliphist_watch
exec_always $kanshi
```

### Why blocks are unreliable for daemons

Inside an `exec_always {}` block, sway translates each inner line to `exec_always <line>` and runs them. For long-running daemon variables, this translation breaks down when the variable's expanded value is a complex compound command (one containing `;`, `&&`, or brace groups `{ ... }`).

The shell process spawned for each line inside the block may not wait for blocking subprocesses, causing daemons to silently not start.

What works fine inside `exec_always {}` blocks:
- Simple one-liner commands
- Variables that expand to a single executable path
- Quick commands that exit immediately

What is unreliable inside `exec_always {}` blocks:
- Variables whose value is a compound command with `;` or `&&`
- Variables that launch blocking/long-running processes (daemons)

```sway
# Example showing the problem
set $cliphist_store 'wl-paste --watch cliphist store'
set $cliphist_watch 'wl-paste --type text --watch /home/milo/.local/bin/waybar-signal clipboard'

# UNRELIABLE — daemons may silently not start
exec_always {
    $cliphist_store
    $cliphist_watch
}

# RELIABLE — use standalone lines
exec_always $cliphist_store
exec_always $cliphist_watch
```

**Practical rule:** Move every daemon-launching `exec_always` out of blocks and onto its own standalone line.

---

## Reliable daemon management pattern

The full three-step pattern for daemons that must restart on `swaymsg reload`:

### Step 1 — Create a dedicated script

```sh
#!/bin/sh
# ~/.config/sway/scripts/my-daemon.sh
#
# Restarts my-daemon cleanly on sway reload.
# Use $HOME paths — never dirname "$0" (sway sets $0 to "sh").

# Kill any existing instance.
# Use ^ anchor to avoid matching this sh process itself.
pkill -f "^my-daemon" 2>/dev/null

# exec replaces this shell with the daemon.
# The daemon becomes a direct child of sway (cleaner process tree).
exec my-daemon --config "$HOME/.config/my-daemon/config.toml"
```

Why `exec` at the end? `exec cmd` replaces the current shell process with `cmd` instead of forking a child. The daemon becomes a direct child of sway rather than a grandchild through a lingering sh process. This gives a cleaner process tree and ensures sway correctly tracks the daemon's lifetime.

### Step 2 — Set a variable with the absolute script path

```sway
# In 01-definitions.conf or equivalent
set $my_daemon '/home/milo/.config/sway/scripts/my-daemon.sh'
```

Use single quotes and an absolute path. Do not use `~` (prefer the explicit path or `$HOME` inside the script itself).

### Step 3 — Launch with standalone exec_always

```sway
# In 99-autostart.conf
exec_always $my_daemon
```

Not inside a block. One line per daemon.

### Complete script template

```sh
#!/bin/sh
# ~/.config/sway/scripts/daemon-template.sh
#
# Template for a sway-managed daemon.
# Called by: exec_always $daemon_var  (standalone, not in block)
#
# IMPORTANT: $0 is "sh" in sway exec context. Never use dirname "$0".
# Always use $HOME or absolute paths for file references.

# Kill any previous instance.
# The ^ anchor prevents pkill from matching this sh -c '...' process,
# whose argv includes the daemon name as a substring.
pkill -f "^daemon-binary-name" 2>/dev/null

# Optional: wait briefly for the old instance to die
# (only needed if the daemon holds exclusive resources)
# until ! pgrep -f "^daemon-binary-name" >/dev/null; do sleep 0.1; done

# Replace this shell with the daemon process.
exec daemon-binary-name \
    --config "$HOME/.config/daemon/config.toml" \
    --log-file "/tmp/daemon.log"
```

---

## exec flags

### --no-startup-id

```sway
exec --no-startup-id firefox
exec_always --no-startup-id $my_daemon
```

By default, sway sends a startup notification sequence when launching applications. This causes a loading cursor to appear. Applications that support the startup notification protocol send a message back when they are ready, clearing the cursor.

Applications that do NOT support startup notifications (most daemons, command-line tools, and some GUI apps) never send the "ready" signal, leaving the loading cursor visible until it times out.

`--no-startup-id` suppresses the startup notification entirely, preventing the cursor from showing at all.

**Use `--no-startup-id` for:**
- Background daemons (clipboard managers, notification daemons, kanshi, etc.)
- Command-line tools
- Applications known not to support startup notification

**Omit it for:**
- GUI applications that do support startup notification (most GTK/Qt apps)

```sway
# Daemon — suppress startup notification
exec_always --no-startup-id $cliphist_store
exec_always --no-startup-id $kanshi

# GUI app — let startup notification work
exec firefox
exec foot
```
