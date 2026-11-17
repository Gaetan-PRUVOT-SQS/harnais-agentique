---
name: android-ondevice-compose
description: >
  Use when building a Jetpack Compose UI for an offline/on-device Android app (e.g. a local LLM chat).
---

# Jetpack Compose gotchas for offline / on-device apps

Hard-won, non-obvious fixes. Each prevents a real crash, ANR, or UX/accessibility defect.

## Fonts: bundle TTF, do NOT use downloadable Google Fonts

Downloadable Google Fonts (`fontProviderAuthority=com.google.android.gms.fonts`) need Play Services + network and **crash an offline app at startup**:
> `java.lang.IllegalArgumentException: bad base-64` (in `FontResourcesParserCompat.readCerts`)

Fix: ship **variable TTF** files in `res/font/` (Manrope, JetBrains Mono are OFL) and drive weights with `FontVariation`:

```kotlin
@file:OptIn(androidx.compose.ui.text.ExperimentalTextApi::class)
private fun manrope(w: Int) = Font(R.font.manrope, FontWeight(w),
    variationSettings = FontVariation.Settings(FontVariation.weight(w)))
val ManropeFamily = FontFamily(manrope(400), manrope(500), manrope(700))
```
Delete the downloadable-font XMLs and the `font_certs.xml` array. (A `.ttf` and a `.xml` with the same resource name collide.)

## Window insets: use safeDrawingPadding, not just status bar

With `enableEdgeToEdge()`, `statusBarsPadding() + imePadding()` alone leaves content **under the navigation bar** — visible only in **landscape** (3-button nav moves to the side and overlaps content/send button) and on **large screens** (system taskbar hides the input bar). Fix:

```kotlin
Modifier.fillMaxSize().safeDrawingPadding()   // status + nav + cutout + IME
```
Apply it to the root of each screen AND to drawer content (keep the drawer background behind bars, pad the content inside).

## Responsive without WindowSizeClass

- **Line length**: cap content width so tablet/landscape text stays readable:
  `Modifier.fillMaxWidth().widthIn(max = 760.dp)` centered (`align(Alignment.TopCenter)` in a Box; expose the background container as a `BoxScope` lambda).
- **Short screens**: make non-list screens (welcome, loading) `Modifier.verticalScroll(rememberScrollState())` or content gets clipped in landscape.
- **Large font scale**: use `heightIn(min = 48.dp)` + padding, not fixed `height(48.dp)`, so buttons grow with text. `sp` typography already scales.
- Simulate without devices: `adb shell settings put system font_scale 1.5`, `wm density 240` (≈ large screen), `settings put system user_rotation 1` (landscape). Reset after.

## Markdown rendering in Compose

There's no built-in renderer; `Text(model.markdown)` shows raw `**`, backticks, `*`. For an LLM chat, write a small parser that is **robust to incomplete markdown** (streaming):
- Split into blocks by triple-backtick fences; an unclosed fence at the end is still rendered as a code block.
- Non-code lines: regex for headings `^#{1,6}\s`, bullets `^[-*•]\s`, numbered `^\d+\.\s`; else paragraph.
- Inline → `buildAnnotatedString` scanning `**bold**`, `` `code` ``, `*italic*`; if a marker has no closer, append it literally (never throw). Recurse for nesting.
- Code blocks: monospace + horizontal scroll + a copy button (`LocalClipboardManager`). Prefer `*` over `_` for italics to avoid false positives on `file_name`.

## Persistence off the main thread (avoid ANR)

File IO (read/parse all conversation files, write JSON) on the main/`viewModelScope` default dispatcher janks/ANRs as data grows. Make store methods `suspend` + `withContext(Dispatchers.IO)`. `MutableStateFlow.update` is thread-safe, callable from any dispatcher. For a conversation list, load only metadata (id/title/updatedAt), not message bodies.

## Persist partial output when the user cancels generation

A cancelled coroutine cannot suspend → calling a `suspend` save inside the `catch (CancellationException)` throws immediately. Save the partial in a **fresh** `viewModelScope.launch { persist() }` (a sibling, not the cancelled job), then rethrow. Also drop the empty assistant bubble if nothing was generated before the stop.

## Accessibility

- `clickable(onClickLabel = "…")` sets the click-action label, **not** a `contentDescription` — it won't appear in a uiautomator dump and TalkBack announces it only as an action. Put a real `contentDescription` on icons; give custom clickable boxes a meaningful label.
- Touch targets ≥ 48 dp (wrap small icons in `IconButton`, don't put `clickable` on a 17 dp `Icon`).
- Contrast: muted greys often fail WCAG AA (4.5:1) on dark backgrounds — verify and lighten.
- Confirm destructive actions (delete) with a dialog; persist data across rotation by holding it in the ViewModel (survives config change).
