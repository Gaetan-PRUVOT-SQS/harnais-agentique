---
name: general-engineering
description: Use for design decisions, docs, errors and logs, dependencies, versions, basic security and performance in any language. Complements pratiques-dev-senior; that one wins on conflict.
...
---

# General software engineering

## Design principles, applied with judgment
- Single responsibility: a module has one reason to change. Split when a file needs "and" to describe it.
- Open/closed: extend through new implementations or configuration when a variation point is real; do not build plugin
  systems for a second case that does not exist yet.
- Liskov: a subtype must honour the contract of its parent (inputs, outputs, errors). If you need `instanceof` checks,
  the abstraction is wrong.
- Interface segregation: small interfaces shaped by the caller's needs.
- Dependency inversion: business logic depends on interfaces it owns; infrastructure implements them. Inject dependencies
  through constructors or parameters.
- KISS and YAGNI beat speculative generality. Duplicate twice, abstract on the third occurrence when the cases truly match.
- Prefer composition over inheritance, immutable data, pure functions for logic, and explicit names over comments.

## Before and during a change
- Write down the assumptions the change rests on before touching code. When a request can be read in more than one
  way, list the readings and pick one with a reason; when the choice changes behaviour, security or data, ask instead
  of guessing.
- Say so when a simpler approach exists, or when the request conflicts with the code, a decision record or a security
  rule. On real confusion, stop and name what is unclear.
- Keep the diff on task: every changed line traces back to the request. Leave neighbouring code, comments and
  formatting alone and follow the local style.
- Remove what your own change made unused (imports, variables, functions, files). Dead code that was already there is
  reported, not deleted in the same change. Line-level pass: `revue-minutieuse`.
- A security problem on the flow this change touches is fixed in the same turn (`norme-cybersecurite`). An unrelated
  finding is still reported, with its severity, and fixed in its own change. Nothing is left silent.
- Once it works and is tested, look again for the shorter version. If a few dozen lines can do what a few hundred do,
  rewrite before asking for review.
- Simplicity never removes input validation, authorization checks, error handling at trust boundaries or security
  logging. They are part of the minimum.
- Deletion test for an abstraction: imagine removing it. If the complexity disappears, it was a pass-through; if it
  comes back in every caller, it earns its place. Add a seam only when at least two real implementations use it.

## Architecture boundaries
- Keep the domain (rules, entities, use cases) free of framework, database and UI types.
- Dependencies point inward: UI and infrastructure depend on the domain, never the reverse.
- Adapters at the edges (HTTP, DB, queues, file system) translate to and from domain types and validate input.
- Organize code by feature or bounded context first, then by layer inside it.
- Make boundaries checkable: module visibility, lint rules on imports, or architecture tests.
- Start as a well structured modular monolith; split into services only for a clear scaling, team or deployment need.

