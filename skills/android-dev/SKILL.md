---
name: android-dev
description: 'Use when creating or reviewing an Android app (Kotlin, Compose, Gradle): architecture, build, security, tests and release per current official guidance. Complements the android-* skills.'
---

# Android development

When a topic skill named `android-*` (or `navigation-3`, `camerax`, `agp-9-upgrade`, `edge-to-edge`, `litert-lm-android`, `r8-analyzer`) covers the same point, that skill wins. This file is the cross-cutting checklist.

## Defaults for new work
- Kotlin only, Jetpack Compose for UI, single activity, Material 3.
- Coroutines and Flow between layers, Hilt for DI, Room for local data, DataStore instead of SharedPreferences,
  WorkManager for deferrable background work that must survive process death.
- Navigation 3 for new Compose apps (you own the back stack as a list of `NavKey`). Keep Navigation 2 in existing
  apps unless there is a concrete reason to migrate.
- Target the API level Google Play currently requires (API 36 for new apps and updates since 31 Aug 2026; existing
  apps must target at least API 35 to stay visible to new users on newer devices; an extension to 1 Nov 2026 can be
  requested in Play Console). Check the Play target API page before each release, the date moves every year.
- Android developer verification: apps had to be registered by 30 Sep 2026 (Play Console for Play apps, Android
  Developer Console for apps distributed outside Play). Enforcement starts in a few countries and goes global in 2027.
- Android 17 (API 37) is stable. Before raising `targetSdk` to 37, review its behavior changes (see Security below).

## Architecture (official app architecture guide)
- Layers: UI (composables + ViewModel), optional domain (use cases), data (repositories + data sources).
- Repositories are the only entry point to data, even with a single source. UI and ViewModels never call Room,
  Retrofit/Ktor, DataStore or system services directly.
- Single source of truth per data type, usually the database. Network refreshes write to the DB, the UI observes the DB.
- Unidirectional data flow: the ViewModel exposes one `StateFlow<UiState>`, the UI sends actions through method
  calls. Do not push one-off "events" from the ViewModel, turn them into state that the UI consumes and acknowledges.
- Collect with `collectAsStateWithLifecycle()`. Use `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`.
- Add a domain layer only when logic is reused by several ViewModels or a ViewModel gets too heavy.
- Model UI state as an immutable data class or sealed interface (Loading / Content / Error). No Android types in it.

## Coroutines and Flow
- Inject dispatchers (`@IoDispatcher`), never hardcode `Dispatchers.IO` in classes you want to test.
- Main-safe suspend functions: the data layer switches context itself, callers do not have to.
- ViewModels launch in `viewModelScope`; work that must outlive the screen goes to an app-scoped `CoroutineScope`
  or WorkManager. No `GlobalScope`.
- Catch `Exception` carefully and always rethrow `CancellationException`.
- Expose `Flow` from repositories, `suspend` for one-shot operations.

## Compose
- Stateless composables that take state and lambdas; hoist state to the lowest common owner.
- Screen-level composable gets the ViewModel; children receive plain parameters so they can be previewed and tested.
- Pass `Modifier` as the first optional parameter. Stable keys in `LazyColumn` items.
- Avoid heavy work in composition; use `remember`, `derivedStateOf`, and defer state reads to lambdas where it matters.
- Check recompositions with Layout Inspector and the Compose compiler reports before optimizing.
- Adaptive layouts: window size classes, test on phone, foldable and tablet emulators.
- With strong skipping (default since Kotlin 2.0.20), do not add `@Stable`, `@Immutable` or immutable collections by
  reflex; make the composable cheaper first, and keep existing annotations unless measurements justify removing them.
- Lazy lists: a stable primitive `key` and a `contentType` on every item; use `itemsIndexed` instead of `indexOf`;
  collect flows once in the parent, never per item; no analytics or side effects in `LaunchedEffect` of prefetched
  items.
- No side effect in a composable body: use `LaunchedEffect`, `SideEffect` or an event handler. Heavy objects such as
  formatters go in `remember`.

## Accessibility
- Every actionable or meaningful image has a `contentDescription`; decorative images use `null`.
- Touch targets at least 48dp, text in `sp`, contrast following WCAG AA, support font scaling up to 200%.
- Use `Modifier.semantics` and `mergeDescendants` for grouped content; test with TalkBack and the Accessibility Scanner.
- Compose UI tests double as accessibility checks when they query by semantics.

