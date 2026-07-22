# Screen sharing — xdg-desktop-portal on wlroots

Sway has no screen-capture API of its own for applications: sharing goes through the **portal**. The full chain is

```
app → (Electron/Chromium) WebRTC → xdg-desktop-portal → xdg-desktop-portal-wlr → chooser (slurp) → PipeWire → wlroots screencopy
```

Every link can fail independently, and the app almost always reports the same useless "can't share screen". Diagnose by **layer**, not by guessing.

## Setup on this system

- Backend routing lives in `/usr/share/xdg-desktop-portal/sway-portals.conf`: default backend `gtk`, but `ScreenCast` and `Screenshot` are routed to `wlr` (`xdg-desktop-portal-wlr`, "xdpw").
- Routing only applies if **`XDG_CURRENT_DESKTOP=sway`** is present in the systemd user environment — otherwise the portal picks the wrong backend and screencast silently misbehaves.

## Output-only selection is by design, not a bug

On wlroots there is **no "share a window" and no "share an area"** through the portal. xdpw's default chooser is `slurp -f %o -or` — **output mode**: one click picks a whole monitor, and dragging is deliberately disabled.

This produces the most common false bug report: the overlay closes on the first click, the user assumes the picker "cancelled", and concludes sharing is broken. It worked — a monitor was selected.

(Chromium's *share a tab* option does exist, but the browser captures that internally without touching the portal, so it proves nothing about the portal chain.)

## Free signal: the waybar privacy module

The waybar `privacy` module reads PipeWire directly. If its indicator lights up while an app tries to share, **the portal delivered the stream** — sway, xdpw, slurp and PipeWire are all healthy and the fault is in the consumer (the app). That single glance skips most of the debugging below.

## Layer-discrimination method

Bisect the chain from the bottom up; each probe removes one layer of suspicion.

| Probe | Proves |
|---|---|
| Chromium/Brave + the WebRTC `getDisplayMedia` sample page, choosing **Entire Screen** | portal + slurp + PipeWire + Chromium all work (an infinite mirror = fully healthy chain), independent of the app |
| A 10-line standalone Electron script calling `desktopCapturer.getSources()`, run with `electronNN /tmp/test.js` | the Electron layer works without the app's own code |
| Whatever still fails after both pass | the app's own layer — its UI, plugin stack, or a stale bundled client mod |

A representative case of that last row: an Electron chat client whose bundled in-app mod had gone months without auto-updating; screen sharing returned once the mod's files were replaced with a current release build. Nothing in sway, the portal, or PipeWire was at fault.

## Journals & live state

```bash
# portal logs — xdpw only logs errors, so silence does NOT mean it is idle
journalctl --user -u xdg-desktop-portal-wlr -u xdg-desktop-portal

# live capture streams
pw-dump | jq '.[] | select(.info.props."media.class" == "Stream/Video")'
```

## Walls

- **No area/window selection via portal on wlroots** — output only; a one-click chooser is correct behaviour.
- **Missing `XDG_CURRENT_DESKTOP=sway`** in the systemd user environment breaks backend routing.
- **xdpw logs nothing on success** — an empty journal is not evidence of a dead portal.
- **A lit privacy indicator moves the blame to the app** — stop debugging the compositor.
- **Browser tab-sharing bypasses the portal** — never use it as a test of the portal chain.
