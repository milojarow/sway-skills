# "A click stuck down" — probe the REAL button state without touching the operator's pointer

Symptom: an app starts doing rubber-band / drag / multi-select just from mouse
motion, as if the left button were held. The first question to answer is
**where** it's stuck: in the kernel/seat (device, libinput, a synthetic-input
tool that sent press without release) or in the CLIENT's internal state
(GTK/Qt stuck in rubber-band mode).

There is no `get_cursor` or button state in sway's IPC (see
[pointer-resolution.md](pointer-resolution.md)). And `ydotool click` / `wtype`
"to test" moves the operator's REAL pointer (never do this without asking)
and contaminates the very measurement you're taking.

## The correct measurement is passive: `EVIOCGKEY` on every `/dev/input/event*`

Returns the kernel's bitmap of keys/buttons currently considered PRESSED.
Injects nothing, moves nothing. Needs membership in the `input` group (or
root).

```python
def _ior(t, nr, size):            # _IOC(_IOC_READ, ...)
    return (2 << 30) | (size << 16) | (ord(t) << 8) | nr
KEY_MAX = 0x2ff
NBYTES     = KEY_MAX // 8 + 1     # 96
EVIOCGKEY  = _ior('E', 0x18, NBYTES)
EVIOCGNAME = _ior('E', 0x06, 256)
# fcntl.ioctl(fd, EVIOCGKEY, buf, True); bit c => buf[c//8] >> (c%8) & 1
# BTN_LEFT=0x110 RIGHT=0x111 MIDDLE=0x112 SIDE=0x113 EXTRA=0x114
# BTN_TOUCH=0x14a BTN_TOOL_FINGER=0x145
```

### Include the positive control, or the zero doesn't count

"No button down" looks identical to "the ioctl failed and nobody noticed".
Two cheap guards:

1. The script **counts and prints** how many devices answered OK vs failed.
2. Run it **with a finger on the touchpad**: it must report `BTN_TOUCH` +
   `BTN_TOOL_FINGER` down. If it sees those, the instrument can find things —
   only then does "`BTN_LEFT` not down" count as evidence. (Measured: one run
   with a finger on the pad detected `BTN_TOUCH`/`BTN_TOOL_FINGER` and
   `KEY_LEFTMETA`; the next run, finger off, came back clean — the instrument
   agrees with itself and discriminates.)

### Reading the result

- **`BTN_LEFT` down on some device** → stuck in the kernel/seat. Suspects: a
  `ydotool`/synthetic-input call that sent press without release, or the
  physical button. Every window on the seat is affected, not just one.
- **Nothing down, but the app keeps banding** → the stuck state lives in the
  CLIENT. Fixed by moving the pointer out of the window and doing one clean
  click on another (`wl_pointer.leave` + a full press/release cycle resets the
  internal flag). A single affected app almost always means this.

### The upstream class of bug (not a config issue)

Icon views in the lxqt/pcmanfm family keep the rubber-band selection active
without re-checking that the left button is still down. Two documented
triggers in the Qt port (`lxqt/pcmanfm-qt#1055` and a related issue): (a) a
synthetic motion event emitted by smooth-scroll code — arrives after
two-finger scrolling followed by a click; (b) starting a drag with the left
button, pressing the right button for the context menu, releasing both, then
Escape — the band keeps following the cursor with no button down at all.
Useful as a reproduction script when this symptom shows up in any file
manager of that family.
