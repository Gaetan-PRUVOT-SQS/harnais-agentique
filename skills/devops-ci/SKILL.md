---
name: devops-ci
description: Use when creating or reviewing CI/CD workflows, branching and release conventions, Dockerfiles, compose files, dependency updates or supply chain controls.
...
---

# CI/CD and DevOps

## GitHub Actions hardening
- Default token read-only at the top of every workflow, widen per job only:
  ```yaml
  permissions:
    contents: read
  jobs:
    release:
      permissions:
        contents: write   # only this job tags releases
  ```
  Also set the repository default "Workflow permissions" to read. A job that only needs to read Dependabot alerts gets
  `vulnerability-alerts: read` (available for `GITHUB_TOKEN` since Sept 2026), not a personal token.
- Pin third-party actions to a full 40 character commit SHA with the version as a comment
  (`uses: actions/checkout@<sha> # v7.0.1`). Check the SHA belongs to the action's own repo, not a fork.
  Enable the "require pinned SHA" actions policy where available. Let Dependabot or Renovate update the pins.
- Workflow dependency lockfiles (`.github/workflows/actions.lock`, public preview since 14 Oct 2026) also lock
  transitive actions and reusable workflows, and the "Require lockfile" policy can enforce them. They complement SHA
  pinning, they do not replace it, and locking does not make a dependency safe: review it first. The lockfile is
  generated with the `gh actions-lock` CLI extension; treat that extension as a new tool and get it vetted and approved
  before installing it anywhere.
- JavaScript actions must run on `node24`: Node 20 was removed from GitHub-hosted runners on 23 Sept 2026. Bump actions
  still declaring `node20` (for example `actions/checkout@v4`) to their current major.
- Cloud access through OIDC (`id-token: write` on that job only) with trust conditions on repo, branch or environment.
  No long-lived cloud keys in secrets.
- Secrets: scoped to environments with required reviewers for production, never echoed, never passed to steps from
  untrusted code. Mask derived values with `::add-mask::`. Rotate anything that leaked into a log.
- Treat `${{ github.event.* }}` text (titles, branch names, bodies) as untrusted: pass it through `env:` and quote it
  in shell, never interpolate it into `run:` directly.
- Avoid `pull_request_target` and `workflow_run` with checkout of PR code. If unavoidable, no secrets in that job.
  Use workflow execution protections (rulesets on actors and events) to restrict who can trigger workflows; on public
  repos the default rule disabling `pull_request_target` is enforced from 2 Nov 2026, keep it unless a reviewed
  exception exists.
- Least-privilege cache access with `cache-mode` at workflow or job level: `read` or `none` for jobs running untrusted
  code, `write` only on trusted `push` jobs. Never declare `write` on `pull_request_target`.
- `persist-credentials: false` on checkout unless a later step must push.
- Lint workflows with actionlint and audit them with zizmor in CI.
- Downloads in CI are pinned: tools by version plus SHA-256 checked before use, Python tools from a hashed requirements
  file inside a venv (`pip install --require-hashes --no-deps -r ...`), npm tools through the lockfile with
  `npx --no-install`, Playwright browsers with `npx --no-install playwright install --with-deps` so the lockfile version
  is used. No `curl | sh`, no `--break-system-packages`, no unpinned `pip install <tool>`.
- When the project already has a security stage in CI, it stays blocking: secret detection, dependency audit, SAST, hadolint when a Dockerfile exists. A tool the workflow requires and that is missing fails the stage. The local baseline is `norme-cybersecurite`. Do not add a second pipeline.
- A trusted workflow never loads or runs configuration from the repository under test with `source`, `eval` or
  `bash -c`. Read such files as data with a strict key allowlist, keep exit thresholds fixed in the script and the
  workflow, and let settings only make them stricter. Changes to pipeline policy files need a review (CODEOWNERS plus a
  required check).
- Self-hosted runners only for private repos, ephemeral, never shared with untrusted forks.