## Code review checklist
1. Does the change do what the ticket or description says, and nothing unrelated?
2. Is it covered by tests at the right level, including edge cases and error paths?
3. Are names, structure and size easy to follow? Can anything be deleted?
4. Errors: are failures handled, reported with context, and never swallowed?
5. Security: input validated, output encoded, authorization checked, no secrets, no new risky dependency.
6. Performance: no obvious N+1 queries, unbounded loops, loading everything in memory, or blocking calls on hot paths.
7. Compatibility: public API, database schema, config and file formats changed in a backward compatible way, or versioned.
8. Observability: useful logs and metrics for the new behaviour, no noise.
9. Docs updated (README, `docs/justifications/`, changelog) when behaviour or setup changed. A repo that already keeps ADRs updates that folder too.
10. Design smells, as judgement calls (low or observation, and the repository's own standards win): names that hide
    what a thing does, logic duplicated inside the change, a function that mostly works on another object's data, the
    same group of parameters always travelling together, a raw string or number standing for a domain concept, the
    same switch repeated, one change scattered over many files, one file changed for unrelated reasons, abstraction
    for needs nobody has, long call chains, layers that only pass calls through, a subclass ignoring what it inherits.
- Review small PRs (under about 400 changed lines); comment on the code, not the author; separate blocking issues from suggestions.

## Documentation
- README: what it is, how to install, run, test and deploy, configuration variables, where to get help. Keep the commands working.
- Structural decisions go in `docs/justifications/<slug>.md` (`justifier-choix-techniques`). A repo that already keeps ADRs in `docs/adr/` keeps that folder. One decision per record, superseded by a new one rather than rewritten.
- No comments in code, or very few, short, in French; names carry the meaning and the why goes in `docs/justifications/`. Never commented-out code. Public API contracts and examples go in the README or the justification file.
- CHANGELOG generated from commits or kept by hand following Keep a Changelog.
- Once a project has its own vocabulary, keep a short `GLOSSARY.md`: one line per term, its meaning, and the words to
  avoid. Use those terms in code, tests, tickets and PRs so names stay consistent and exchanges stay short.
- A repository worked on by coding agents keeps one short, hand-written `AGENTS.md` at the root, plus nested ones only
  where a sub-project really differs: exact build, test and lint commands, environment quirks, conventions that differ
  from the language defaults, paths an agent must not change, and where the spec and decision records live. Leave out
  what the code already shows. Each line should prevent a real mistake: prune the file when the agent goes wrong, and
  turn any rule that must hold every time into a hook or a CI check, because the file is advice. When a tool wants
  its own file name, point it to `AGENTS.md` instead of keeping a second copy. The file is versioned, reviewed like
  code and holds no secret.

## Versioning
- Semantic Versioning for anything others depend on: MAJOR for breaking changes, MINOR for compatible features, PATCH for fixes.
- Deprecate before removing: mark, document the replacement, keep it for at least one minor release.
- Version APIs explicitly (URL or header) and keep old versions until clients have moved.

## Error handling
- Fail fast on programmer errors (assertions, invalid state); handle expected failures (network, user input, missing file)
  explicitly and close to where a decision can be made.
- Never swallow errors. Either handle, or add context and propagate (`wrap` with cause).
- Use typed errors or result types for expected failures; exceptions or panics for the unexpected.
- Clean up resources on every path (`finally`, `use`, `defer`, RAII). In C, norme 42 forbids `goto`, so each error path frees what it owns and returns.
- User-facing messages are helpful and safe; internal details go to logs, not to the screen or API response.
- Mishandling exceptional conditions is now its own OWASP Top 10 category: fail closed, not open.

## Logging
- Structured logs with level, timestamp, component, correlation or trace id, and stable message keys.
- Levels: ERROR needs action, WARN is unexpected but handled, INFO is a business-relevant event, DEBUG is for development.
- Log once per error, at the boundary that handles it. No secrets, tokens, passwords or personal data; redact by default.

## Security basics (OWASP Top 10:2025)
- Broken access control: deny by default, check authorization on the server for every request and every object.
- Security misconfiguration: secure defaults, no debug in production, minimal exposed surface, security headers.
- Software supply chain failures: pinned and reviewed dependencies, lockfiles, SBOM, trusted build pipeline.
- Cryptographic failures: TLS everywhere, standard libraries only, strong password hashing (Argon2id, bcrypt), no home-made crypto.
- Injection: parameterized queries, safe APIs, output encoding per context.
- Insecure design: threat model new features that touch auth, money or personal data.
- Authentication failures: MFA or passkeys, rate limiting, secure session handling.
- Integrity failures: verify signatures of updates and artifacts, no unsafe deserialization of untrusted data.
- Logging and alerting failures: security events logged and alerting works.
- Mishandling of exceptional conditions: errors leave the system in a safe state.
- Secrets never go in the repo, images or client bundles. Use environment variables or a secret manager, commit a
  `.env.example`, enable secret scanning and a pre-commit hook (gitleaks). If a secret leaks, rotate it first, then clean history.

## Dependency hygiene
- Add a dependency only when it saves real work; check maintenance, licence, size, known vulnerabilities and transitive weight.
- Commit lockfiles, pin versions, update regularly in small batches through automated PRs, read changelogs for majors.
- Remove unused dependencies; audit in CI (`npm audit`, `pip-audit`, OWASP Dependency-Check, `gradle dependencyCheck`).
- Before adding or keeping a dependency, also check: archived or unmaintained upstream, a single maintainer able to
  publish, install-time scripts. Data you could not obtain is "not assessed", never "clean".
- A package name proposed by a coding agent, or found in generated code, is checked before install: it exists in the
  official registry under that exact name, its source repository and publisher are the project you expect, and its
  age, downloads and release history look like a real project. Existing is not enough, since invented names get
  registered by attackers. Read the lockfile diff for every new direct and transitive package.

## Performance mindset
- Measure before optimizing: profile, benchmark, and set a budget (latency, memory, bundle size, startup time).
- Fix the algorithm and the data access first (complexity, N+1 queries, missing indexes, chatty APIs), then micro-optimize.
- Cache with a clear invalidation rule and a size limit; paginate and stream large data.
- Keep performance tests or benchmarks for hot paths so regressions show up in CI.
- For tricky algorithms, write the plain version that is obviously correct first. The optimized version must return
  the same results on the same inputs, checked by differential or property tests, and the plain version stays in the
  test suite as the reference.
- Weigh complexity against gain: a tiny speedup that adds a lot of hard code is not worth it, while the same result
  with less code is always a win.

## Commits and approval
- Commits are short and simple, one logical change each, with a natural description of what changed and why
  (`Calcul de la taxe sorti de la facturation`).
- Nothing is pushed, merged, released or deployed without explicit approval from the user.
- Keep structural changes (rename, move, extract, reformat) and behaviour changes in separate commits, structural
  first, with the tests green before and after each. The behaviour commit of a long agent diff can then be reviewed
  on its own.

## Sources
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP Cheat Sheet Series: https://cheatsheetseries.owasp.org/
- Semantic Versioning 2.0.0: https://semver.org/
- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Keep a Changelog: https://keepachangelog.com/
- ADRs (Michael Nygard): https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions and https://adr.github.io/
- Google engineering practices, code review: https://google.github.io/eng-practices/review/
- The Clean Architecture (Robert C. Martin): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- OpenSSF Concise Guide for Evaluating Open Source Software: https://best.openssf.org/Concise-Guide-for-Evaluating-Open-Source-Software
- Martin Fowler, Refactoring, 2nd edition, chapter 3 (code smells): https://martinfowler.com/books/refactoring.html
