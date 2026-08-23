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

## Never veto `close-request` to "just hide" a long-lived window

A GTK4 daemon that hides its window instead of closing it is often written like this:

```python
win.connect("close-request", lambda *_: (hide(), True)[1])   # WRONG
```

Returning `True` **vetoes** the close — and that makes the window **unkillable from the compositor**: `swaymsg '[app_id="…"] kill'` is absorbed silently, exit status 0, no message anywhere.

The real failure mode is not "the window won't close". It is a testing trap that costs far more:

1. the script is edited,
2. the usual kill + relaunch runs,
3. the kill kills nothing, and the relaunch hits the single-instance `flock` and exits 0,
4. **the next test measures the OLD binary while everyone believes it measures the patch.**

Hiding is the job of the toggle keybinding (`move scratchpad` / `scratchpad show`) and of an Escape handler; a close must actually close, and persistent state survives in its own file. The `close-request` handler quits the main loop and returns `False` (see the startup skeleton above).

### The five-second check before believing any test of a self-written daemon

Compare the process start time against the script's mtime:

```sh
stat -c %y /proc/$PID          # when the process started
stat -c %y ~/.scripts/mytool   # when the script was last edited
```

If the process is **older** than the script, the test measured old code. This applies to any user daemon, not just GTK ones — and it is the first thing to check whenever a patch "has no effect".

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

### Loading it from inside the script instead: `CDLL` before `import gi`

When the keybinding isn't the only launch path (invoked by hand from a
terminal, or from a wrapper that doesn't control the exec line), load the
`.so` explicitly before `gi` is imported at all — this is what the
gtk4-layer-shell project itself documents (`linking.md`):

```python
from ctypes import CDLL
CDLL("libgtk4-layer-shell.so")

import gi
gi.require_version("Gtk4LayerShell", "1.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk4LayerShell as LayerShell
from gi.repository import Gtk, Gdk, GLib
```

**Reordering `gi.require_version()` calls does NOT fix this** — both orderings
fail identically. GI resolves a library's *dependencies* before the library
itself, so `libwayland-client` is always in the process before
gtk4-layer-shell gets a chance to interpose over it, regardless of which
`require_version` line comes first. The trade-off vs. the `LD_PRELOAD`
keybinding above: the knowledge lives in the script instead of the bind, so
running it by hand behaves the same as the keybind launch — nothing to
remember at a second call site.

### The failure is a silent warning, not an error — a "did it survive" test passes anyway

A window whose layer-shell init failed is still a live, drawing process — just
a normal floating window instead of a layer surface: no anchors, no screen
coverage, doesn't take the keyboard. stderr carries the only signal:

```
Failed to initialize layer surface, GTK4 Layer Shell may have been linked after libwayland.
GtkWindow is not a layer surface. Make sure you called gtk_layer_init_for_window()
```

A test that only checks "did the process survive" or "is the screenshot
non-empty" passes either way. Grep for the warning, or check in-process
without opening a window in the operator's session:

```python
LayerShell.is_layer_window(win)   # bool, no present() needed
```

`is_layer_window()` works on a realized-but-unmapped window, so it can be
verified in the real session with nothing appearing on screen.

### `Gtk.Application` also breaks layer-shell, on top of its own startup cost

Registering a `Gtk.Application` brings up the Wayland display inside
`activate` — after gtk4-layer-shell's interposition window has already
closed, so it reproduces the same failure as the import-order trap above, on
top of the ~400 ms `app.run()` cost documented earlier in this file. For a
one-shot layer-shell popup, skip `GApplication` entirely and use the
`Gtk.init()` + `GLib.MainLoop()` skeleton from the top of this file, calling
`LayerShell.init_for_window()` right after `Gtk.Window()` is created.

---

## CSS: generic class names belong to the theme — prefix everything

A rule that looks obviously correct renders wrong, with **no CSS parse error, no GTK warning, no log line**. Typical shape: a `1px solid #00ecec` border comes out a dull theme grey, and it gets reported as a border bug — the border is there, it is just the theme's colour.

```css
.frame { border: 1px solid #00ecec; background: #0a0612; }   /* renders grey */
```

`frame` is a class GTK themes style themselves (it is what `GtkFrame` uses). The theme's rule wins even though the app provider is installed at `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION` (600) against the theme's 400 — presumably on specificity. The mechanism does not matter; the observable fact does: **the theme wins.** Themes that define a lot of generic classes (Catppuccin, Adwaita derivatives) make this common.

