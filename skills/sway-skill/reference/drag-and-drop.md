# Drag and drop between clients on sway/wlroots

Wayland drag-and-drop is a **client-to-client** protocol (`wl_data_device`): the compositor only routes it. So a failed drop is almost never a sway config problem — it is one of the two clients. The facts below are measured on wlroots 0.20.2 / SwayFX 0.6, with every app running Wayland-native (confirmed by `swaymsg -t get_tree` reporting `app_id`, not `class` — an `class` field means XWayland, which changes the whole picture).

## Chromium/Electron never inserts a dropped LINK or TEXT — whatever the source

The discriminator is the **payload**, not the toolkit at either end.

| payload | target | result |
|---|---|---|
| file | Chromium / Electron | **works** — the attach overlay appears |
| link or text | Chromium / Electron | the text field does not change |
| link or text | terminal | works |

Files arrive because they travel a different road (`dataTransfer.files`). That is why a file manager "can drag into the browser" and the fault looks like it belongs to the source — the difference is the payload, not the toolkit and not the origin. A GTK middleman window therefore rescues **file** drops into a Chromium target; it does nothing for a link or a text selection, because the middleman was never the problem.

Two earlier explanations were measured and refuted, in this order: first "a Chromium-family client cannot be the *source*", then "the mimes offered are wrong". Instrumenting the sender's `Gdk.ContentProvider` to log every read, with a local page reporting its DOM events, a link dragged out of a GTK4 client into Chromium/Electron produces:

```
target read text/uri-list
target read text/html
target read text/x-moz-url
target read text/plain;charset=utf-8
target read text/plain
drag-end selected_action=1        (1 = COPY)
```

So Chromium **accepts** the drop and **reads all five mime types in full** — and the text field still does not change. What is missing is the browser's own *insert-into-editable* path for an external drag, **not** the event: a page with its own `drop` handler does receive it (a local probe logged six).

**Formats still decide whether the event arrives; they never buy the insertion.** With `text/x-moz-url` in the offer that same probe saw `dragenter` and never `drop`; trimmed to the exact set a browser's own link drag offers (`text/uri-list` + `text/html` + `text/plain`) it arrived normally. One format too many costs you the event.

## The sender gets two signals that lie — decide by destination instead

The negotiated action reports COPY, and the byte reads complete. Neither says whether the application did anything with them, so any fallback shaped like *"if the target rejected it, then…"* never fires. There is nothing to infer.

What works is **choosing by destination, explicitly**: an allowlist of `app_id`s where a text drop really lands (terminals), and for everything else write the value yourself — `wl-copy`, then a synthetic paste (`ydotool key ctrl+v`). To the user it is still a single drag.

Three details that cost an afternoon each if found by hand:

1. **Setting the clipboard from the toolkit fails silently.** Owning a Wayland selection requires a recent input *serial* in that client; a `clipboard.set()` issued as a drag ends reports success while `wl-paste` keeps returning the previous value. `wl-copy` goes through `wlr-data-control`, needs no serial, and keeps serving the data after it returns.
2. **Nudge the pointer 1 px before reading which window has focus.** sway reassigns focus on pointer *motion* (`focus_follows_mouse` defaults to `yes`), and releasing the button generates no motion by itself — without the nudge you read the previous window and paste into the wrong one.
3. **Terminals paste with `Ctrl+Shift+V`, not `Ctrl+V`.**

Mime unions can be checked without opening a window, in-process:

```python
p = Gdk.ContentProvider.new_union([...])
print(p.ref_formats().union_serialize_mime_types().to_string())
```

## Deciding the payload at read time — sound in theory, breaks in PyGObject

A drag source is told nothing about where the drop will land, which is why the
workaround above (write something generic, then fix it with a synthetic paste)
exists at all. There is in fact a narrower window where the target IS knowable:
in Wayland DnD the receiver calls `wl_data_offer.receive` **after** the button
is released, and the source's mime-write handler runs then — before the
toolkit's drag-end. Measured: at that moment `focused_window()` already
resolves to the real drop target, so a provider that decides its bytes inside
the write handler can hand each target exactly the payload it wants, with
nothing to erase afterwards.

