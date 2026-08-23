# "What is under the pointer?" — sway's IPC has no answer, resolve it client-side

A window that hides, shrinks, or slides out from under a stationary pointer has to
hand keyboard focus somewhere. "Whatever the pointer is over" is the natural
answer, and sway will not give it to you directly. Two separate walls, both
measured on sway 1.12 / SwayFX 0.6.

## Wall 1 — no pointer position anywhere in the IPC

`get_seats` returns `{name, capabilities, focus, devices}` — no coordinates.
Neither does `get_inputs` or `get_tree`. There is no `get_cursor`. And a Wayland
client is told about the pointer only while it is over its own surface, so there
is no protocol back door either.

## Wall 2 — `focus_follows_mouse` fires on CROSSING, not on motion

This is the part that burns time, because the obvious workaround — nudge the
pointer 1px so sway re-evaluates — silently does nothing:

| gesture | focus moves? |
|---|---|
| `swaymsg seat - cursor move 1 0` (and back) | no |
| `ydotool mousemove -x 1 -y 0` (a real uinput device) | no |
| `ydotool mousemove -x -1000 -y 0` (crosses into another container) | **yes** |

So it is not synthetic vs real input — sway tracks which *container* the cursor
is in and only re-evaluates focus when that changes. A move inside the same
container is not a change. `swaymsg seat <name> cursor move|set` is also marked
*Deprecated: use the virtual-pointer Wayland protocol instead* in `sway(5)`, and
note `cursor move 1 0` leaves Y alone — a `0` means "do not update this
coordinate", not "move to 0".

**The one exception, worth knowing because it looks like a contradiction.** After
a DRAG, a 1px nudge *does* work. sway does not reassign focus while the pointer
is grabbed, so when the button comes up sway is holding a stale idea of what is
under the cursor, and any motion at all corrects it. Coming out of a grab: nudge
works. No grab and the pointer never left its container: nudge is useless.

## Resolve it client-side instead

A GTK client the pointer is currently over already has the answer, and the
invariant that makes this sound is worth stating: **if the pointer were over some
other window, `focus_follows_mouse` would already have focused it** — so the only
time a client still holds focus is when the pointer is over that client.

```python
pointer = {"x": None, "y": None, "fresh": False}
track = Gtk.EventControllerMotion()
track.connect("motion", lambda _c, x, y: pointer.update(x=x, y=y, fresh=True))
track.connect("enter",  lambda _c, x, y: pointer.update(x=x, y=y, fresh=True))
track.connect("leave",  lambda _c: pointer.update(fresh=False))
root.add_controller(track)
```

The physical pointer does not move when the window does, so the absolute point
is **the window's rect BEFORE it moves, plus the last local coordinates**. Read
the rect first, then move, then resolve.

Then pick the container from `get_tree` (see [ipc.md](ipc.md) for the query),
with three rules that each cost a round to learn:

- **Start at the WORKSPACE node, never the tree root.** Windows on other
  workspaces keep rects in the same global coordinate space, so a root-level
  search cheerfully matches — and focuses — a floating window that is not even
  on screen.
- **Distance first, floating second.** Ranking floating ahead of distance reads
  as correct ("floating sits on top") and is wrong: a floating window nowhere
  near the pointer then beats the tiled window the pointer is actually inside.
  Floating belongs in the tie-break, where the point is inside both.
- **Fall back to the nearest rect, not to a default.** When the pointer sits on
  a sliver of the client itself, or in a workspace gap, nothing contains the
  point; minimum squared distance to each rect keeps the answer pointer-driven
  instead of jumping to an unrelated window.

```python
def gap(r, ax, ay):
    dx = max(r["x"] - ax, ax - (r["x"] + r["width"]),  0)
    dy = max(r["y"] - ay, ay - (r["y"] + r["height"]), 0)
    return dx * dx + dy * dy

key = (gap(r, ax, ay), 0 if floating else 1, r["width"] * r["height"])
```

## Testing it needs a discriminating layout

With one window on the workspace, pointer-based and any-fallback-you-like give
the same answer, and the test passes while proving nothing. Stack TWO windows
and probe **the same x at two different y** — a result that changes with y alone
cannot be produced by "focus the largest/first/last window". Make the two areas
nearly equal so a largest-window fallback is unambiguous when it does appear.

Two harness traps met while measuring this:

- A window that "collapses" by sliding off-screen keeps its `rect.width` (sway
  will not size a floating window under `floating_minimum_size`, 75x50), so
  open-vs-collapsed must be read from **x**, not width.
- Any `jq` that hunts a window by `app_id` across the whole tree can match one on
  another workspace, which produces expectations that are wrong rather than
  code that is.