Proof — same declarations, two class names, one window, one screenshot: `.frame` renders a dull grey border, `.mytool-frame` renders bright cyan. Nothing else differs. (Ruled out first: the `border:` shorthand. Shorthand and longhand both render correctly when the class name does not collide.)

**Fix: prefix every class in an app stylesheet** — `.mytool-frame`, `.mytool-bar`, `.mytool-hint`. Never use these bare:

`frame` · `background` · `view` · `flat` · `title` · `subtitle` · `header` · `card` · `dim-label` · `body` · `heading` · `toolbar` · `osd` · `entry` · `progress` · `trough` · `linked` · `circular` · `suggested-action` · `destructive-action`

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

## CSS: the `entry` node ignores `padding`, `min-height` and `color` — only the inner `text` node answers

Half a stylesheet can be decorative without a single error anywhere. These rules parse cleanly and do nothing:

```css
entry.path { color: #d8d4f0; padding: 12px 14px 12px 0; font-size: 15px; }
```

The entry keeps the theme's colour and the theme's height. Verified silent — hooking `Gtk.CssProvider::parsing-error` produces zero output.

Same entry, same class, five selectors, measured one at a time:

| selector | entry colour | entry height | inner `text` colour |
|---|---|---|---|
| `entry.path { color; padding }` | unchanged | 22 | unchanged |
| `.path { color; padding }` | unchanged | 22 | unchanged |
| `entry { color; padding }` | unchanged | 22 | unchanged |
| `text.path { color }` | unchanged | 22 | unchanged |
| **`.path text { color }`** | unchanged | 22 | **applied** |

`.path text` working proves the class *does* land on the entry's node (it is the descendant combinator's anchor) — it is the entry node's own box and colour that will not take app CSS. `min-height` on it is ignored too. Themes also set an explicit colour on the `text` node, which is why inheritance from the parent does not reach it either. `get_css_name()` still returns `"entry"` and the child still returns `"text"` — the node names are not the surprise, the styling reach is.

**Rule 1 — every text property goes to `text`, not to the entry:**

```css
.mytool-path text {
  color: #d8d4f0;
  font-family: "JetBrainsMono Nerd Font", monospace;
  font-size: 15px;
  caret-color: #00ecec;
}
.mytool-path text selection { background: #00ecec; color: #0a0612; }
```

**Rule 2 — vertical rhythm goes on the row that *contains* the entry, never on the entry.** A `Gtk.Box` honours `padding` and `border` perfectly: a box with `padding: 10px 14px; border: 1px` around a 24 px entry measures 46 px, exactly 24 + 20 + 2.

```css
.mytool-bar { padding: 15px 0; }     /* the Gtk.Box holding the entry */
```

### The bug the ignored padding actually causes

Entry padding silently does nothing, so the row measures 24 px while the window height is pinned with `set_size_request(720, 56)`. **A vertical `Gtk.Box` packs its children at the top**, so the text sits glued under the 1 px top border with 32 px of dead space below — which reads as *"the top border is eating the top of the text."*

Text pixel rows within the 56 px surface:

```
before:  rows  7..20   (7 px above, 35 px below)   <- pinned height, entry padding ignored
after:   rows 22..35   (22 px above, 20 px below)  <- height from .bar padding, width-only size_request
```

Fix: let the height come from padding and pin only the width — `col.set_size_request(W, -1)` and `win.set_default_size(W, -1)`. The row is then centred by construction instead of by arithmetic.

## CSS: after a node refuses twice, stop writing selectors — draw it yourself

`.frame` and the `entry` node above are two instances of one pattern: **a composite widget's internal nodes belong to the theme, not to the app stylesheet.** `GtkProgressBar` is the third.

| node | what was tried | what happened |
|---|---|---|
| `.frame` (bare class) | `border: 1px solid #00ecec` | rendered theme grey; the same rule under `.mytool-frame` rendered cyan |
| `entry` box | `padding`, `min-height`, `color` via `entry.path`, `.path`, bare `entry` | all parsed clean, all did nothing; only the inner `text` node answered |
| `progress` (`GtkProgressBar`) | `progress`, `> trough > progress`, `background-image: none`, four `min-height` values | fill always came out the theme's accent colour; `min-height` ignored entirely |