**This breaks specifically in the PyGObject binding.** Overriding
`do_write_mime_type_async` on a `Gdk.ContentProvider` subclass emits, on every
single drag:

```
GLib-GIO-CRITICAL: g_task_return_boolean: assertion 'G_IS_TASK (task)' failed
Warning: g_object_unref: assertion 'G_IS_OBJECT (object)' failed
```

The data still arrives correctly — it is a completion/lifetime failure, not a
transfer failure, and a failed `g_object_unref` declines to free rather than
corrupting anything. But it is a leak on every drag, and none of the obvious
fixes clear it: building the `Gio.Task` by hand (works with a Python callback
in isolation, fails once the real callback is a C function pointer),
delegating to `Gdk.ContentProvider.new_for_bytes` at read time so the C
callback passes straight through C→C, passing `None` instead of the received
`user_data`, and anchoring the provider in a long-lived list against GC
collecting the Python subclass while GIO still holds it. A value-based
provider (`do_ref_formats` + `do_get_value`, letting GDK's own serialiser
produce the mime) is not an escape either — GDK answers *"Cannot provide
contents as text/uri-list"* and never calls `do_get_value`.

**The idea is sound and the binding is what stops you** — this is likely fine
in C. From PyGObject, stay with the write-generic-then-correct approach
documented above.

## Erasing what a drop already inserted: count the minimum, never your model

The write-generic-then-fix approach means the source, at some point, has to
erase what the terminal inserted before writing the real value. The obvious
implementation sends one backspace per character the source *believes* it put
there. That belief is a model of the receiver, and the receiver is a chain —
terminal, then possibly mosh, then tmux, then whatever TUI is running — each
layer free to transform the text on the way in.