## Modularization and build
- Modules by feature (`:feature:xyz`) plus shared `:core:data`, `:core:domain`, `:core:ui`, `:core:testing`.
  Features never depend on other features, they talk through navigation keys and core contracts.
- Gradle version catalog (`gradle/libs.versions.toml`) for every dependency and plugin version.
- Shared build logic in convention plugins (`build-logic/` included build), no `allprojects {}` or copy-pasted blocks.
- Kotlin DSL, configuration cache and build cache on. With AGP 9 the built-in Kotlin support replaces the
  `org.jetbrains.kotlin.android` plugin. AGP 9.4 needs Gradle 9.6+ and SDK Build Tools 36; the new Variant API becomes
  mandatory in AGP 10, so migrate custom build logic now.
- KSP instead of kapt (Hilt, Room).
- Release builds: R8 full mode with `isMinifyEnabled` and `isShrinkResources`, keep rules kept minimal and commented.
- Baseline Profiles (and Startup Profiles) generated with Macrobenchmark; measure startup and scrolling jank before and after.
- Native code: build with NDK r28+ so libraries are 16 KB page size aligned (required for apps targeting API 35+).

## Security (OWASP MASVS v2 as the checklist, MASTG v2 tests and MASWE IDs for findings)
- No secrets in the APK or in git. API keys that must ship are restricted server-side; real secrets stay on a backend.
- Network: HTTPS only, `network_security_config.xml` with cleartext disabled; pin certificates only with a rotation plan.
- Storage: app-private storage by default; sensitive data encrypted with Android Keystore backed keys.
  (Jetpack Security crypto is deprecated, use Keystore + Tink or platform APIs.)
- Components: `android:exported` explicit, validate every Intent extra and deep link parameter, use `PendingIntent.FLAG_IMMUTABLE`.
- Intents and IPC:
  - An intent received from outside is never forwarded as is to a private component. Check its target package and
    component against an allowlist, or rebuild it with `IntentSanitizer` (AndroidX Core 1.9+).
  - `onNewIntent` applies the same checks as `onCreate`, and calls `setIntent()` before reading the new intent.
  - A mutable `PendingIntent` always names an explicit component; immutable stays the default.
  - No sticky broadcasts. Dynamic receivers are registered with `RECEIVER_NOT_EXPORTED` unless they really serve
    other apps; custom broadcasts between your own apps use a `signature` permission.
  - Identify a caller with `Binder.getCallingUid()` and its signing certificate (`PackageManager.hasSigningCertificate`),
    never with a package name passed in an extra. Inside `onReceive`, `getCallingUid()` returns your own uid.
  - Bound services check `enforceCallingPermission()` on each sensitive method, never the `...OrSelf...` variants.
  - Exported `ContentProvider`: `readPermission` and `writePermission` at `signature` level, parameterized selections,
    and `grantUriPermissions` limited to an explicit sub-path, never `pathPrefix="/"`.
- Runtime permissions: check them before each use, never cache the result; request background location in a separate
  step after foreground location is granted; prefer the photo picker and other no-permission APIs.
- WebView: JavaScript off unless needed, no `addJavascriptInterface` on untrusted content.
- Auth: Credential Manager (passkeys), tokens in encrypted storage, never in logs.
- Play Integrity API for server-side trust decisions, not as the only defense.
- When targeting Android 17 (API 37):
  - certificate transparency is on by default, keep it on;
  - local network access needs the `ACCESS_LOCAL_NETWORK` permission;
  - background activity starts use `MODE_BACKGROUND_ACTIVITY_START_ALLOW_IF_VISIBLE` instead of
    `MODE_BACKGROUND_ACTIVITY_START_ALLOWED`;
  - native libraries loaded with `System.load()` must be read-only files;
  - `setContentCaptureEnabled` is deprecated, protect screens showing sensitive data with `FLAG_SECURE`;
  - SMS OTPs are delayed for apps reading SMS, use the SMS Retriever or SMS User Consent APIs.
- Disable `android:debuggable` and verbose logging in release; strip logs with R8 or a logging wrapper.

