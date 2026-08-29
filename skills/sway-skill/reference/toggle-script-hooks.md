# Start/stop toggle scripts: only the STARTING instance knows the output path

The common shape for a one-key-does-both binding (recording, and anything else
built the same way) is one script that checks whether the process is already
running and branches:

```sh
pgrep -x wf-recorder >/dev/null
if [ $? != 0 ]; then
    file="$target_path/$timestamp.webm"
    wf-recorder -g "$area" --file="$file"     # blocks until SIGINT
    notify "Finished recording ${file}"
else
    pkill -x --signal SIGINT wf-recorder
fi
```

## Where to hook "the thing just finished"

To hook anything onto "a recording just finished" — index it, upload it, put
it on a shelf, run it through a converter — the placement is not a preference.
The **stopping** press takes the `else` branch, sends a signal and exits; it
never learns the filename. The **starting** instance is the one still blocked
on `wf-recorder`, and when that call returns the file is closed and `$file` is
still in scope. That single line after the blocking call is the only place the
path is both final and known. Putting the hook in the stop branch, or in a
wrapper around the keybinding, silently gets nothing.

Guard with `-s`, not `-f`. `wf-recorder` dying (bad codec params, full disk)
leaves a 0-byte file behind, and a downstream consumer pointed at an empty
file is worse than one that never fired:

```sh
if [ -s "$file" ]; then
    consumer --add "$file"
fi
```

## Testing it without touching the operator's mouse

The blocker is that the script calls `slurp` for region selection, so the
obvious test needs a human drag — or synthetic pointer input, which is rude on
a machine someone is using. Stub `slurp` instead: it reads candidate rects on
stdin and prints the chosen geometry, so a three-line replacement first on
`PATH` is a faithful stand-in:

```sh
printf '#!/bin/sh\ncat >/dev/null\necho "0,0 160x120"\n' > "$tmp/slurp"
chmod +x "$tmp/slurp"
PATH="$tmp:$PATH" setsid ./recorder.sh > rec.log 2>&1 &
until pgrep -x wf-recorder >/dev/null; do sleep 0.25; done
sleep 2
./recorder.sh                      # second invocation takes the stop branch
until ! pgrep -x wf-recorder >/dev/null; do sleep 0.25; done
```

That exercises the real script and the real recorder end to end — the
countdown, the branch selection, the filename construction, the hook. Pick a
tiny region: the recording is of the live screen, and a 160x120 corner keeps
whatever is on it out of the file. Delete the artifact afterwards.

Measure the result against state that existed before, not against the log:
count the files in the output directory and the entries in the consumer's
store before and after, and assert the new path is the one that appeared. A
log line saying "Finished recording X" proves the notification ran, not that
the hook did.

## Two adjacent facts worth keeping

- `pgrep -x wf-recorder` before starting a test — if a real recording of the
  operator's is already running, the test's first invocation would STOP it.
- `pgrep -a -f '<pattern>'` to check whether your own helper survived will
  match the shell running the check itself. Read the compositor's window
  list, or match on the process name, rather than trusting a `-f` pattern
  about your own tooling.

## A three-state toggle (launch / show / hide) needs a lock around the launch

A different shape: a bar button (`on-click`) drives a script with three
branches — no instance → **launch** it · hidden → **show** · visible →
**hide**. The script launches the app in the background and returns
immediately.

Between the launch and the window actually mapping, a Chromium/Electron-class
app takes 0.8–2.5 s cold. The user sees nothing happen, clicks again, and the
second click lands inside that window. Two silent outcomes, both wrong:

- if the window has settled by then, the toggle finds it and **hides** it —
  it flashes on then off in one blink;
- if it hasn't, the toggle **launches again** — and a launcher with the usual
  "instance alive but 0 windows → restart it" guard **kills the instance that
  was still starting** and opens a fresh one instead.

This reads as "it redraws from scratch on every click", which sounds like a
compositor/rendering bug and isn't. To confirm without adding instrumentation,
if the toggle already logs its branch: check how many LAUNCH branches were
immediately followed by a HIDE — if most of them were, seconds apart, that's
the user's impatient second click, not a timer.

**Fix — `flock -n` on a per-instance lockfile, taken on entry, with the
launch itself running in the FOREGROUND while the lock is held:**

```sh
LOCK="${XDG_RUNTIME_DIR:-/tmp}/mi-toggle-$acct.lock"
exec 9>"$LOCK"
flock -n 9 || { log "clic ignorado — lanzamiento en curso"; exit 0; }
```

The lock is held for a normal show/hide barely long enough to matter, and for
however long the launch takes when there's nothing running yet. Extra clicks
during a launch are dropped instead of hiding or reaping the window that just
came up.

**Send the launcher's own stdout/stderr into the toggle's log, not
`/dev/null`.** The silent "instance alive, 0 windows — restarting it" branch
is exactly the line that proves this failure mode, and it's the one branch
most likely to be swallowed with `>/dev/null 2>&1`.

## Killing a shell daemon by its script PID orphans the pipeline

A daemon whose body is a pipeline —

```sh
swaymsg -t subscribe -m '["window","workspace"]' \
  | jq --unbuffered -r 'select(...) | .change' \
  | while read -r change; do ...; done
```

— started as `./daemon.sh &` and stopped with `kill $!` only kills the `sh`.
The three pipeline members are reparented to PID 1 and keep running — still
subscribed, still acting.

This matters beyond leaked processes: run a test twice and the second run has
TWO live daemons racing the same state. That has produced a phantom FAIL in a
suite where the code under test was correct — two concurrent undos each
subtracted the full delta and left a workspace 30px wider than the screen. The
bug was in the harness, and the symptom pointed straight at the feature.

Detection:

```sh
ps -eo pid,ppid,args | grep -E 'daemon\.sh|swaymsg -t subscribe'
```

`PPID 1` on something you just killed is the tell.

Two fixes, both worth having:

- **Stop it the way it is supervised.** `systemctl --user stop <unit>` kills
  the whole cgroup. In a test harness with no service manager,
  `setsid ./daemon.sh &` then `kill -- -$PID` (a negative PID targets the
  whole process group).
- **Make concurrent runs safe anyway**, because the keypress path and the
  daemon path of the same feature can genuinely overlap in normal use, not
  just in a test. A `flock` on a shared lock file, taken *before* the state is
  read, serializes the read-modify-write:

  ```sh
  exec 9>"$STATE_DIR/.lock"
  flock -w 2 9 || exit 0
  ```

  Taking the lock before `get_tree` — not just before the write — also stops
  the geometry a run acts on from going stale underneath it.

## Match windows by a stable `app_id` suffix, not the literal string

`--app` windows built from a URL + profile can have their `app_id`
**rewritten** by the browser when the site starts behaving like a PWA. Any
script that targets those windows (by criteria or `swaymsg`) should match on
the stable part (e.g. a trailing pattern) rather than the exact literal.

The failure is asymmetric: the toggle itself fails loudly (it just launches
again, which is noticeable). What fails silently is a **closer/cleanup**
script that falls through to a generic branch, skips whatever teardown it was
supposed to run, and leaves the browser process alive with 0 windows eating
memory. When applying this fix, sweep every script in the set in the same
change — a toggle/launcher/closer trio fixed in two of three still leaves the
hole open.