Nothing warns in any of the three: no CSS parse error, no `GTK-CRITICAL`, no log line. The rule appears to apply and quietly loses. Renaming does not help here the way it does for `.frame` — `progress` and `trough` are *node names*, not classes, so there is no app-side name to prefix.

**The rule: the second failure on the same node is the signal. Stop writing selectors and draw the thing.** A `Gtk.DrawingArea` has no theme node to lose to:

```python
self.frac = 0.0
self.bar = Gtk.DrawingArea()
self.bar.set_content_height(3)
self.bar.set_hexpand(True)
self.bar.set_valign(Gtk.Align.CENTER)
self.bar.set_draw_func(self._draw_bar)

def _draw_bar(self, _area, cr, w, h):
    cr.set_source_rgb(0x24 / 255, 0x1f / 255, 0x38 / 255)   # trough
    cr.rectangle(0, 0, w, h); cr.fill()
    cr.set_source_rgb(0.0, 0xec / 255, 0xec / 255)          # fill
    cr.rectangle(0, 0, w * self.frac, h); cr.fill()

def _set_frac(self, f):
    self.frac = max(0.0, min(1.0, f))
    self.bar.queue_draw()
```

Measured after the swap: the fill reads exactly the requested `(0, 236, 236)` across the full 598 px width. No theme, no `min-height` argument, no cascade to lose. `set_content_height()` is a widget call, so the 3 px is not a CSS request the theme can override either.

The general shape of the escape hatch, in order of preference:

1. Prefix the class, if the losing selector is a *class* (`.frame` → `.mytool-frame`).
2. Target the leaf node the theme actually styles (`.mytool-path text`), if there is one that answers.
3. Move geometry to a container you own — a plain `Gtk.Box` honours `padding` and `border` reliably.
4. If the node itself is the problem, replace the widget with a `Gtk.DrawingArea` and a draw func.

Read the computed style (below) *before* shipping, so a losing rule is caught at the readback rather than in a screenshot. For geometry there is no colour to read back, so compare `widget.measure(Gtk.Orientation.VERTICAL, w)` against what the rule should have produced.

## Text renders soft by default (`gtk-font-rendering: AUTOMATIC`, GTK ≥ 4.16)

Glyph stems land between pixel columns at half intensity and the flat cap-height top of every digit rounds away. Tall thin letters look faded next to short ones; digits look chopped. **Nothing is clipped** — the glyphs are rasterised that way. The report will be about geometry ("the border is eating the top of the text", "the top looks chopped"), which sends you hunting for a clipping bug that does not exist.

```
$ python3 -c 'import gi; gi.require_version("Gtk","4.0"); from gi.repository import Gtk
Gtk.init(); s=Gtk.Settings.get_default()
print(s.get_property("gtk-font-rendering"), s.get_property("gtk-xft-hintstyle"))'
<FontRendering.AUTOMATIC: 0> hintslight
```

`AUTOMATIC` means GTK decides for itself and **ignores the system hint settings** — `gsettings get org.gnome.desktop.interface font-hinting` can say `slight` while GTK renders as if unhinted. `gtk-hint-font-metrics` is a different knob and makes no difference here.

**Fix — per process, nothing else on the machine changes.** Call right after `Gtk.init()`, before building any widget:

```python
def force_crisp_text() -> None:
    try:
        settings = Gtk.Settings.get_default()
        if settings is None:
            return
        settings.set_property("gtk-font-rendering", Gtk.FontRendering.MANUAL)
        settings.set_property("gtk-xft-hinting", 1)
        settings.set_property("gtk-xft-hintstyle", "hintfull")
    except Exception:
        pass   # GTK < 4.16 has no gtk-font-rendering
```

Measured against a PangoCairo render of the same string, `MANUAL` + `hintfull` reproduces it exactly. `hintslight` is better than `AUTOMATIC` but still soft; `hintnone` is worse. Side effect: full hinting makes text ~1 px taller, so a container sized around the old metrics grows by a pixel.

### Ground truth — what the glyphs *should* look like

Draw the same string straight through PangoCairo, with no widget in the path, then compare pixel row by pixel row:

