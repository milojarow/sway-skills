# Screen sharing — xdg-desktop-portal on wlroots

Sway has no screen-capture API of its own for applications: sharing goes through the **portal**. The full chain is

```
app → (Electron/Chromium) WebRTC → xdg-desktop-portal → xdg-desktop-portal-wlr → chooser (slurp) → PipeWire → wlroots screencopy
```

Every link can fail independently, and the app almost always reports the same useless "can't share screen". Diagnose by **layer**, not by guessing.

## Setup on this system

- Backend routing lives in `/usr/share/xdg-desktop-portal/sway-portals.conf`: default backend `gtk`, but `ScreenCast` and `Screenshot` are routed to `wlr` (`xdg-desktop-portal-wlr`, "xdpw").
- Routing only applies if **`XDG_CURRENT_DESKTOP=sway`** is present in the systemd user environment — otherwise the portal picks the wrong backend and screencast silently misbehaves.

## Sharing a single WINDOW is possible — the limit is the chooser, not the stack

> Older guidance (including earlier versions of this file) said window capture does not exist on wlroots and that output-only selection is "by design". **That stopped being true with sway 1.12**, whose release notes add support for capturing individual windows. Both halves of the chain carry it:
>
> ```bash
> strings $(readlink -f $(command -v sway)) | grep image_capture_source
> #   wlr_ext_foreign_toplevel_image_capture_source_manager_v1_create
> #   wlr_ext_output_image_capture_source_manager_v1_create
> #   wlr_ext_image_copy_capture_manager_v1_create
>
> strings /usr/lib/xdg-desktop-portal-wlr | grep -iE "toplevel|window"
> #   ext_foreign_toplevel_image_capture_source_manager_v1
> #   wlroots: capturable toplevel: %s app_id: %s title: %s
> #   Window: %s (%s)   ·   target->output || target->toplevel
> ```
>
> The portal shipped the support first and the compositor caught up; with **sway ≥ 1.12 and xdg-desktop-portal-wlr ≥ 0.8.2** the capability is present on the machine.

**Why it still looks output-only in practice: the chooser.** Per `man 5 xdg-desktop-portal-wlr`, the chooser must print one of two things on stdout:

- `Output: <name>` (what slurp produces with `-f 'Monitor: %o'`), or
- `Window: <ext-foreign-toplevel-list-v1 identifier>` — the same id `lswt(1)` prints.

With `chooser_type=default` xdpw takes the first available of slurp, wmenu, wofi, rofi, bemenu, mew, fuzzel — and **slurp can only select geometry**, so it can never emit a `Window:` line. The whole flow therefore feels monitor-only even though the capability is there.

To offer windows, configure a dmenu-style chooser in `~/.config/xdg-desktop-portal-wlr/config`:

```ini
[screencast]
chooser_type=dmenu
chooser_cmd=rofi -dmenu -p "Share"
```

With `chooser_type=dmenu` xdpw feeds the candidate list on stdin; the `Window: …` lines come from the capturable toplevels. **A portal config change needs the service restarted** — `systemctl --user restart xdg-desktop-portal-wlr` — reopening the app is not enough.

*Verification status:* the capabilities of both binaries and the documented chooser contract are measured; the dmenu-picks-a-window flow has not been driven end-to-end here.

**The output picker's one-click behaviour is still correct**, and still the most common false bug report: with slurp in output mode the overlay closes on the first click, dragging is deliberately disabled, the user assumes the picker "cancelled" and concludes sharing is broken. It worked — a monitor was selected.

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

- **"Window sharing doesn't exist on wlroots" is stale** — sway ≥ 1.12 + xdpw ≥ 0.8.2 support it; the default slurp chooser is what cannot offer it. Area selection is still output-only.
- **A one-click monitor pick is correct behaviour**, not a cancelled dialog.
- **Portal config changes need `systemctl --user restart xdg-desktop-portal-wlr`** — restarting the app changes nothing.
- **Missing `XDG_CURRENT_DESKTOP=sway`** in the systemd user environment breaks backend routing.
- **xdpw logs nothing on success** — an empty journal is not evidence of a dead portal.
- **A lit privacy indicator moves the blame to the app** — stop debugging the compositor.
- **Browser tab-sharing bypasses the portal** — never use it as a test of the portal chain.
