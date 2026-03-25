# swayr Command Reference

> Note: commands with `lru` in their name mean MRU (most-recently-used), not least-recently-used. This is a naming quirk from the project's early development.

---

## Non-Menu Switchers

These commands cycle through a sequence of windows without opening a menu. The sequence order is:
1. All windows with urgency hints
2. Matching windows (command-specific)
3. The most-recently-used window at sequence start
4. Back to the origin window (window focused when the sequence began)

No window is visited twice across all steps. Steps 1, 3, and 4 can be suppressed with flags.

**Common flags for all non-menu switchers:**
- `--skip-urgent` — skip step 1 (urgent windows)
- `--skip-lru` — skip step 3 (MRU window)
- `--skip-origin` — skip step 4 (return to origin)
- `--skip-lru-if-current-doesnt-match` — skip MRU window only if the currently focused window does not match the command's criteria

### `switch-to-urgent-or-lru-window`
Cycles to urgent windows first, then the MRU window, then back to origin. Step 2 (matching windows) is disabled — this is the purest MRU switcher. Ideal for Alt+Tab.

### `switch-to-app-or-urgent-or-lru-window <name>`
Cycles through windows matching `<name>`, then urgent windows, then MRU. `<name>` is matched literally against `app_id` (Wayland) or `class`/`instance` (X11). Exits non-zero if no matching window exists, enabling "focus or launch" shell idioms:
```sh
swayr switch-to-app-or-urgent-or-lru-window --skip-lru-if-current-doesnt-match firefox || firefox
```

### `switch-to-mark-or-urgent-or-lru-window <con_mark>`
Cycles to the window carrying `<con_mark>`. Since sway marks are unique per window, this effectively jumps to a specific named window. Exits non-zero if no window has the mark.

### `switch-to-matching-or-urgent-or-lru-window <criteria>`
Cycles through windows matching a criteria query (see Criteria section below), then urgent, then MRU. Exits non-zero if no window matches.

---

## Menu Switchers

These commands open the configured menu program and act on the selection.

### `switch-window`
Shows all windows sorted: urgent first, then MRU order, focused window last. Focusing the selected window.

### `steal-window`
Shows all windows (same order as `switch-window`). Moves the selected window into the current workspace.

### `steal-window-or-container`
Shows all windows and containers. Moves the selected window or container into the current workspace.

### `switch-workspace`
Shows all workspaces in MRU order. Switches to the selected workspace.

### `switch-output`
Shows all outputs (monitors). Focuses the selected output.

### `switch-workspace-or-window`
Shows all workspaces and their windows in a tree structure. Switches to the selected workspace or focuses the selected window.

### `switch-workspace-container-or-window`
Shows workspaces, containers, and windows. Switches to or focuses the selected item.

### `switch-to`
Shows outputs, workspaces, containers, and windows. Switches to or focuses the selected item.

### `quit-window`
Shows all windows. Quits the selected window via sway IPC `kill`.
- `--kill` / `-k` — uses `kill -9 <pid>` instead of the IPC kill message.

### `quit-workspace-or-window`
Shows workspaces and their windows. Quits all windows of the selected workspace, or just the selected window.

### `quit-workspace-container-or-window`
Shows workspaces, containers, and windows. Quits all windows of the selected workspace/container, or the selected window.

### `move-focused-to-workspace`
Shows workspaces. Moves the currently focused window or container to the selected workspace.

Non-matching input creates a new workspace. Supported formats:
- `w:<workspace>` — switch to (or create) workspace by digit, name, or `<digit>:<name>`
- `s:<cmd>` — execute a sway command via swaymsg
- Anything else is treated as a workspace name (`w:<input>`)
- Prefix with `#` to force non-match treatment

### `move-focused-to`
Shows outputs, workspaces, containers, and windows. Moves the currently focused container or window to the selected target. Non-matching input handled same as `move-focused-to-workspace`.

### `swap-focused-with`
Shows all windows and containers. Swaps the currently focused window or container with the selected one.

---

## Cycling Commands

These cycle through windows in tree iteration order (not MRU order). The MRU order is frozen during a cycle sequence and resumes when a non-cycling command is received.

### `next-window all-workspaces|current-workspace`
Focus the next window in depth-first tree order. Argument controls scope.

### `prev-window all-workspaces|current-workspace`
Focus the previous window in depth-first tree order.

### `next-tiled-window` / `prev-tiled-window`
Cycle only windows in tiled containers.

### `next-tabbed-or-stacked-window` / `prev-tabbed-or-stacked-window`
Cycle only windows in tabbed or stacked containers.

### `next-floating-window` / `prev-floating-window`
Cycle only floating windows.