## Testing (pyramid)
| Level | Tools | Where |
|---|---|---|
| Unit (most tests) | JUnit 4/5, MockK, Turbine for Flows, `kotlinx-coroutines-test` (`runTest`, `StandardTestDispatcher`) | `src/test` |
| JVM UI / Android framework | Robolectric, Compose UI test on Robolectric | `src/test` |
| Instrumented UI | Compose UI test (`createAndroidComposeRule`), Espresso for Views, Hilt testing | `src/androidTest` |
| Screenshot | Compose Preview Screenshot Testing or Roborazzi | CI on a fixed device config |
| Performance | Macrobenchmark, Baseline Profile generator | dedicated `:benchmark` module |
- Prefer fakes over mocks for repositories and data sources (put them in `:core:testing`).
- Test ViewModels by driving actions and asserting emitted `UiState` with Turbine.
- Use Room in-memory databases and a `MockWebServer` (or Ktor MockEngine) for data layer tests.
- Instrumented tests run on Gradle Managed Devices in CI so the device setup is versioned.
- Use test tags only when semantics cannot identify the node.
- Behind every Android framework or external dependency, put an interface with a default implementation and a fake
  in the test source set; mock only when no fake is possible.
- Screenshot tests per screen across compact, medium and expanded sizes, plus font scale 1.5 and each theme;
  components in each theme and font scale. Screenshots check rendering, not behaviour.
- Compose behaviour tests match by semantics first, use a test tag only when more than a few matchers would be
  needed, and always check state restoration (`StateRestorationTester`).
- Navigation has its own tests: back handling, deep links, and multiple back stacks when the app has them.
- Room or SQLDelight queries also run as instrumented tests on an in-memory database, so the device SQLite engine is
  covered.

## Static analysis
- Android Lint with `warningsAsErrors` on new code, a committed baseline for legacy issues, `checkDependencies = true`.
- detekt for code smells and complexity, ktlint (or detekt formatting) for style, both run in CI and as a pre-commit hook.
- Dependency updates through Dependabot or Renovate, with the version catalog as the single file to change.

## Release
- App signing by Google Play; keep the upload key in a password manager or CI secret store, never in the repo.
- Signing config read from environment variables or `~/.gradle/gradle.properties`, not from committed files.
- Android App Bundle (`.aab`), versionCode increasing automatically from CI, versionName following SemVer.
- Staged rollout, internal and closed testing tracks first, watch Android vitals (ANR, crash rate) before widening.
- Keep the Data safety form, permissions declarations and privacy policy accurate; request runtime permissions in context
  and only when needed. Review Play policy updates before each release.

## Definition of done for an Android change
1. `./gradlew lint detekt ktlintCheck testDebugUnitTest` green, instrumented tests green where a device is available.
2. New logic covered by unit tests; new screens covered by at least one Compose UI test of the main path.
3. No new Lint warnings, no new hardcoded strings (use resources), accessibility checked.
4. Release build assembles with R8 and the app starts (smoke test).

## Commits and approval
- Commits are short and simple, with a natural description of what changed and why in French (for example
  `Le champ email est gardé après la rotation`).
- Nothing is pushed, merged or published to a Play track without explicit approval from the user.

## Sources
- Android architecture recommendations: https://developer.android.com/topic/architecture/recommendations
- Guide to app architecture: https://developer.android.com/topic/architecture
- Navigation 3: https://developer.android.com/guide/navigation/navigation-3
- Coroutines best practices: https://developer.android.com/kotlin/coroutines/coroutines-best-practices
- Modularization guide: https://developer.android.com/topic/modularization
- Testing strategies: https://developer.android.com/training/testing/fundamentals/strategies
- Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/overview
- 16 KB page sizes: https://developer.android.com/guide/practices/page-sizes
- Play target API requirement: https://developer.android.com/google/play/requirements/target-sdk
- OWASP MASVS: https://mas.owasp.org/MASVS/
- OWASP MASTG v2 (tests linked to MASWE weaknesses) and MASWE v1.0.0: https://mas.owasp.org/MASTG/ and https://mas.owasp.org/MASWE/
- Android 17 behavior changes (apps targeting 37): https://developer.android.com/about/versions/17/behavior-changes-17
- Android developer verification: https://developer.android.com/developer-verification
- AGP 9.4 release notes: https://developer.android.com/build/releases/agp-9-4-0-release-notes
- Now in Android reference app: https://github.com/android/nowinandroid
