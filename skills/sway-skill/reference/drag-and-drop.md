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

## Dragging across workspaces

`$mod+<N>` **does** switch workspace with the mouse button held — the compositor handles its own binds before forwarding to the client. What is *not* established is whether the drag survives the switch, so do not build a workflow on it.

The reliable construction is a floating **`sticky`** window as the intermediate shelf: it follows you across workspaces, so you drop into it on one workspace and drag out of it on another, with no cross-workspace drag involved.

```sway
for_window [app_id="dev.example.myshelf"] floating enable, sticky enable
```

See [fundamentals.md](fundamentals.md) for `sticky`, and [gtk4-tools.md](gtk4-tools.md) for building the GTK4 window that acts as the shelf.

## Walls

- **A drop that "does nothing" is a client bug, not a compositor bug** — Wayland DnD is client-to-client; sway only routes it.
- **Test the payload before the toolkit.** File vs link/text is the axis that decides; source and target toolkits are not.
- **Chromium/Electron never inserts a dropped link or text into an editable**, from any source — the drop is accepted and every mime is read. Do not build a fallback on "the target rejected it"; it never reports rejection.
- **A GTK middleman window restores a file drop** into a Chromium target — and only a file drop.
- **An extra offered mime (e.g. `text/x-moz-url`) can cost you the `drop` event entirely** — offer the set a browser's own link drag offers.
- **For non-terminal targets, write the value yourself** — `wl-copy` + synthetic paste, after nudging the pointer 1 px so focus is current.
- **A cross-workspace drag is not guaranteed to survive the workspace switch** — use a floating `sticky` shelf instead of relying on it.
