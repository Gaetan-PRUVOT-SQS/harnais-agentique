---
name: c-systems
description: 'Use when writing or reviewing C for systems, embedded or OS work: safe coding rules, strict tooling, modern CMake, cross-compilation, freestanding limits. Complements c-bas-niveau.'
---

# C systems, integration and OS development

## Language level
- Portable system C follows `posix`: `-std=c17 -D_POSIX_C_SOURCE=202405L`. C23 only when the project already pinned every target compiler. `c-bas-niveau`, `osdev-c`, `gestion-memoire` and `posix` win on conflict with this skill, except layout and forbidden constructs: le code C respecte la norme 42, seul le bandeau 42 est exclu. The only accepted norminette error is `INVALID_HEADER`. Include guards stay. Do not write the 42 banner. The CMake section applies when the project already uses CMake; a Makefile project stays on Make.
- Name `-std=c17` on the command line. `-std=c23` only in the case already stated above. GCC 15 defaults to `gnu23`,
  so an unpinned build can change behaviour after a compiler upgrade.
- Use C23 features only when pinned: `nullptr`, `bool` as keyword, `[[nodiscard]]`, `[[maybe_unused]]`,
  `constexpr` objects, `typeof`, `#embed`, `<stdckdint.h>` checked arithmetic.
- Avoid GNU extensions in portable code; isolate them behind macros in one header when needed (kernel code is the exception).

## Coding rules
- SEI CERT C is the default rulebook (focus: MEM, STR, INT, ARR, EXP, ERR, FIO, CON).
- MISRA C:2025 when the project is safety related or the customer asks for it; otherwise use it as awareness
  (no dynamic allocation after init, single exit discipline is optional, explicit casts, no implicit int conversions).
- Fixed width types from `<stdint.h>`, `size_t` for sizes and indexes, `bool` from C23 or `<stdbool.h>`.
- Every integer operation that can overflow on external input is checked (`ckd_add`, or explicit range checks).
- `const` by default on pointer parameters, `static` for everything not exported, one definition per symbol.
- No VLAs, no `gets`, no `strcpy`/`strcat`/`sprintf` on untrusted sizes; use `snprintf` and check its return value.
- Declare, then assign on the next line. Norminette rejects `DECL_ASSIGN_LINE`, so neither `int x = 0` nor `= {0}` on the declaration. It also rejects `for`, `switch`, `goto`, ternaries and function-like macros. Use `while`.

## Memory handling
- Ownership is written down for each function in the project's justification file or in the names (`*_take`, `*_borrow`, `*_free`): who allocates, who frees.
- One allocation, one matching free on every path. `goto` is rejected (`GOTO_FBIDDEN`): each error path frees what it owns and returns.
- Set pointers to `NULL` after free when they stay in scope; never free memory you did not allocate.
- Check every `malloc`/`calloc`/`realloc` result; `realloc` into a temporary pointer.
- Prefer `calloc(n, size)` over `malloc(n * size)` (overflow check built in).
- Bounds: pass buffer and length together (`buf, len`) or use a small span struct.
- Embedded and kernel: static pools or arenas, no general heap after init unless designed for it.
- Secrets (keys, passwords, tokens) are wiped as soon as they are no longer needed with `memset_explicit` (C23),
  `explicit_bzero` or the platform equivalent; a plain `memset` before `free` can be removed by the optimizer. For
  crypto code, check the release build's assembly to confirm the wipe is still there.
- Code handling secrets has no branch, loop bound or array index that depends on the secret value, and compares
  secrets with a constant-time function (`CRYPTO_memcmp`, `timingsafe_bcmp` or a reviewed equivalent).

## Error handling convention
- Functions return `int` status (0 success, negative errno style code) or a project `enum status`; outputs go through
  pointer parameters. Mark status returning functions `[[nodiscard]]` (or `__attribute__((warn_unused_result))`).
- Never ignore a return value from I/O, allocation, locking or syscalls; `(void)` cast only when the ignored result is justified in the justification file.
- Keep `errno` reads immediately after the call that sets it.
- Log once at the boundary that decides what to do, not at every level.

