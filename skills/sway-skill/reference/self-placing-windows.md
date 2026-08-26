# Self-placing windows: gap offset, and two daemons fighting over one rect

A window that positions itself on launch (a strip, a panel, a launcher parked at
an edge) "disappears." The instinct is that it crashed — check that first, and
expect it to be wrong:

```sh
pgrep -af <binary>
swaymsg -t get_tree | jq '[recurse(.nodes[]?,.floating_nodes[]?)
  | select(.app_id=="<app_id>")] | .[] | {x:.rect.x, y:.rect.y, w:.rect.width}'
```

A live process plus a rect whose `x` exceeds `output_width - visible_sliver` means
it is parked past the edge, not dead. Nothing is on screen, including whatever
sliver was supposed to stay reachable.

## No `window` event fires for a floating move/resize in place — poll instead

The instinct for a guard that watches its own geometry is to subscribe to the
`window` event and react. Measure before building on that:

```sh
swaymsg -t subscribe -m '["window"]' \
  | jq -r --unbuffered 'select(.container.app_id=="<app_id>")
      | "change=\(.change) rect=\(.container.rect.x),\(.container.rect.y)"' &
swaymsg '[app_id="<app_id>"] move position 1700 300'   # → nothing
swaymsg '[app_id="<app_id>"] resize set 460 600'        # → nothing
```

**Zero events, both times.** `window` fires on new/close/focus/title/fullscreen/
move-between-containers/floating-toggle/urgent/mark — a floating *position* or
*size* change within the same container is not among them (see
[ipc.md](ipc.md#event-window) for the full `change` value list and this same
caveat). So a geometry guard has no event source; polling is the only option
left, and that is the documented exception, not laziness — worth stating with
the measurement attached.

One `get_tree` plus a walk measured 5.7ms on a 56KB tree — under 0.06% of a
core at a 10s interval, and it does nothing unless the rect is wrong. Make the
guard **state-aware** (an open panel belongs at a different x than a collapsed
one) and have it refuse to act while a drag is in flight, or it yanks the
window out from under the gesture.

## `resize set` is CENTER-anchored — resize before you move

Measured: at a fixed position, growing the height by 100 moves the top edge up
by 50. `resize` in sway keeps the container's center fixed and grows/shrinks
around it, it does not anchor a corner. So **resize BEFORE you move**, never
after — any size change that bypasses the placement routine leaves the window
shifted with nothing to correct it, since nothing is watching for it (see the
polling section above).

## Why `move position` lands somewhere else than requested

sway offsets a requested floating position by the gaps and border. Measured on
one setup: ask for `move position 1906 90`, get `1936,150` — a constant, stable
`+30,+60`. SwayFX animations do not muddy the read (`get_tree` reports the final
rect immediately, whether read at 0ms or 600ms after the move). So a self-placing
window typically moves, reads its rect back, and moves again by the difference to
compensate.

That read is the vulnerability. If ANY other agent moves the window between the
move and the read — an auto-placer daemon, a position-memory daemon, a
`for_window` rule — the correction is computed against a foreign position and
doubles down on it. A single poisoned read can put a window off the visible
output entirely.

## Two rules follow

1. **A window that places itself must be excluded from every daemon that also
   places windows.** There is usually more than one, with overlapping scopes:

   ```sh
   systemctl --user list-units --type=service | grep -i 'float\|window\|place'
   ```

   Check each daemon's own exclusion list rather than assuming they agree — one
   may track only a couple of app_ids while another ignores a different couple.

2. **A self-correcting move must verify, not double down.** Correcting once and
   trusting the result cannot detect that it was corrected against garbage. Loop
   until the rect read back IS the one requested, cap the attempts, and log when
   it never lands — that log line is how you learn something else is moving it:

   ```python
   want = ask = (target_x, target_y)
   for _ in range(4):
       sway(f'[app_id="{APP_ID}"] move position {ask[0]} {ask[1]}')
       got = read_rect()
       if got == want:
           return
       ask = (ask[0] + want[0] - got[0], ask[1] + want[1] - got[1])
   log(f"wanted {want}, settled at {got} — something else is moving this window")
   ```

## Proving the exclusion worked needs a positive control

`journalctl --user -u <placer>.service | grep -c <app_id>` before and after
adding the exclusion is the direct evidence — one line per launch beforehand,
zero after. But zero alone also describes a dead daemon. Float any other window
and confirm the daemon logs THAT in the same window of time; only then does the
zero mean exclusion, not a stopped service.

Also note which test actually discriminates: relaunching the widget and seeing
it land correctly does **not** prove the race was fixed. With the race removed,
the old one-shot correction converges too, because the gap offset is constant.
What the old code couldn't survive was a poisoned read mid-correction — only the
placer daemon's own journal measures whether that can still happen.

## When the mover cannot be pinned down, stop hunting

Not every displacement traces to a daemon in the config. A window at the SAME
size but a different position is a pure move, which no daemon may admit to —
and with `floating_modifier $mod normal`, any `$mod`+drag over the window moves
it, so after the fact a stray drag is indistinguishable from a daemon in the
logs.

Reasserting the one position the window is sure of (the polling guard above)
makes the question moot. Diagnosis is worth doing until it stops paying; a
self-healing window is worth more than a name for the culprit.

## Keep a way in

A window pushed past the edge cannot be clicked, so its keybinding has to
still reach it, and opening it has to run through the same placement routine
that the guard uses. That is the difference between "it disappeared" and "it
disappeared and there is no way to get it back".