## Workflow structure
- `concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }` on PR workflows
  (not on deploy jobs, where you want queueing instead).
- `timeout-minutes` on every job.
- Caching: built-in caches of `setup-node`, `setup-java` (`cache: gradle`), `setup-python`; `actions/cache` keyed on the
  lockfile hash otherwise. Never cache secrets or build outputs that should be rebuilt. Jobs that run PR code get
  `cache-mode: read`; one trusted job on `push` to main saves the caches.
- Node version from the project: `node-version-file: .nvmrc` (exact version), not `lts/*`, so a security release is
  picked up by bumping one file. Dependabot (`.github/dependabot.yml`) covers `github-actions`, `pip` and `npm`
  with a cooldown.
- Matrix for OS or runtime versions with `fail-fast: false` when you want the full picture.
- Reusable workflows (`workflow_call`) for shared pipelines and composite actions for shared steps; version them by tag or SHA.
- The same entry point locally and in CI is the project's existing test command (`npm test`, `make test`, or the one the repo already documents). Do not add `scripts/test-pipeline.sh`. CI is never the only place a check runs.
- Upload test reports and coverage as artifacts with short retention; write a job summary.
- Path filters to skip irrelevant jobs, but keep required checks always reporting (use a final "all green" job).

## Branching and review
- Trunk based: short-lived branches (a few days at most), small PRs, feature flags for unfinished work.
- Protect the main branch with rulesets: PR required, at least one review, required status checks, linear history or
  squash merge, no force push, no deletion, signed commits if the team uses them, CODEOWNERS for sensitive paths.
- Merge queue when main is busy, so every merged commit was tested against the latest main.
- PR descriptions stay short and carry three things: what changed, shown with the smallest useful view (a diff
  sketch, a call tree or a file tree); evidence that it works (the test that failed before and passes now, command
  output, a screenshot for visual changes); and the merge risk. Say whether the change can be rolled back cleanly or
  not (data migration, deletion, public API change, key rotation), and what it could break. A change that cannot be
  rolled back needs the user's explicit approval before merging.

## Commits, versions and releases
- Follow the commit convention the repository already uses; without one, short natural French messages, no `feat:` or `fix:` prefixes. Conventional Commits only when the repository already adopted them (needed for release-please or semantic-release).
- Commits are short and simple, with a natural description of what changed; the body explains why when it is not obvious.
- Semantic Versioning: breaking change bumps MAJOR, feature bumps MINOR, fix bumps PATCH; 0.x means no stability promise.
- Changelog and version bump generated from commits (release-please, semantic-release or changesets), tags `vX.Y.Z`.
- Releases built once in CI from a tag, the same artifact promoted through environments.

## Dockerfiles
- Multi-stage: build stage with the toolchain, final stage with only the runtime and the artifact.
- Small, maintained base images pinned by digest (`node:22-slim@sha256:...`, distroless, Alpine when musl is fine,
  or hardened images); rebuild regularly to pick up patches.
- Run as a non-root user (`USER 10001`), read-only root filesystem where possible, no `sudo` in images.
- Order layers from least to most frequently changed; copy lockfiles first and install, then copy sources.
- `.dockerignore` excludes `.git`, `node_modules`, build output, `.env`.
- Secrets at build time with `RUN --mount=type=secret`, never `ARG` or `ENV`. Cache mounts for package managers.
- One process per container, `HEALTHCHECK` or orchestrator probes, exec form for `CMD`/`ENTRYPOINT`, handle SIGTERM.
- Lint with hadolint, scan images with Trivy or Grype in CI, fail on fixable critical vulnerabilities.

## Docker Compose for development
- `compose.yaml` with services for the app dependencies (database, cache, mail catcher), named volumes, healthchecks and
  `depends_on: condition: service_healthy`.
- Values from a committed `.env.example`; the real `.env` is gitignored.
- Profiles for optional services; `docker compose watch` or bind mounts for hot reload.
- Same image versions as production where it matters (database major version).

