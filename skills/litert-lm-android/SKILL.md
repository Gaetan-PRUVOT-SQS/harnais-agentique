---
name: litert-lm-android
description: >
  Use when building, integrating, or debugging an on-device LLM (Gemma) Android app with Google's LiteRT-LM (com.google.ai.edge.litertlm).
---

# On-device LLM on Android with LiteRT-LM

Knowledge for shipping a Gemma chat app that runs 100% locally via LiteRT-LM. All facts below are verified against `litertlm-android:0.13.1`. Re-verify the API for other versions with `javap` (see end).

## Engine lifecycle

```kotlin
// dependency: com.google.ai.edge.litertlm:litertlm-android:0.13.x
val config = EngineConfig(
    modelPath = file.absolutePath,
    backend = Backend.GPU(),            // or Backend.NPU(nativeLibraryDir) / Backend.CPU(numOfThreads)
    visionBackend = Backend.GPU(),      // image encoder
    audioBackend = Backend.CPU(),       // audio encoder
    maxNumTokens = null,                // null = model default (context, e.g. 4096)
    maxNumImages = null,
    cacheDir = context.cacheDir.path,
)
val engine = Engine(config).apply { initialize() }
val conversation = engine.createConversation(
    ConversationConfig(
        systemInstruction = Contents.of("…"),
        samplerConfig = SamplerConfig(topK = 40, topP = 0.95, temperature = 0.8, seed = 0),
    ),
)
// streaming: Flow of chunks
conversation.sendMessageAsync(Contents.of(contents)).map { it.extractText() }
```

- New conversation without reloading the model: `engine.createConversation(config)` again (reuse the loaded `Engine`). Loading the model is the slow part (~10 s).
- Guard `Engine`/`Conversation` access with a `Mutex`; `initialize()` and inference are heavy → `Dispatchers.IO`.

## Backends & fallback

- `EngineConfig` exposes **backend, visionBackend, audioBackend** only — there is **no video** modality.
- NPU is hardware-gated: Gemma-4 NPU runs only on **Tensor G5** (Pixel 10). Detect via `Build.SOC_MODEL`/`BOARD`/`HARDWARE`. Most devices → GPU.
- Robust init = try an ordered list and fall back: `[preferred → GPU → CPU] × [MULTIMODAL → TEXT_ONLY]`, catching exceptions per attempt. For NPU multimodal use `backend = Backend.NPU(nativeLibraryDir)`, `visionBackend = Backend.GPU()`, `audioBackend = Backend.CPU()`.
- `Backend.NPU(nativeLibraryDir = context.applicationInfo.nativeLibraryDir)` — it dlopens dispatch `.so` from there.

## Multimodal Content types

`Content.Text`, `Content.ImageBytes`, `Content.ImageFile`, `Content.AudioBytes`, `Content.AudioFile`, `Content.ToolResponse`. Build a `List<Content>` and `Contents.of(list)`.

## ⚠️ Audio MUST be WAV/FLAC/MP3 — never AAC/M4A

LiteRT-LM decodes audio via **miniaudio**, which supports only WAV/FLAC/MP3. Sending AAC/M4A (the default `MediaRecorder` output) fails with:

> `Failed to start nativeSendMessageAsync: INTERNAL: Failed to initialize miniaudio decoder, error code: -10`

Fix: record raw PCM with **`AudioRecord`** (16-bit, 16 kHz, mono) and write a 44-byte WAV header yourself (`MediaRecorder` cannot output WAV). Patch the RIFF/`data` size fields after recording.

## ⚠️ GPU top-K sampler (≈2× decode) needs a native lib + patchelf

By default the top-K sampler runs on **CPU** (logcat: `GPU sampler unavailable. Falling back to CPU sampling … libLiteRtTopKOpenClSampler.so not found`). To keep sampling on GPU:

1. Get `libLiteRtTopKOpenClSampler.so` (arm64) from `google-ai-edge/LiteRT-LM` repo `prebuilt/android_arm64/` **at the tag matching your AAR version** (it's git-LFS; clone `--filter=blob:none --sparse` + `git lfs`).
2. It has no `DT_NEEDED` for `libLiteRt.so` and expects `LiteRtCreateEnvironment` from the global scope → `dlopen` fails. Fix with **`patchelf --add-needed libLiteRt.so <lib>`** (the AAR's `libLiteRt.so` exports that symbol). `System.loadLibrary` is NOT enough.
3. Drop it in `app/src/main/jniLibs/arm64-v8a/`. Success log: `Dynamically loaded LiteRtTopKOpenClSampler C API.`

## Speculative decoding & benchmarking

```kotlin
@OptIn(ExperimentalApi::class) ExperimentalFlags.enableSpeculativeDecoding = true  // works if the bundle ships an MTP drafter
@OptIn(ExperimentalApi::class) ExperimentalFlags.enableBenchmark = true            // logs; remove for prod
```

## Shipping the model (it's huge, ~2.4 GB)

- A single Android **asset** > 2 GB hits the Java limit. Two options:
  - **Runtime download (preferred → light APK ~70 MB):** download the `.litertlm` on first launch to `filesDir`. `litert-community/*` models on HF are often **public/ungated** → anonymous download works. Crucial: HF `resolve` 302-redirects to a CDN; `HttpURLConnection` drops the `Range` header on auto-redirect → **follow redirects manually** (set `instanceFollowRedirects=false`, read `Location`, re-request with `Range`) to support resume. Verify final size, then rename `.partial` → final.
  - **Bundled chunks:** split the file into <2 GB `.bin` chunks shipped as assets (`noCompress`), reassemble at first launch. Heavy APK; only for offline-install scenarios.
- Cap user input length to avoid exceeding the context window.

## Performance reality

Decode is **memory-bandwidth-bound** on the 4-bit weights. On Tensor G3 GPU: ~8 tok/s CPU-sampler → ~13–18 tok/s with the GPU sampler. A bigger jump needs the NPU (G5) or a smaller/more-quantized model — not config tweaks.

## Inspect the API for any version

```bash
JAR=$(find ~/.gradle/caches -iname 'litertlm-android-*-runtime.jar' | head -1)
javap -classpath "$JAR" -p com.google.ai.edge.litertlm.EngineConfig
javap -classpath "$JAR" -p com.google.ai.edge.litertlm.ExperimentalFlags
unzip -l "$JAR" | grep 'Content\$'   # available Content subtypes
```
