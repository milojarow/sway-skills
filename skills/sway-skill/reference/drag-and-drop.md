# Drag and drop between clients on sway/wlroots

Wayland drag-and-drop is a **client-to-client** protocol (`wl_data_device`): the compositor only routes it. So a failed drop is almost never a sway config problem — it is one of the two clients. The facts below are measured on wlroots 0.20.2 / SwayFX 0.6, with every app running Wayland-native (confirmed by `swaymsg -t get_tree` reporting `app_id`, not `class` — an `class` field means XWayland, which changes the whole picture).

## Chromium/Electron cannot be the SOURCE of a drop into another Chromium/Electron window

| source → target | result |
|---|---|
| GTK file manager → terminal | works |
| GTK file manager → Chromium (file) | works |
| GTK file manager → Electron (file) | works |
| Chromium → Electron | **not delivered** |
| Electron → Chromium | **not delivered** |

The **receiver is not the problem**: the same Electron window happily accepts a file dropped from a GTK file manager. What fails is a Chromium-family client acting as the **source** toward another Chromium-family client. Do not spend time on the drop target, its listeners, or `for_window` rules — reproduce the same drop from a non-Chromium source first, and the fault is located in one step.

**Workaround: a GTK middleman rescues the case.** Drop into a small GTK window of your own and drag out of it again — that second drag does reach the Chromium target.

## The mime trap: `text/uri-list` for a link is a silent data loss

A link offered as `text/uri-list` makes Chromium read it as a **file**, fail to open it, and discard the payload **with no error at all** — the target field simply stays empty, which reads as "the drag never arrived".

**Rule:** `text/uri-list` only for real local files. Links and text selections are offered **`text/plain` only**.

Verified without opening a window, in-process:

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
- **Chromium/Electron → Chromium/Electron never delivers** — the receiver is fine; test with a GTK source before debugging the target.
- **A GTK middleman window restores the path** into a Chromium target.
- **`text/uri-list` on a link is dropped silently by Chromium** — offer links and text as `text/plain` only.
- **A cross-workspace drag is not guaranteed to survive the workspace switch** — use a floating `sticky` shelf instead of relying on it.
