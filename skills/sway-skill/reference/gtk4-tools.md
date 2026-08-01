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

## Walls

- **`Gtk.Application` costs ~400 ms of invisible startup** — use `Gtk.init()` + `GLib.MainLoop()` for keybind-launched windows.
- **No `Gtk.Application` means no `application_id`** — `GLib.set_prgname()` is what sets the sway `app_id`; without it, window criteria have nothing to match.
- **A/B startup timings must be interleaved** — sequential runs measure machine load, not the change.
- **`flock` after `import gi` is too late** — the duplicate has already paid full GTK startup.
- **Re-exec for `LD_PRELOAD` is ~40 ms per launch** — put it in the `bindsym` and keep re-exec as the manual-launch fallback.