**What it costs when the model is wrong.** A count of `len(path) + 2` assumed
foot shell-quotes what it inserts on a drop. Over a live mosh session it does
not: the path arrives raw, no quotes at all — quoting happens on a *local*
drop and does not survive the trip through mosh. Two backspaces too many per
file overshot the end of the user's line and reached a `[Pasted text #1 +443
lines]` block sitting above it — one pasted block is one token to that TUI, so
it vanished in a single keystroke, taking 443 lines of the user's own writing
with it.

**The measurement that settles it, two gestures, no guessing:**

```sh
ssh host 'tmux capture-pane -p -t <session>'   # before
#   -> user drops ONE file, nothing else
ssh host 'tmux capture-pane -p -t <session>'
#   -> user presses ONE backspace
ssh host 'tmux capture-pane -p -t <session>'
```

Diffing the three answers both questions at once, in exact bytes rather than
guesses: what the receiver actually inserted, and whether one backspace
removes one character or a whole token. `tmux capture-pane -p` over ssh beats
a screenshot here — a screenshot cannot tell you whether the string is quoted.
When the receiver is your own live session rather than a remote one, your own
hand is the better instrument: two keystrokes from a human beat a synthetic
drag, which in a tiling layout can land wherever the windows have rearranged
to.

**The rule:** count the minimum the receiver can possibly have inserted —

```python
typed = sum(len(p) for p in paths) + max(0, len(paths) - 1)
```

the paths plus one separator between them, not a byte more. If some receiver
quotes on top of that, a couple of stray quote characters survive on the line.
Visible litter beats a deletion that reaches text nobody asked it to touch:
undershooting is cosmetic, overshooting is unrecoverable and the user cannot
undo it.

**And send every keystroke as ONE ordered process**, e.g. one
`ydotool key -d 4 14:1 14:0 ...` call carrying the full argument list — never
one process per keystroke. 66 concurrent single-keystroke invocations once
raced and only 45 landed, truncating the path mid-string.

## Testing synthetic drags without wrecking a live session

- **`ydotool mousemove -a` does not land where you ask** — absolute mode goes
  through pointer acceleration, as its own `--help` warns, and relative steps
  are accelerated too. Raising the step rate once overshot and put twelve
  drops into a browser window two windows past the intended target, changing
  the user's tab. Pin the origin first with a huge relative move
  (`-x -5000 -y -5000` clamps at 0,0), then step relatively from there — and
  **verify the landing from the outcome**, never assume it. A source that logs
  its own resolved target is the instrument.
- A list widget with rubber-band selection usually decides drag-vs-sweep from
  the pressed row's *selection state*, so a synthetic drag starting on an
  unselected row can silently become a multi-select instead of a single-item
  drag. Click to select first, then press-and-move.
- Build a **disposable** remote target for the test
  (`foot -- mosh host -- sh -c 'read ...'`) — never the operator's own live
  sessions, which have real work in them.
- A drop into a shell's line buffer does not commit on its own: send Enter as
  a separate step, or the reader never returns and the capture file stays
  empty — which reads exactly like a failed drop.

## Dragging across workspaces

`$mod+<N>` **does** switch workspace with the mouse button held — the compositor handles its own binds before forwarding to the client. What is *not* established is whether the drag survives the switch, so do not build a workflow on it.

The reliable construction is a floating **`sticky`** window as the intermediate shelf: it follows you across workspaces, so you drop into it on one workspace and drag out of it on another, with no cross-workspace drag involved.

```sway
for_window [app_id="dev.example.myshelf"] floating enable, sticky enable
```

See [fundamentals.md](fundamentals.md) for `sticky`, and [gtk4-tools.md](gtk4-tools.md) for building the GTK4 window that acts as the shelf.

## Cancelling a Wayland drag with Escape: only the compositor can

Measured on wlroots 0.20.2 / SwayFX 0.6 (GTK4): **keyboard events never reach the
origin app's toolkit while its drag is in flight**. A `Gtk.EventControllerKey` in
CAPTURE phase on the window, logged line by line, recorded zero keypresses during
the drag. No in-process handler can abort a drag this way — a key controller and
a direct `drag_cancel()` call from that handler both failed, for the same reason.

The compositor *does* see the keyboard during the drag — sway's own binds stay
live (`$mod+N` still switches workspace with the button held). The pattern that
works:

1. The app enters a **sway mode** when its drag starts (`swaymsg mode drag`) and
   leaves it on drag-end/cancel/shutdown.
2. The mode binds Escape to a CLI call that signals the app —
   `bindsym --to-code Escape mode "default", exec app --cancel-drag` (note:
   `exec` swallows the rest of the line, so it must be the last item in the
   comma chain).
3. The signal handler calls `Gtk.DragSource.drag_cancel()` — that does kill an
   in-flight Wayland drag (confirmed).

Two traps in this pattern:

- **A sway mode suspends every bind from the default mode.** If the workflow
  depends on keys during the drag (switching workspace mid-drag), replicate
  them inside the mode. Unbound keys still fall through to apps normally.
- **GLib only exposes a handful of signals** (`g_unix_signal_add`: HUP, INT,
  TERM, USR1, USR2, WINCH). If USR1/USR2 are already taken, SIGWINCH is a
  legitimate free choice for a GUI app that never runs in a terminal.

## Four traps of `Gtk.DragSource` in a window that is also a drop target

Measured building a GTK4 window that is both origin and destination of drags (a
carry-shelf). Each trap produced a symptom that looked like a different bug.

1. **The window's own drop target fires on its own drags.** If the window
   hides/collapses when it starts its own drag, the pointer is still inside it
   → its own `Gtk.DropTarget` gets `enter` → the "open on approach" logic
   REOPENS it. Symptom: open/close flicker on every drag-out, reads as
   "intermittent". Guard: an own-drag-in-flight flag; `enter` returns 0 and
   `leave` returns early while it is set.
2. **Never rebuild the list while a drag is in flight.** A rebuild destroys the
   row and its `DragSource` → the drag is orphaned: cancelling it does nothing,
   and the drag ghost does NOT clear because the icon surface keeps its last
   committed frame. Symptom: "Escape doesn't work" plus a frozen ghost. If
   something async can refresh the list (an external watcher), defer the
   refresh until drag-end/cancel.
3. **The payload freezes at drag-begin.** If collapsing/closing clears the
   selection, recomputing "what am I carrying" at drag-end sees an empty
   selection → a 3-item drag delivers 1 via the path that re-queries, while the
   provider (prepared earlier) is carrying 3. Capture the list at drag-begin and
   reuse it in end/cancel.
4. **Collapsing the origin window means MOVE, never hide/resize.** A
   `Gtk.WidgetPaintable` used as the drag icon stays bound to the live widget;
   unmapping it mid-drag leaves the gesture with a blank ghost. Moving the
   window off-screen does not unmap anything. (Freezing it to a texture with
   `renderer.render_texture()` is not a workaround either: off-screen surfaces
   don't paint text — measured 0 bytes with ink expected on both sides.)

### Bonus: `GtkListBox`'s internal click can stop firing

With a `Gtk.GestureDrag` in CAPTURE phase on the listbox (for rubber-band
selection), the listbox's internal `GtkGestureClick` stopped updating selection
in MULTIPLE mode (plain click and Ctrl+click both dead; rubber-band and drags
kept working). Rather than fight it: `listbox.observe_controllers()` → the sole
`GtkGestureClick` → `set_propagation_phase(NONE)`, then implement click
semantics by hand (plain = collapse-to-one, Ctrl = toggle, Shift = range;
`listbox.pick()` to leave row-button clicks alone).

## Walls

- **A drop that "does nothing" is a client bug, not a compositor bug** — Wayland DnD is client-to-client; sway only routes it.
- **Test the payload before the toolkit.** File vs link/text is the axis that decides; source and target toolkits are not.
- **Chromium/Electron never inserts a dropped link or text into an editable**, from any source — the drop is accepted and every mime is read. Do not build a fallback on "the target rejected it"; it never reports rejection.
- **A GTK middleman window restores a file drop** into a Chromium target — and only a file drop.
- **An extra offered mime (e.g. `text/x-moz-url`) can cost you the `drop` event entirely** — offer the set a browser's own link drag offers.
- **For non-terminal targets, write the value yourself** — `wl-copy` + synthetic paste, after nudging the pointer 1 px so focus is current.
- **A cross-workspace drag is not guaranteed to survive the workspace switch** — use a floating `sticky` shelf instead of relying on it.
- **Only the compositor sees the keyboard during a Wayland drag** — cancel it via a sway mode that signals the app, not via an in-process key handler.
- **A window that is both drag source and drop target can reopen itself on its own drag-out** — guard with an own-drag-in-flight flag.
- **Never rebuild a list mid-drag** — it orphans the `DragSource` and leaves a ghost that Escape cannot clear.
- **Collapsing the drag-origin window must MOVE it, never hide or resize it** — a `WidgetPaintable` drag icon stays bound to the live (and now unmapped) widget.
- **A source CAN read its drop target before writing the payload** (`focused_window()` resolves correctly inside the mime-write handler) — but overriding `do_write_mime_type_async` from PyGObject leaks on every drag; the idea is sound, the binding is what stops you.
- **`ydotool mousemove -a` (absolute) is not exact** — pointer acceleration applies to it too; pin the origin with a large relative move first, then step relatively, and verify the landing from the source's own log rather than assuming it.
- **When erasing what a drop already inserted, count the minimum the receiver can possibly have — never a model of it.** Quoting is not consistent across a terminal→mosh→tmux chain, and one backspace too many can delete a whole pasted block instead of one character. Measure with `tmux capture-pane`, not a guess.
- **Send corrective keystrokes as ONE ordered process**, never one process per keystroke — concurrent single-keystroke calls can race and drop characters.
