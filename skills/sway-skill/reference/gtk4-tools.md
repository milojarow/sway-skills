# Writing GTK4 tools for sway — startup, app_id, styling

Small GTK4 windows bound to a sway keybinding — a launcher, prompt, picker, popup, overlay — hit a set of gotchas that produce **no error, no warning, and no log line**. The rules below are all measured on GTK 4.22 / python-gobject 3.56.3 under SwayFX 0.5.3.

---

## Do NOT use `Gtk.Application` for a keybind-launched window

`Gtk.Application` spends roughly **400 ms inside `app.run()` before the `activate` callback ever fires** — before your first line of UI code. The window lands ~0.8–1.5 s after the keypress, which produces the classic double-launch: the key appears not to have worked, it gets pressed again, and two windows open.

Timestamps relative to process start, same program both ways:

| Milestone | `Gtk.Application` | `Gtk.init()` + `GLib.MainLoop()` |
|---|---|---|
| gtk imported | 198 ms | 198 ms |
| init / main entered | 199 ms | 199 ms |
| activate fires | 667 ms | — |
| css installed | — | 266 ms |
| `present()` returned | 788 ms | 355 ms |
| window mapped | **847 ms** | **380 ms** |

Interleaved A/B, 6 pairs: median 857 ms vs 386 ms → **2.2× faster**.

**Always measure this interleaved.** A straight "all of the old, then all of the new" run can report the new version as *slower* purely because the machine picked up load in between — absolute numbers move ~3× with load, the ratio does not.

```python
from gi.repository import Gtk, Gdk, GLib

GLib.set_prgname("dev.example.mytool")   # load-bearing on sway, see below
Gtk.init()

prov = Gtk.CssProvider(); prov.load_from_data(CSS)
Gtk.StyleContext.add_provider_for_display(
    Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

loop = GLib.MainLoop()
win = Gtk.Window(title=f"mytool:{os.getpid()}")   # Gtk.Window, not Gtk.ApplicationWindow
win.connect("close-request", lambda *_: (loop.quit(), False)[1])
win.connect("destroy", lambda *_: loop.quit())
win.present()
loop.run()
```

### The sway-specific catch: `set_prgname` becomes the `app_id`

Without a `Gtk.Application` there is no `application_id`, so the Wayland **`app_id` falls back to the program name**. `GLib.set_prgname(...)` is therefore load-bearing: every `for_window [app_id="…"]` rule and every `swaymsg '[app_id="…"] kill'` hangs off it. With it set, the tree reports the chosen id and `for_window [app_id="dev.example.mytool"] floating enable, border none` matches normally:

```
app_id = 'dev.example.mytool' | name = 'mytool:12345' | rect {...}
```

## Single-instance: take the lock *before* `import gi`

A non-blocking `flock` taken before the GTK import makes a second keypress cost ~60 ms and exit silently, instead of paying the whole GTK startup and *then* discovering it should not have opened.

```python
_LOCK_FD = None   # module-level: must not be garbage collected

def claim_lock() -> bool:
    global _LOCK_FD
    run_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    try:
        fd = os.open(os.path.join(run_dir, "mytool.lock"), os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    _LOCK_FD = fd
    return True

if not claim_lock():
    sys.exit(0)

import gi   # only now
```

`flock` releases on process death (including SIGKILL), so a stale lock file is never a problem.

## `gtk4-layer-shell`: put `LD_PRELOAD` in the keybinding

`gtk4-layer-shell` must load before `libwayland-client`, which a language binding cannot arrange from inside the process — the usual workaround is for the script to `os.execv` itself with `LD_PRELOAD` set. That second interpreter start costs ~40 ms of dead time on **every** launch. Set it in the keybinding instead, and keep the re-exec only as a fallback for launching by hand:

```sway
bindsym --to-code $mod+i exec LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so ~/.scripts/mytool
```

```python
if (_LAYER_SO not in os.environ.get("LD_PRELOAD", "")
        and not os.environ.get("MYTOOL_PRELOADED")
        and os.path.exists(_LAYER_SO)):
    ...re-exec...
```

---

## CSS: generic class names belong to the theme — prefix everything

A rule that looks obviously correct renders wrong, with **no CSS parse error, no GTK warning, no log line**. Typical shape: a `1px solid #00ecec` border comes out a dull theme grey, and it gets reported as a border bug — the border is there, it is just the theme's colour.

```css
.frame { border: 1px solid #00ecec; background: #0a0612; }   /* renders grey */
```

`frame` is a class GTK themes style themselves (it is what `GtkFrame` uses). The theme's rule wins even though the app provider is installed at `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` (600) against the theme's 400 — presumably on specificity. The mechanism does not matter; the observable fact does: **the theme wins.** Themes that define a lot of generic classes (Catppuccin, Adwaita derivatives) make this common.

Proof — same declarations, two class names, one window, one screenshot: `.frame` renders a dull grey border, `.peek-frame` renders bright cyan. Nothing else differs. (Ruled out first: the `border:` shorthand. Shorthand and longhand both render correctly when the class name does not collide.)

**Fix: prefix every class in an app stylesheet** — `.mytool-frame`, `.mytool-bar`, `.mytool-hint`. Never use these bare:

`frame` · `background` · `view` · `flat` · `title` · `subtitle` · `header` · `card` · `dim-label` · `body` · `heading` · `toolbar` · `osd` · `entry` · `linked` · `circular` · `suggested-action` · `destructive-action`

### Catching it without a compositor

Read the **computed** style in-process. No window is shown, so it never steals focus:

```python
lbl = Gtk.Label(); lbl.add_css_class("mytool-prompt")
w = Gtk.Window(); w.set_child(lbl); w.realize()      # surface exists, never mapped
c = lbl.get_color()
print(tuple(round(v * 255) for v in (c.red, c.green, c.blue)))
```

**Trap:** `get_color()` caches. Install the CSS provider *before* creating the widget, or the readback returns the pre-provider value and it looks like `Gtk.StyleContext.add_provider_for_display` is a no-op. It is not — provider-before-widget returns the expected value.

Colour *and* geometry together still need a real render: a nested headless sway + `grim` + per-row pixel analysis. `Gtk.WidgetPaintable.snapshot()` on a merely *realized* (unmapped) window does **not** work — the widget draws nothing and the PNG comes out flat background.

---

## Walls

- **`Gtk.Application` costs ~400 ms of invisible startup** — use `Gtk.init()` + `GLib.MainLoop()` for keybind-launched windows.
- **No `Gtk.Application` means no `application_id`** — `GLib.set_prgname()` is what sets the sway `app_id`; without it, window criteria have nothing to match.
- **A/B startup timings must be interleaved** — sequential runs measure machine load, not the change.
- **`flock` after `import gi` is too late** — the duplicate has already paid full GTK startup.
- **Re-exec for `LD_PRELOAD` is ~40 ms per launch** — put it in the `bindsym` and keep re-exec as the manual-launch fallback.
- **A bare generic class name (`.frame`, `.entry`, `.card`…) loses to the GTK theme, silently** — prefix every app class.
- **`get_color()` caches** — install the CSS provider before creating the widget or the readback lies.
- **`WidgetPaintable.snapshot()` on an unmapped window renders nothing** — geometry checks need a real (nested/headless) compositor.
