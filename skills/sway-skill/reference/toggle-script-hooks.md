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
