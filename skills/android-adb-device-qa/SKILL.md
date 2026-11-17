---
name: android-adb-device-qa
description: >
  Use when driving QA, UI testing, or dogfooding of an Android app on a real device/emulator over adb (no Espresso/instrumentation).
---

# adb-driven QA on a real Android device

Techniques and pitfalls for testing an app on-device via `adb` (no instrumentation framework). `ADB="$HOME/Library/Android/sdk/platform-tools/adb"`.

## Core loop

```bash
$ADB shell am force-stop <pkg>; $ADB logcat -c
$ADB shell am start -n <pkg>/.MainActivity
$ADB shell uiautomator dump /sdcard/d.xml         # UI tree
$ADB shell cat /sdcard/d.xml                       # parse bounds
$ADB exec-out screencap -p > shot.png              # screenshot
$ADB shell input tap X Y          # / input text "a%sb"  / swipe x1 y1 x2 y2 ms  / keyevent KEYCODE_*
```
Get an element's centre from its `bounds="[x1,y1][x2,y2]"`:
```bash
$ADB shell cat /sdcard/d.xml | tr '<' '\n' | grep -i 'content-desc="Menu"' \
  | grep -oE 'bounds="\[[0-9]+,[0-9]+\]\[[0-9]+,[0-9]+\]"' | head -1 \
  | grep -oE '[0-9]+' | paste -sd' ' - | awk '{print int(($1+$3)/2), int(($2+$4)/2)}'
```

## Pitfalls (each cost real debugging time)

1. **Soft keyboard shifts the layout** → fixed coordinates for the send/bottom buttons become wrong after typing. Hide the keyboard with `input keyevent 111` (ESC) before tapping, OR compute a control's position **relative to a stable sibling** (e.g. send button = mic icon's right edge + offset) found in a fresh dump.
2. **`onClickLabel` is NOT in the uiautomator dump.** A Compose `clickable(onClickLabel=…)` exposes a click *action*, not a `content-desc` — you can't locate it by text. Locate a labelled sibling (a real `contentDescription`) or compute an offset.
3. **Accented text breaks grep/quoting.** Matching `Génère…` or apostrophes (`l'app`) in shell often fails (UTF-8 / single-quote termination). Tap by coordinate instead, or avoid accents in the match. When building JSON/text payloads with accents/apostrophes, write them to a file (Write tool) and read in `python3`, never inline single-quoted shell.
4. **Screenshots > 2000 px are rejected** by some image viewers (landscape/large-screen are 2244 px wide). Resize first: `sips -Z 1400 shot.png --out shot_s.png`.
5. **BACK can exit the app.** From a chat/main screen `keyevent KEYCODE_BACK` finishes the activity → you land on the launcher and think the app crashed. To close a drawer/sheet, tap the scrim, don't press BACK.
6. **Inspect app-private files** with `run-as`: `$ADB shell run-as <pkg> ls -la files/...`. Globs may not expand in `run-as sh` → delete/list by **exact filename**, not `*.ext`.
7. **Reliable crash check.** `logcat -d | grep -icE 'FATAL|AndroidRuntime'` over the whole buffer catches unrelated system noise → false positives. Filter by package and confirm the process is alive:
   `$ADB logcat -d | grep -iE 'AndroidRuntime|FATAL EXCEPTION' | grep -ic <pkg>` and `$ADB shell pidof <pkg>`.
8. **Mask secrets** (tokens) in any command output: pipe through `sed "s#$TOKEN#***#g"`. Never echo a token.
9. **Background work isn't instant.** Poll with a loop + `sleep`, re-dumping until a ready marker (e.g. the input hint) appears, instead of a single fixed wait.

## Forcing configurations for responsive / robustness tests

```bash
# Landscape (app must allow rotation)
$ADB shell settings put system accelerometer_rotation 0
$ADB shell settings put system user_rotation 1
# Large-screen simulation (more dp width → tablet breakpoint, taskbar)
$ADB shell wm density 240
# Large font scale
$ADB shell settings put system font_scale 1.5
```
Always **restore** afterwards (leaving the device altered is a defect of the test itself):
```bash
$ADB shell wm density reset
$ADB shell settings put system user_rotation 0
$ADB shell settings put system accelerometer_rotation 1
$ADB shell settings put system font_scale 1.0
```

## Measuring throughput without instrumentation

For a streaming text app, sample the visible text length at two timestamps during generation (`uiautomator dump` → count chars in `text="…"`), diff over elapsed time → chars/s → ~tokens/s (≈4 chars/token, language-dependent). Crude but enough to confirm a perf change.

## Verifying a fix end-to-end

Prefer black-box evidence over assertions: send a prompt and check for the finalized-response marker; force an error path and read logcat; for media, confirm the produced file's size/format with `run-as ls -la`. State clearly which cases were NOT covered (e.g. file-picker / mic flows are hard to automate via adb).
