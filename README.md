# Harnais agentique

English · [Français](README.fr.md)

A working harness for coding agents: permanent rules, guardrails executed
as hooks, ten method skills, 5 read-only subagents and a verifier that
checks the whole thing. Built so that an agent can work in automated mode
without turn-by-turn supervision: what it claims is proven, what is
dangerous is intercepted before it runs, and what is delivered is
re-checked before handover.

## The problem addressed

A coding agent left in autonomy fails repeatedly and predictably:

- it **narrates instead of proving**: "the tests pass" with no output
  read back, "fixed" with no diff checked;
- it **touches secrets** ("I only looked at the `.env`") and may copy
  them into a deliverable;
- it runs **irreversible commands** (`rm -rf`, disk writes, firmware
  flash, `git reset --hard`) without understanding the scope;
- it **drifts from its rules** as context grows: the instructions of the
  first turn do not survive the tenth file;
- with several agents, **they write in parallel** to the same files and
  correct each other in loops.

The problem addressed: **delegating real work to an agent, in automated
mode (minimal intervention), without losing secrets, local data,
repository integrity, or the truth of the announcements.** The answer is
not a better prompt: it is a short behavioral contract (AGENTS.md)
**reinforced by machine checks** the agent cannot bypass because they do
not run inside it.

## Architectural design

One source of truth, engines wired to it:

```
            ┌───────────────── engine A (ZCode etc) ─────────────────┐
            │  instructions ← AGENTS.md link                       │
            │  skills/agents ← symbolic links                      │
            │  events → hooks registered at the engine             │
            └──────────────────────────┬───────────────────────────┘
                                       │ AGENT_CONFIG_ROOT=<copy of the harness>
~/.agents (one copy per engine)        ▼
├── AGENTS.md            permanent rules: the single source of rules
├── regles/bas-niveau.md OS/kernel rules: hardware spec cited,
│                         proof by steps (host, QEMU, machine)
├── DESIGN.md            default visual contract for any UI
├── skills/              10 method skills (frontmatter name + description)
├── agents/              5 read-only subagents (no shell)
├── hooks/dispatch.py    SINGLE ENTRY POINT of all hooks
└── verifier             checks the whole config
```
(harness memory, history and justifications: with the author, never
published)