### `next-window-of-same-layout` / `prev-window-of-same-layout`
Cycles windows of the same layout type as the current window:
- Floating current → cycles floating
- Tabbed/stacked current → cycles tabbed/stacked
- Tiled current → cycles tiled
- Otherwise → cycles all windows

### `next-matching-window <criteria>` / `prev-matching-window <criteria>`
Cycle only windows matching the given criteria query.

---

## Layout Modification Commands

### `tile-workspace exclude-floating|include-floating`
Re-tiles all windows on the current workspace. Process: moves all windows to a scratch workspace, sets current workspace to `splith`, re-inserts windows. Works with `auto_tile` to produce balanced layouts.

### `shuffle-tile-workspace exclude-floating|include-floating`
Like `tile-workspace` but shuffles window order before re-insertion and randomly focuses already-inserted windows during insertion. Produces more balanced layouts with `auto_tile` (e.g., 2+4 split instead of 1+4).

### `tab-workspace exclude-floating|include-floating`
Puts all windows of the current workspace into a tabbed container.

### `toggle-tab-shuffle-tile-workspace exclude-floating|include-floating`
Toggles between tabbed and tiled layout. Calls `shuffle-tile-workspace` if currently tabbed, and `tab-workspace` if currently tiled.

---

## Scripting Commands

### `get-windows-as-json`
Returns a JSON array of all windows.
- `--include-scratchpad` — include scratchpad windows
- `--matching <CRITERIA>` — restrict to matching windows
- `--error-if-no-match` — exit non-zero if no windows match (makes it suitable for `if` checks in scripts)

### `for-each-window <CRITERIA> <SHELL_COMMAND>`
Executes `<SHELL_COMMAND>` for each window matching `<CRITERIA>`. Format placeholders (e.g. `{app_name}`, `{pid}`) are substituted in the command. Commands run in parallel and must complete within 2 seconds. Returns a JSON array with exit code, stdout, stderr, and error for each execution.

Example:
```sh
swayr for-each-window true echo "App {app_name} has PID {pid}."
```

---

## Miscellaneous Commands

### `configure-outputs`
Repeatedly prompts for output configuration commands via the menu until aborted. Useful for ad-hoc monitor setup.

### `execute-swaymsg-command`
Shows most common swaymsg commands (that need no additional input) and executes the selected one. Non-matching input is passed directly to swaymsg. Custom commands can be added via `[swaymsg_commands]` in config.

### `execute-swayr-command`
Shows all swayr commands in the menu and executes the selected one. Useful for commands without keybindings.

### `nop`
Does nothing. Used to explicitly break out of a non-menu switching sequence or cycling sequence without side effects.

### `print-config`
Prints the current active config in TOML format to stdout.

### `print-default-config`
Prints the built-in default config (the one generated on first run) in TOML format to stdout.

### `merge-config <FILE>`
Reads config from `<FILE>` and merges it with the current config. Options in `<FILE>` override current options; unspecified options are unchanged. Useful for temporary alternate configs:
```sh
swayr merge-config ~/.config/swayr/alt.toml; swayr switch-window; swayr reload-config
```

### `reload-config`
Reloads config from the standard config file (`~/.config/swayr/config.toml`), discarding any merges or in-memory changes.

---

## Criteria Queries

Used by `switch-to-matching-or-urgent-or-lru-window`, `next-matching-window`, `get-windows-as-json`, `for-each-window`, and others.

### Simple criteria (compatible with sway's `[criteria]` syntax)

| Criterion | Description |
|---|---|
| `app_id=<regex\|__focused__>` | Match Wayland app ID |
| `class=<regex\|__focused__>` | Match X11 window class |
| `instance=<regex\|__focused__>` | Match X11 window instance |
| `title=<regex\|__focused__>` | Match window title |
| `workspace=<regex\|__focused__\|__visible__>` | Match workspace |
| `con_mark=<regex>` | Match container mark |
| `con_id=<uint\|__focused__>` | Match container ID |
| `shell=<"xdg_shell"\|"xwayland"\|__focused__>` | Match shell type |
| `pid=<uint>` | Match process ID |
| `floating` | Match floating windows |
| `tiling` | Match tiled windows |
| `app_name=<regex\|__focused__>` | Match app_id OR class OR instance (swayr extension) |

All regex values use Rust's `regex` crate syntax. `__focused__` performs a literal match against the focused window's value.

### Compound criteria

```
[and <crit1> <crit2> ...]   # all must match (and is optional)
[or <crit1> <crit2> ...]    # any must match
not <crit>                   # negate a criterion
```

Combinators can be `AND`/`OR`/`NOT` or `&&`/`||`/`!`. Criteria can be nested:
```
[|| [app_id="firefox" tiling]
    [&& !app_id="firefox" floating workspace=__focused__]]
```

Boolean literals `true` and `false` (or `TRUE`/`FALSE`) are also valid criteria.