## Dependency updates
- Dependabot (`.github/dependabot.yml`) or Renovate for every ecosystem in the repo, including `github-actions` and Docker.
- Group minor and patch updates, keep majors separate. Add a cooldown before adopting new releases
  (Dependabot `cooldown`, Renovate `minimumReleaseAge`, for example 3 to 7 days); security updates are not delayed.
- Lockfiles committed, installs in CI with `npm ci` / `pnpm install --frozen-lockfile` (only on a repository already using pnpm) and `--ignore-scripts` when the
  project allows it.
- Dependency review action on PRs to block known vulnerable or disallowed licences.

## Supply chain
- SBOM generated per release (CycloneDX or SPDX, with Syft or the build tool plugin) and attached to the release.
- Build provenance with GitHub artifact attestations (`actions/attest-build-provenance`, needs `id-token: write` and
  `attestations: write`): SLSA Build L2 by default, L3 when the build runs in a reusable workflow. Verify with
  `gh attestation verify`.
- Sign container images (cosign keyless) and verify signatures at deploy time. Use cosign 3.1.3 or later
  (fixes GHSA-fx35-mq7g-6g98, a verification bypass with legacy bundles).
- Run OpenSSF Scorecard on public repos and fix the low scores (pinned deps, token permissions, branch protection).
- Secret scanning and push protection on; CodeQL or an equivalent SAST on PRs.
- Publish packages with trusted publishing (OIDC) instead of long-lived registry tokens.

## Observability basics
- Structured logs (JSON) with level, timestamp, service, request or trace id; no secrets or personal data in logs.
- The four golden signals per service: latency, traffic, errors, saturation. Alert on symptoms users feel (SLO burn rate),
  not on every metric.
- OpenTelemetry SDKs for traces, metrics and logs, exported to whatever backend the project uses.
- Health and readiness endpoints; dashboards and alerts versioned with the code.
- Every deploy is traceable to a commit, and rollback is one command.

## Approval rule
Nothing is pushed, merged, tagged, released or deployed without explicit approval from the user. Changes to branch
protection, secrets or cloud permissions are proposed, not applied.

## Sources
- GitHub Actions secure use reference: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- OIDC in GitHub Actions: https://docs.github.com/en/actions/concepts/security/about-security-hardening-with-openid-connect
- Workflow lockfiles and execution policies: https://docs.github.com/en/actions/how-tos/administer/control-workflow-execution
- Workflow lockfiles public preview (14 Oct 2026): https://github.blog/changelog/2026-10-14-github-actions-workflow-lockfiles-in-public-preview
- cache-mode (10 Sept 2026): https://github.blog/changelog/2026-09-10-control-github-actions-cache-access-with-cache-mode/
- Workflow execution protections GA (17 Sept 2026): https://github.blog/changelog/2026-09-17-workflow-execution-protections-in-github-actions-generally-available/
- Node 20 removed from Actions (23 Sept 2026): https://github.blog/changelog/2026-09-23-node-20-is-no-longer-available-in-github-actions/
- `vulnerability-alerts` token permission: https://github.blog/changelog/2026-09-03-github-actions-early-september-2026-updates/
- Artifact attestations and SLSA L3: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- SLSA v1.2 (current, adds the Source track; in practice here: a ruleset on `main` with required review and required
  checks, see Branching and review): https://slsa.dev/spec/v1.2/
- cosign v3.1.3 release: https://github.com/sigstore/cosign/releases/tag/v3.1.3
- Dependabot options (cooldown): https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference
- Docker build best practices: https://docs.docker.com/build/building/best-practices/
- Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/ and SemVer: https://semver.org/
- OpenSSF Scorecard: https://scorecard.dev/
- Trunk based development: https://trunkbaseddevelopment.com/
- Google SRE book, monitoring: https://sre.google/sre-book/monitoring-distributed-systems/