## Headers
- Include guards (`#ifndef` / `# define` / `#endif`). `#pragma once` is not a 42 guard. Each header compiles on its own (include it first in its .c). The 42 banner is not written.
- Headers declare, they do not define (except `static inline` helpers and macros).
- Include what you use, nothing more; forward declare structs to cut dependencies; opaque types for public APIs.
- Public headers live in `include/<project>/`, private ones next to the sources.
- Macros: uppercase, parenthesize arguments and the whole body, prefer `static inline` functions and `enum` constants.

## Compiler flags (OpenSSF hardening guide)
- AGENTS.md wins. Pour tout fichier C : le code C se compile avec gcc -Wall -Wextra -Werror. Other warnings may be added. A cross gcc is still gcc. clang is for analysis and for sanitizers that exist only there. It does not replace this compile. These flags stay on C that a downstream packager rebuilds.
- Extra warnings: `-Wpedantic -Wformat=2 -Wconversion -Wsign-conversion -Wshadow -Wimplicit-fallthrough
  -Wstrict-prototypes -Wmissing-prototypes -Werror=implicit -Werror=incompatible-pointer-types -Werror=int-conversion`.
- Hardening for hosted release builds: `-O2 -D_FORTIFY_SOURCE=3 -fstack-protector-strong -fstack-clash-protection
  -fcf-protection=full` (x86_64) or `-mbranch-protection=standard` (AArch64), `-fPIE -pie -Wl,-z,relro,-z,now
  -Wl,-z,noexecstack`. GCC 14+ offers `-fhardened` as a shortcut.
- Debug and test builds: `-O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined` (ASan + UBSan),
  separate builds for `-fsanitize=thread` (threads) and `-fsanitize=memory` (clang only).
- Run Valgrind memcheck on test binaries that are not built with ASan (they do not mix).

## Static analysis and fuzzing
- clang-tidy with a committed `.clang-tidy` (`bugprone-*`, `cert-*`, `clang-analyzer-*`, `misc-*`, `readability-*`
  with noisy checks disabled explicitly), run on `compile_commands.json`.
- cppcheck with `--enable=warning,style,performance,portability --error-exitcode=1`, plus the MISRA addon when relevant.
- scan-build (Clang static analyzer) or GCC `-fanalyzer` in CI on a nightly basis. For machine-readable diagnostics use
  SARIF (`-fdiagnostics-format=sarif-file` or `-fdiagnostics-add-output=sarif`); GCC 16 removed the JSON format.
- Do not clang-format C or headers. Norminette checks that layout. Other languages keep the project formatter, checked in CI, not discussed in review.
- Fuzz every parser and every function reading external input: libFuzzer harness (`LLVMFuzzerTestOneInput`) built with
  ASan + UBSan, AFL++ for binaries; keep the corpus in the repo, add crashing inputs as regression tests.
- A fuzzing harness accepts every input size (check `size` first), never calls `exit()`, joins its threads, frees
  what it allocates, and resets global state at each iteration. It stays deterministic: seed any PRNG from the input,
  fake time and PIDs, no network or `/dev/urandom`. One input format per harness, no logging, aim for thousands of
  executions per second. Run it with `-fsanitize=fuzzer,address,undefined`.
- When a checksum, magic value or random seed blocks the fuzzer, bypass only that check behind
  `#ifndef FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION`, document why it is safe, and compare coverage before and after.
  Check the code after the bypass for assumptions that would create false crashes. A CI check fails any release build
  where that macro is defined.

## Modern CMake (target based)
- `cmake_minimum_required(VERSION 3.25)` or newer; CMake 4 removed compatibility with policies older than 3.5.
- Everything is a target: `add_library`, then `target_include_directories`, `target_compile_options`,
  `target_compile_features(foo PUBLIC c_std_17)` with the right PUBLIC / PRIVATE / INTERFACE scope.
- No global `include_directories`, `add_definitions` or `CMAKE_C_FLAGS` edits in project files.
- Warnings and sanitizers through an `INTERFACE` target or a preset, so they apply to your code only.
- `CMakePresets.json` for debug, asan, release and each cross target; `CMAKE_EXPORT_COMPILE_COMMANDS ON`.
- Dependencies through `find_package` or `FetchContent` pinned to a tag and hash; install and export targets for libraries.
- Tests through CTest (`add_test`, labels `unit` / `integration`), `ctest --output-on-failure`.

