# Synthetic input: wtype vs ydotool, and the wtype→slurp crash

Two tools inject keystrokes on this machine's Wayland session, and they are not
interchangeable — each corrupts a different thing if used past its limits.

## wtype leaves the seat in a state that SIGSEGVs the next `slurp`

`wtype` uploads its own generated keymap through `zwp_virtual_keyboard_v1`. That
leaves the seat in a state where the **next** `slurp` invocation takes SIGSEGV
inside `xkb_state_update_mask` (libxkbcommon), reached from
`wl_display_dispatch_queue_pending` via libffi (`si_code: SEGV_MAPERR`). No
`slurp` means no geometry, so any capture script built on `GEOMETRY=$(slurp)`
aborts.

**Symptom on this machine:** the `Print` screenshot binding "stops working" —
freeze overlay appears, hangs, then snaps back with no capture — seconds AFTER
some unrelated action (showing a window, pasting a path, dictating). It reads
as a screenshot bug and gets debugged there, but the trigger is whatever last
called `wtype`, not the screenshot flow itself.

**It does not heal on its own.** A bare retry is worthless — three slurps in a
row died after a single `wtype` call, across repeated rounds.

### Measure with the exit status, NOT coredump counts

`coredumpctl list | grep -c slurp` gives false negatives: the core takes time
to be written and indexed, so a count taken ~1s later can read "survived" when
the crash is in fact in flight and shows up moments later with a timestamp
proving it. If an instrument disagrees with itself between otherwise-identical
runs, suspect the instrument, not the code.

The exit status is direct and unambiguous:

```sh
probe() {
  slurp >/dev/null 2>&1 & local p=$!
  sleep 1.3; kill $p 2>/dev/null; wait $p 2>/dev/null
  case $? in 139) echo SIGSEGV ;; 143) echo healthy ;; *) echo "rc=$?" ;; esac
}
```

Calibrate against itself: two clean runs give 143/143; two runs right after
`wtype -M shift -m shift` give 139/139. Reproducing takes ~5s and needs no
screenshot tooling — `wtype` typing NO text is already enough to trip it.
Controls: the same shift gesture via `ydotool key 42:1 42:0` leaves `slurp`
healthy, and `slurp` run alone does too — isolating `wtype`'s virtual-keyboard
upload as the cause.

### The repair: one event from a real uinput device

```sh
ydotool key 42:1 42:0    # shift down/up — types nothing, fires no binding
```

This restores the seat completely, and the repair holds for every later
`slurp`. `ydotoold` registers one real `uinput` device on the seat carrying
the seat's own layout, which is why it heals rather than adding a second
virtual keymap on top.

### Choosing wtype vs ydotool by what the caller types

**ASCII callers (paths, URLs, identifiers) — use ydotool outright**, byte-exact
and no seat corruption:

| wtype | ydotool |
|---|---|
| `wtype "text"` | `ydotool type -d 4 -- "text"` |
| `wtype -M ctrl -k f -m ctrl` | `ydotool key 29:1 33:1 33:0 29:0` |
| `wtype -k BackSpace` | `ydotool key 14:1 14:0` |

Keycodes are Linux input-event codes: ctrl 29, shift 42, f 33, backspace 14,
enter 28.

**Unicode callers — cannot be swapped; keep wtype and repair afterwards.**
`ydotool type` maps characters against the active keyboard layout and
**silently drops everything non-ASCII** — accented/Spanish text loses every
accented character with no error (dead keys `' " ~ ^` came through fine; the
problem is unicode, not dead keys). A dictation or accented-text tool must
therefore keep `wtype` for the typing itself and call the `ydotool key 42:1
42:0` repair when its session closes.

### Net pattern for a capture script

Repair, THEN retry once, and only on a signal death. A user cancel (Escape)
exits 1 with empty output and must never be retried, or Escape re-opens the
selector:

```sh
GEOMETRY=$(slurp) || SLURP_STATUS=$?
if [ "${SLURP_STATUS:-0}" -ge 128 ]; then
    ydotool key 42:1 42:0 2>/dev/null || true
    GEOMETRY=$(slurp) || true
fi
```

### Finding the trigger

The action that breaks `Print` is usually not the one being debugged, and can
be a keybinding used constantly (e.g. a "show this window, then send it
Ctrl+F" script). Enumerate every caller before blaming one:

```sh
grep -rln 'wtype' ~/.scripts ~/.config ~/.local/bin
```

### Ordering as evidence

When two programs crash together, check which died FIRST —
`coredumpctl list` timestamps to the second. A downstream viewer crashing
~1s after `slurp` makes the viewer's crash a consequence, not the cause —
don't start the investigation at the wrong end.
