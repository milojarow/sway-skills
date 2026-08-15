# Proving a visual change actually renders (nested headless sway + frame counting)

`swaymsg <directive>` answering `{"success": true}` proves the directive **parsed**. It says nothing about whether a pixel moved. Animations, blur, shadows and `corner_radius` all accept happily and can still be doing nothing — and "I looked at it and it seemed smoother" is not a measurement either.

The method below produces a number instead of an impression, and it applies to any visual sway/SwayFX change.

## The harness: a nested compositor, headless, driven by a script

Run a second sway inside the session, with no outputs and no input devices, and let its own config launch the choreography:

```bash
env -u WAYLAND_DISPLAY -u SWAYSOCK -u DISPLAY \
    WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 \
    WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128 XDG_CURRENT_DESKTOP=sway \
    dbus-run-session -- sway -c "$CONF"
```

The recorder is started **from inside** the nested session (an `exec` in `$CONF`), so it inherits that session's `WAYLAND_DISPLAY` and `SWAYSOCK` and there is no socket to guess:

```bash
wf-recorder -o HEADLESS-1 -f "$OUT" -x yuv420p &
```

Take two runs of the **same script**, changing exactly one config line (e.g. `animation_duration_ms 0` vs `250`). Driving it by hand twice is what turns a demonstration back into an anecdote: your own rhythm contaminates every difference you then read off the result.

**Cycle gotcha:** the take completes correctly (a valid mp4 is written) but `dbus-run-session` does not always return. Wrap the launch in `timeout 60` and judge the run by ffprobing the **file**, never by the launcher's exit code.

## The measurement: wf-recorder captures on damage, so the frame count is the proof

`wf-recorder` emits a frame when the compositor reports damage. A still desktop produces almost no frames. That makes the frame count a direct measure of **how much was drawn** — no watching the video required:

| | frames | in bursts (<50 ms apart) | isolated |
|---|---:|---:|---:|
| `animation_duration_ms 0` | 67 | 14 | 52 |
| `animation_duration_ms 250` | 217 | 170 | 46 |

The **isolated** frames are the control — static content redrawing itself. They stay flat (52 vs 46), which is what says the extra 156 burst frames are drawing, not load. Inside the bursts, the intervals: 78 frames at 17 ms, 72 at 16 ms, 10 at 18 ms → 160 of 170 sustained at 60 Hz. That is the compositor waking at full refresh rate for exactly as long as the animation lasts.

```bash
# count frames, split into bursts vs isolated
ffprobe -v error -select_streams v:0 -show_entries frame=pts_time -of csv=p=0 x.mp4 \
  | tr -d ',' | awk 'NR>1{d=$1-p; if(d<0.05) b++; else g++} {p=$1} END{print b, g}'
```

## Aligning two takes without trimming by eye: a sync flash

Because only damaged frames are emitted, the first frame of each take lands at an unpredictable offset (measured: 0.657 s vs 1.096 s from the identical script). Trimming "until it looks right" is precisely the failure mode — the eye aligns the takes to whatever conclusion it expects.

Have the choreography fire a **flash** before it opens anything: solid-colour background for 0.5 s, then back to the wallpaper. A background change is *not* animated, so it lands on the same beat at any duration setting. Then find it numerically:

```bash
ffmpeg -v error -i x.mp4 -vf "crop=300:200:0:400,signalstats,\
  metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null -
```

Keep the frame whose YAVG spikes, and trim each take against **its own** flash. The alignment becomes a measurement rather than a judgement call.

## The compound-event trap: repeat every event 2–3 times

An A/B is only about the event you think you triggered. If the action drags a *second*, animatable change along with it, the burst you measure belongs to the passenger and the take looks impeccable while answering the wrong question.

Measured case: asking whether the scratchpad animates. The first `scratchpad show` produced a 14-frame burst — on its own, "the scratchpad animates" is irresistible and false. Sway returns the window **floating**, so that first show carried a tiled→floating conversion, and the resize/move path animated *that*. The second show (already floating) was flat.

**The asymmetry between repetition 1 and repetition 2 is the tell.** So:

- **Repeat each event 2–3 times in the choreography.** If the first differs from the second, there is a hidden event inside the first.
- **Then isolate it** by performing the suspected passenger up front as its own step (here: `floating enable` before sending the window to the scratchpad). If the burst moves to that step and the event under test goes flat, the passenger was the animation.

Generalized: **before believing an A/B, ask what else the action changed.** Correct data about a compound event is still a wrong answer.

## Hygiene when the recording will be published

A bare `fastfetch` prints `user@host` and `Local IP`. For footage that leaves the machine, name the modules explicitly and drop `Title` and `LocalIp`:

```bash
fastfetch -s OS:Host:Kernel:Uptime:Packages:Shell:Display:WM:Terminal:CPU:GPU:Memory:Swap:Disk:Locale:Break:Colors
```

Inspect the frame **before** uploading, not after.

## Walls

- **`{"success": true}` is a parse result, not a render result.** Anything visual needs a frame-level check.
- **`dbus-run-session` may not return** even on a clean take — `timeout` it and verify the output file.
- **Two hand-driven runs are not an A/B** — script the choreography, change one line, run it twice.
- **The first recorded frame is not t=0** — damage-based capture starts whenever damage starts; align on a scripted flash.
- **Isolated (non-burst) frames are the control** — if they move too, the difference you measured is load, not drawing.
- **A compound event answers the wrong question with correct data** — repeat each event 2–3 times; if the first burst differs from the second, something else rode along with it.