## Cross-compilation
- One toolchain file per target (`cmake/toolchains/arm-none-eabi.cmake`) setting `CMAKE_SYSTEM_NAME`,
  `CMAKE_SYSTEM_PROCESSOR`, compilers, `CMAKE_SYSROOT`, and `CMAKE_FIND_ROOT_PATH_MODE_*`.
- Bare metal: `CMAKE_SYSTEM_NAME Generic` and `CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY`.
- Host tools needed during the build are built in a separate host build, not with the cross compiler.
- Run cross-built unit tests under QEMU user mode (`CMAKE_CROSSCOMPILING_EMULATOR`) so CTest works unchanged.

## Freestanding and kernel code
- `-ffreestanding -nostdlib -fno-builtin` (re-enable chosen builtins explicitly), `-fno-stack-protector` unless you provide
  `__stack_chk_fail`, `-fno-pic` or a deliberate PIC model, `-mno-red-zone` on x86_64 kernels (interrupts clobber it),
  `-mgeneral-regs-only` or `-mno-sse -mno-mmx` when FPU state is not saved.
- Only freestanding headers are available (`stddef.h`, `stdint.h`, `stdbool.h`, `stdarg.h`, `limits.h`, `float.h`);
  provide your own `memcpy`, `memset`, `memmove`, `memcmp` because the compiler emits calls to them.
- Linker script owns the memory map: sections, alignment, `_start`, BSS boundaries; keep it under review like code.
- `volatile` only for MMIO and memory touched outside the compiler's view; use explicit barriers and atomics for ordering.
- Keep architecture specific code in `arch/<name>/`, everything else portable and unit testable on the host.
- Test in QEMU in CI: boot the image headless (`-nographic -serial stdio`), use `isa-debug-exit` or semihosting so the
  test result becomes the process exit code, and add a timeout.

## Unit testing
- Unity (+ CMock for mocks) or CMocka for C; Check is fine for hosted POSIX code; GoogleTest when the project already has C++.
- Test pure logic on the host with sanitizers; use link-time substitution or function pointers to fake hardware.
- One test file per module, deterministic, no sleeps; boundary values on every size and index.
- Coverage with gcov/gcovr or llvm-cov, reported per change.

## Documentation
- No Doxygen blocks: contracts (`@return` codes, ownership, thread safety) go in `docs/justifications/`, the code reads through its names.
- README with build commands for each preset and target. Memory maps and ABI decisions go in `docs/justifications/`. A repo that already keeps ADRs updates that folder too.

## Reproducible builds
- Pinned toolchain (container image or SDK with version), pinned dependencies, no network during the build.
- `SOURCE_DATE_EPOCH`, `-ffile-prefix-map=$(pwd)=.`, no `__DATE__`/`__TIME__`, sorted inputs, `ar D` deterministic archives.
- Verify by building twice in different directories and comparing hashes.

## Commits and approval
- Commits are short and simple, in French (`Débordement RX de l'UART traité avant la lecture`).
- Nothing is pushed, merged, flashed to shared hardware or released without explicit approval from the user.

## Sources
- SEI CERT C Coding Standard: https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard
- MISRA C:2025: https://misra.org.uk/product/misra-c2025/
- OpenSSF compiler hardening guide: https://best.openssf.org/Compiler-Hardening-Guides/Compiler-Options-Hardening-Guide-for-C-and-C++.html
- GCC 15 changes (C23 default): https://gcc.gnu.org/gcc-15/changes.html
- GCC 16 changes (JSON diagnostics removed, more C2y features): https://gcc.gnu.org/gcc-16/changes.html
- CMake toolchains and presets: https://cmake.org/cmake/help/latest/manual/cmake-toolchains.7.html
- Clang sanitizers and libFuzzer: https://clang.llvm.org/docs/AddressSanitizer.html, https://llvm.org/docs/LibFuzzer.html
- AFL++: https://aflplus.plus/
- Reproducible builds: https://reproducible-builds.org/docs/
- OSDev wiki (freestanding, red zone, linker scripts): https://wiki.osdev.org/