**Cycle of a turn.** The engine triggers the hooks; `dispatch.py`
(translating the host engine's tool names along the way) routes:

| Event | Check | Effect |
|---|---|---|
| `PreToolUse` | guard: secrets (raw **and resolved** paths, extended catalog), recursive `rm`, disk/firmware writes, force-push, disable markers, repository writer lock | `deny` or `ask` **before** execution |
| `PostToolUse` (writes) | shellcheck, checkbashisms, shfmt/ruff, cyber scan | reported during the turn; quality failures **hold the Stop** until fixed |
| `Stop` | cyber scan, gitleaks and semgrep on modified projects, regression tests, oracle, config verifier, harness state (degradation, interruption mark, locks) | handover does not happen while a check fails |
| `SessionStart` / `UserPromptSubmit` | session state, re-reading of the engine record, lock heartbeat, one-shot triggers | cleanup, routing, degradation alert |

**Subagents.** The 5 agents (`architecte`, `auditeur-securite`,
`chercheur`, `explorateur`, `relecteur`) are read-only at the
**technical** level: no shell (Read, Grep, Glob, web for the
`chercheur`), tool list imposed by the engine and checked by the
verifier. They return a report (≤ 2,000 tokens) that the main thread
re-checks with fresh evidence. One writer per repository, never two.

**One engine per copy, one writer per repository.** Each engine holds
its own copy of the harness (cloned through git) and exports
`AGENT_CONFIG_ROOT` to its root; copies synchronize through the upstream
git repository. A per-repository writer lock (session, 6 h expiry,
dead-lock takeover, refreshed at each owner turn) refuses a write from a
session on a repository already held by another. Two engines on the same
copy = two writers = forbidden (and detected).

**Context budget.** The skills listing is measured by the verifier
(ceiling 230,000 characters; the ten published skills take a tiny
fraction of it): discovery cannot silently overflow the context.

**Ten method skills**: the discipline of the agent itself, not domain
tools: `pratiques-dev-senior` (senior level, PERMANENT),
`revue-minutieuse` (every line of a change is required by a criterion),
`iso-29119` + `tests-regression-auto` + `tests-locaux` (the test
doctrine and its execution), `validation-gate` and `revue-validation`
(the verdict only lands on evidence), `justifier-choix-techniques` (one
document per decision, rejected alternative written down),
`pratiques-git-github` (commit hygiene, zero tool trace),
`multi-agent-orchestration` (one writer, the others report). The other
skills of the author (domain stacks and work tooling) are not published.

## System limits

Stated frankly:

- **Fail-open at the call, fail-closed at the turn.** The guarantee
  rests on the hook running; two cases must be told apart.
  *Registration drift* (hook disabled, command modified, timeout
  shortened, event removed) is caught twice: by the verifier, which
  checks the exact registration of each event, and by `dispatch.py`,
  which re-reads the engine record at each turn and holds the `Stop` as
  long as an expected event is missing. A hook killed *at run time*,
  timeout exceeded (guard 10 s, Stop 400 s), crash, or an event that
  never fires, cannot prevent the call that triggered it (after the
  timeout, it is the engine, not the harness, that decides to run the
  tool): the guard sets a mark before its verdict and lifts it after;
  the mark survives the killed hook and the turn's `Stop` blocks until
  the action is resumed under control. Still out of reach: the call
  already executed, and total deactivation (no hook active at all; only
  a verifier pass lifts it). An engine without a hook mechanism is not
  protected at all.
- **One layer, not two.** On engines that expose a permission list
  (static denials), the guard adds itself to it and the denial holds
  even with a killed hook. On engines that do not expose one, the guard
  is the only layer; making native permissions a verifier-checked
  install requirement remains open work.
- **The control plane protects itself, without being out of reach.**
  The disable markers (`disable-*`) can no longer be created, modified
  or deleted by the agent (guard denial, including through shell
  redirection); the verifier lists the existing ones and the author
  sets them by hand. The rest of the harness stays writable by the
  agent (by design, it maintains its config on request): full
  separation of controller and controlled would need a dedicated
  account (open work).
- **Subagent read-only is technical, not declarative.** The 5 agents
  no longer have a shell: Read, Grep, Glob (web for the `chercheur`),
  list imposed by the engine; the verifier refuses Bash in an agent.
  What the agents lose (git log, find), the brief from the calling
  thread must supply.
- **Test suites run project code under the user account.** Their
  environment is cleaned (no more secret variables or auth agent
  sockets) and their external network is cut with bwrap
  (`--unshare-net`, loopback up: local integration tests pass; bwrap
  missing = explicit warning). Remaining: no dedicated account, full
  disk access.
- **The Stop only covers the recognized runner.** A project without a
  recognized test suite has no regression gate; the oracle only bites
  if the project provides one.
- **Language-typed gates.** Format and lint target shell and Python
  (shfmt, shellcheck, checkbashisms, ruff); C depends on the project
  rules (`-Wall -Wextra -Werror`); project secrets go through gitleaks
  at Stop and web/python code through semgrep (ERROR alerts, python +
  OWASP top ten rules); other languages have no dedicated SAST.
- **Normal push is contractual.** Force-push is confirmed by the guard;
  an ordinary push is not mechanically intercepted: it relies on the
  rule "no push without a request".
- **Reasoning quality stays out of machine reach.** The harness
  constrains actions and checks artifacts; it does not prove the
  relevance of a design. Fresh evidence is a behavioral contract for
  everything that cannot be mechanically checked.
- **Cost.** ~2 min of verifier when the config changes (Stop), ~50 KB
  of rules loaded at every session, one PreToolUse check per tool call.
- **Drift between copies.** One engine per copy protects simultaneous
  writes, reinforced by a per-repository writer lock (refusal to write
  to a repository already held by another session, 6 h expiry); copies
  diverge if they are not synchronized through git.
- **Engine scope.** The event vocabulary, the matchers (regex) and the
  timeouts depend on the engine; the adaptation is written in the copy,
  not in the common harness.

**Open work items** (acknowledged, not implemented): dedicated account
and filesystem permissions for test suites (the network is already
cut), native engine permissions as an install requirement, upstream
provenance of skills per commit (the lock already checks the local
fingerprint of every imported skill), file opening without symlink
following at the engine side.

## Threat model

**Assets to protect.** Local secrets (`.env`, SSH keys, credentials),
workstation integrity (disks, firmware, data outside repositories),
uncommitted local work, confidentiality of the harness memory (facts
about the machine and the projects), truthfulness of deliverables
(announced tests, published content).

**Adversary.** The agent itself, by inadvertence, by content injection
(a read file containing instructions), or by two concurrent instances.
**Not** an attacker who controls the machine or the engine: against
them, the harness offers nothing (see out of model).

| Risk | Interception | What remains uncovered |
|---|---|---|
| Reading/exfiltrating a secret | guard `deny`: raw **and resolved** paths (symlinks), interpreter patterns (`python -c open(".env")` and close ones), extended catalog (kube, docker, gcloud, npmrc, pypirc, private `.pem`); gitleaks on what is written | a secret already copied outside the patterns; the call executed before a killed hook (the interruption mark holds the turn) |
| Irreversible command (`rm -rf`, `dd`, firmware) | guard `ask`/`deny` before execution | nothing, as long as the hook runs |
| Loss of local work (`git clean`, `reset --hard`) | repository guard: uncommitted work detected | commits already force-pushed (confirmed only) |
| Silent deactivation of a check | `disable-*` markers refused by the guard (creation, modification, deletion, redirections) and listed by the verifier; an event removed from the engine is detected at every turn, `Stop` held | total deactivation: no hook can run to notice it |
| A subagent writing despite "read-only" | no more shell in the agents (tool list imposed by the engine); the verifier refuses Bash in an agent | the calling thread stays the single writer; its own shell calls remain under the guard |
| Project code executed by the automation (test suites) | cleaned environment (secret variables masked, auth sockets removed), external network cut (bwrap) | full disk access of the user account, no dedicated account |
| Secret in the deliverable | gitleaks + semgrep on the harness (PostToolUse and Stop); gitleaks + semgrep (ERROR, web/python) on modified projects at Stop | scanner false negatives, SAST limited to covered languages |
| Green tests announced without proof | Stop gate re-runs the suite; tests without assertions block; oracle tests a false implementation; shellcheck/format hold the Stop until fixed | suites not recognized by the runner |
| Injection through read content | subagents without shell, re-check by the thread, secrets refused even when "requested" | benign instruction executed without a trigger (no sandbox) |
| Two engines or sessions on a repository | one engine per copy + `AGENT_CONFIG_ROOT`; per-repository writer lock (refusal before writing, 6 h expiry); divergence detected by the verifier | writes through raw shell (the lock protects the writing tools); desynchronization without git pull |

**Out of the model**: engine or OS compromise, network exfiltration by
a process that bypasses the hooks, physical attacks, side channels. The
harness is a control of the agent's actions, not a confinement: there
is no sandbox.

## Prerequisites

- Linux (written and tested on Ubuntu), `bash`, `git`.
- Python ≥ 3.11 (`tomllib`), with `pytest`.
- Tools of the checks: `jq`, `ruff`, `shellcheck`, `checkbashisms`
  (devscripts package), `shfmt`, `gitleaks`, `semgrep`. A missing tool
  is reported ("do not announce a validation"); the verifier never lies
  about what it did not run. On the first pass, semgrep downloads its
  rules (network), then keeps them cached.
- `bwrap` (bubblewrap), recommended: cuts the external network of test
  suites while leaving the filesystem and loopback intact. Without it,
  the runner warns and continues without isolation.
- A hook-capable engine (Claude Code protocol: ZCode, Claude Code,
  Grok) for the dynamic part. Rules, skills and agents can be used
  without an engine.
- ~12 MB (104 files).

## Installation

```sh
git clone <this repository> ~/.agents
~/.agents/verifier --rapide        # must end green before continuing
```

Wire your engine: **one engine per copy**, never two writers on the
same repository:

**Rules**: link `AGENTS.md` into the engine instructions.

**Skills and agents**: symbolic links (many engines discover
`~/.agents/skills` directly):

```sh
mkdir -p ~/.yourengine/skills ~/.yourengine/agents
for d in ~/.agents/skills/*/; do ln -s "$d" ~/.yourengine/skills/"$(basename "$d")"; done
for a in ~/.agents/agents/*.md; do ln -s "$a" ~/.yourengine/agents/; done
```

**Hooks**: register `dispatch.py` on the events, exporting
`AGENT_CONFIG_ROOT` to the harness root. Full example for an engine in
the Claude Code format:

```json
{
  "hooks": {
    "enabled": true,
    "events": {
      "SessionStart": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/me/.agents python3 -E -s /home/me/.agents/hooks/dispatch.py SessionStart",
          "timeout": 15 }] }
      ],
      "UserPromptSubmit": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/me/.agents python3 -E -s /home/me/.agents/hooks/dispatch.py UserPromptSubmit",
          "timeout": 30 }] }
      ],
      "PreToolUse": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/me/.agents python3 -E -s /home/me/.agents/hooks/dispatch.py PreToolUse",
          "timeout": 10 }] }
      ],
      "PostToolUse": [
        { "matcher": "Write|Edit|MultiEdit|NotebookEdit|ApplyPatch",
          "hooks": [{ "type": "command",
            "command": "AGENT_CONFIG_ROOT=/home/me/.agents python3 -E -s /home/me/.agents/hooks/dispatch.py PostToolUse",
            "timeout": 150 }] }
      ],
      "Stop": [
        { "hooks": [{ "type": "command",
          "command": "AGENT_CONFIG_ROOT=/home/me/.agents python3 -E -s /home/me/.agents/hooks/dispatch.py Stop",
          "timeout": 400 }] }
      ]
    }
  }
}
```

The protocol spoken by `dispatch.py`: JSON on standard input, JSON
output (`decision`, `permissionDecision`, `additionalContext`) or exit
code (`2` = block).

**Content deliberately absent** from this repository: the other skills
of the author (personal work tools), `memory/`, `BRAIN.md`,
`HISTORIQUE.md`, `docs/justifications/`, `archives/`: tools, personal
data, machine state and internal justifications are not published. Only
the agentic brain (rules, guardrails, verifier, agents and method) is
shared. The public test suite is adjusted accordingly (tests removed or
skipped when the target tool is absent).

## Validation

Four stages, all replayable:

```sh
# 1. The harness suite (126 tests): structure, guard, gates, verifier.
python3 -m pytest tests/

# 1 bis. The hooks suite (110 tests): guard, gates, fail-closed,
# writer lock, markers, symbolic links, cleaned environment.
python3 -m pytest hooks/verify.py

# 2. The full verifier.
./verifier                 # or --rapide (~2 min)

# 3. End to end, on real payloads:
echo '{"tool_name":"Read","tool_input":{"file_path":"'"$HOME"'/.ssh/id_rsa"},"cwd":"'"$HOME"'"}' \
  | AGENT_CONFIG_ROOT="$HOME/.agents" python3 -E -s ~/.agents/hooks/dispatch.py PreToolUse
# expected: {"permissionDecision":"deny", ...}

echo '{"session_id":"test","stop_hook_active":false}' \
  | AGENT_CONFIG_ROOT="$HOME/.agents" python3 -E -s ~/.agents/hooks/dispatch.py Stop
# expected: empty JSON output, exit code 0
```

The verifier checks: skill and agent frontmatter and links, listing
budget, hooks in isolated python (`python3 -E -s`, exact timeouts),
secret refusals, disable markers (`disable-*`), fingerprints of
imported skills (lock check; "not run" if the repository publishes
none, like this one), gitleaks, semgrep, ruff, shellcheck,
checkbashisms, pytest suite. Machine-bound checks report "not run" when
the target file is absent: the repository is green on any machine,
without lying about what did not run.

One design detail: the oracle gate deliberately tests a **false
implementation** (`hooks/oracle_vide.py`) to prove the tests bite: a
test that cannot tell true from false is worth nothing.

### 4. Clean install, replayable

```sh
git clone <this repository> fresh-harness
cd fresh-harness && mkdir home-isolated && HOME="$PWD/home-isolated" ./verifier --rapide
# expected: 0 failures; engine-bound and local tooling checks report
# "not run" (five at publication: engine not wired, lock absent,
# pytest/state depending on the machine).
```

On the author's machine, the live engine is wired to another copy of
the harness: the same checks fail there (KO): the verifier compares the
engine record to ITS root, it does not lie about what it sees.

## Experimental results

Observations from real use, not a controlled benchmark.

**Field.** One month of daily use in personal development: 248
sessions across 33 projects. The ten method skills published here are
extracted from a much larger working copy; in all cases the listing is
measured at every verifier pass and stays well below the 230,000
character ceiling.

**What happens in development, turn after turn.**

- **`PreToolUse` guard on every tool call**: response under 1 s for a
  10 s budget. In practice it lets normal work through without friction
  and intercepts what falls outside the frame: reading an SSH key
  denied (`permissionDecision: deny`), confirmation required before a
  recursive `rm`, a disk write or a force-push.
- **Write gates (`PostToolUse`)**: every modified shell script goes
  through shellcheck and checkbashisms (under 1 s), every file is
  formatted; a shellcheck warning holds the turn until fixed.
- **Stop**: the project regression suite is re-run at every end of turn
  on the touched files; a failed regression blocks handover. When the
  harness config changed during the turn, the `--rapide` verifier is
  added (~2 min).
- **What it costs**: ~2 min of verifier occasionally at Stop, under a
  second per tool call, a skills listing far below the ceiling.

**Measurements of the checks** (full repository, dev machine):

| Check | Duration |
|---|---|
| Hooks suite (`verify.py`, 110 cases) | ~104 s |
| Verifier tests (194 private cases, 126 public) | ~2 s |
| gitleaks | 0.9 s |
| semgrep (harness) / project SAST at Stop | 3.5 s / ~2 s |
| ruff, shellcheck, checkbashisms | under 1 s each |
| Full `--rapide` verifier | ~112 s |

**What these numbers do not say.** The coverage of the regression gates
depends on the runner recognized in each project; the behavioral part
(fresh evidence, re-checking of reports) is a contract, observed to
hold as long as the rules stay loaded and short; this is exactly what
the verifier budgets.

## License

Harness code and ten method skills: MIT (see `LICENSE`).