```python
import gi
gi.require_version("Pango","1.0"); gi.require_version("PangoCairo","1.0")
from gi.repository import Pango, PangoCairo
import cairo
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 260, 40); ctx = cairo.Context(surf)
ctx.set_source_rgb(0.04, 0.02, 0.07); ctx.paint()
lay = PangoCairo.create_layout(ctx)
fd = Pango.FontDescription("JetBrainsMono Nerd Font")
fd.set_absolute_size(15 * Pango.SCALE)      # 15 device px == CSS font-size:15px
lay.set_font_description(fd); lay.set_text("11223344556677889900", -1)
ctx.move_to(2, 10); ctx.set_source_rgb(0.85, 0.83, 0.94)
PangoCairo.show_layout(ctx, lay); surf.write_to_png("ref.png")
```

**Never compare one GTK screenshot against another GTK screenshot** — both go through the same rasteriser, they will match perfectly, and that match proves nothing.

### Test with repeated digits, not with words

`11112222233333344444`. Round and irregular letters hide a flattened top; digits share one flat cap height, so the defect reads as a straight chop across the whole line.

### Before blaming a container for clipping, build the control where clipping is impossible

A `Gtk.Label` has no height constraint of any kind. Put a label, a plain entry, an entry with `min-height`, an entry with `padding-top`, and a bare `Gtk.Text` in one window with the same CSS and screenshot them together. If all five render byte-identically, nothing is clipping and the container theory is dead.

---

## Walls

- **`Gtk.Application` costs ~400 ms of invisible startup** — use `Gtk.init()` + `GLib.MainLoop()` for keybind-launched windows.
- **No `Gtk.Application` means no `application_id`** — `GLib.set_prgname()` is what sets the sway `app_id`; without it, window criteria have nothing to match.
- **A/B startup timings must be interleaved** — sequential runs measure machine load, not the change.
- **`flock` after `import gi` is too late** — the duplicate has already paid full GTK startup.
- **Returning `True` from `close-request` makes the window unkillable by `swaymsg … kill`** — the kill is absorbed silently and the relaunch bounces off the instance lock, so the next test runs the old binary. Hide from the toggle bind, not by vetoing the close.
- **Before trusting any test of a patched daemon, compare `/proc/$PID` mtime against the script's** — an older process means the measurement is of old code.
- **Re-exec for `LD_PRELOAD` is ~40 ms per launch** — put it in the `bindsym` and keep re-exec as the manual-launch fallback. Loading via `CDLL("libgtk4-layer-shell.so")` before `import gi` works too, keeps the fix inside the script instead of the bind, and reordering `gi.require_version()` calls never substitutes for either — GI resolves dependencies before the library itself.
- **A failed gtk4-layer-shell init is a silent warning, not an error** — the window still opens, just as a normal floating window (no anchors, no keyboard). A "process survived" test passes either way; verify with `LayerShell.is_layer_window(win)` (works unmapped) or grep stderr for "may have been linked after libwayland".
- **`Gtk.Application` breaks gtk4-layer-shell too, not just startup latency** — its Wayland display comes up inside `activate`, after the interposition window has already closed.
- **A bare generic class name (`.frame`, `.entry`, `.card`…) loses to the GTK theme, silently** — prefix every app class.
- **`get_color()` caches** — install the CSS provider before creating the widget or the readback lies.
- **`WidgetPaintable.snapshot()` on an unmapped window renders nothing** — geometry checks need a real (nested/headless) compositor.
- **`padding` / `min-height` / `color` on an `entry` node do nothing** — text properties go to `.cls text`, vertical rhythm goes to the containing `Gtk.Box`.
- **A vertical `Gtk.Box` packs children at the top** — pinning window height with `set_size_request` leaves the content glued to the top border; pin width only and let padding set the height.
- **`progress` / `trough` are node names, not classes** — there is nothing to prefix, and `min-height` plus the fill colour both stay the theme's.
- **The second failed selector on the same node is the stop signal** — replace the widget with a `Gtk.DrawingArea` + draw func; it has no theme node to lose to.
- **`gtk-font-rendering: AUTOMATIC` (GTK ≥ 4.16) overrides the system hint settings** — set `MANUAL` + `hintfull` per process; "chopped glyph tops" is soft rasterisation, not clipping.
- **A GTK-vs-GTK screenshot comparison proves nothing** — the ground truth is a PangoCairo render with no widget in the path.
- **Reported geometry bugs are often rendering bugs** — build the no-constraint control (`Gtk.Label`) first; if everything renders identically, nothing is clipping.
