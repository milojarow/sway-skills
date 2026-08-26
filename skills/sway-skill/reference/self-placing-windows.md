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
