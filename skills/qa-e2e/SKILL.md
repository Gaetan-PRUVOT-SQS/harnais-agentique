---
name: qa-e2e
description: Use when designing or stabilising automated E2E, API, visual or accessibility tests with Cypress or Playwright, or a test automation architecture. Complements iso-29119.
...
---

# QA automation with Cypress and Playwright

The per-feature loop is `tests-regression-auto` and `iso-29119` (`feature-test-pipeline` for test quality). This skill covers how automated tests
are built so they stay fast, stable and maintainable.

## Automation architecture (ISTQB CTAL-TAE v2.0, gTAA)
- Keep the four gTAA capabilities separate:
  - test generation (optional, model based),
  - test definition (specs, data, keywords),
  - test execution (runner, logs, reports),
  - test adaptation (adapters to the system under test: UI, API, DB, queues).
- Layer the framework, and keep layers few:
  1. test scripts (readable scenarios, no selectors or raw HTTP),
  2. business logic library (app actions, page or component objects, API clients for this product),
  3. core library (generic helpers, data builders, reporting, reusable across products).
- Pick the scripting approach on purpose: structured scripting by default, data driven for many input variations,
  keyword driven (ISO 29119-5) when non-developers write scenarios, BDD only when the business actually reads them.
- Automation code follows the same rules as product code: review, lint, type check, versioned with the app.
- Track automation health: pass rate, flake rate, duration, defects found, and maintenance effort per change.

## Pyramid or trophy
- Pyramid for most products: many unit tests, a solid layer of integration and API tests, few E2E journeys.
- Trophy (more integration and component tests, static analysis at the base) fits frontend-heavy SPAs where most bugs sit
  in component wiring. Both agree on one point: E2E covers critical user journeys, not every branch.
- Push a check down a level whenever it does not need a real browser. Each E2E test must justify its runtime.

## Selectors
- Cypress: dedicated `data-cy` (or `data-testid`) attributes, or `cy.getByRole(role, { name })` (built in since 16.2.0,
  no plugin needed) when the accessible name is part of what you test. Use `cy.contains` only when a text change should
  fail the test.
- Playwright: user-facing locators first (`getByRole`, `getByLabel`, `getByPlaceholder`, `getByText`), then `getByTestId`.
  Use `locator.visible()` (1.63+) instead of the `:visible` CSS pseudo-class.
- Never CSS classes, generated ids, XPath on layout, or nth-child chains.
- If something cannot be selected accessibly, treat it as a possible accessibility bug before adding a test id.

## Waiting and assertions
- No fixed waits (`cy.wait(2000)`, `page.waitForTimeout`). Wait on state:
  - Cypress: retried assertions (`should`), aliased intercepts (`cy.wait('@saveOrder')`);
  - Playwright: web-first assertions (`await expect(locator).toBeVisible()`), `waitForResponse` when a request matters.
- Assert outcomes the user sees, plus the request payload when the contract matters.
- Avoid conditional testing ("if the banner shows, close it"); make the state deterministic instead.
- Playwright: never wait for `networkidle`; wait for the element, the response or the URL that proves the next state.
- Cypress: never mix `async`/`await` or hand-made Promises with `cy` chains; stay in the chain, or return the Promise
  explicitly when one is unavoidable.
- Cypress: define aliases in `beforeEach`, not `before`. Aliases are cleared between tests, so a `before` alias is gone
  from the second test on.
- When asserting a text, locate the element by role, label or test id, not by that same text, otherwise the
  assertion cannot fail. Playwright `toMatchAriaSnapshot` with a partial snapshot (regex for changing values) checks
  structure and accessible names in one readable assertion.
- In review, check that each test title and comment still matches what the test does; a wrong title hides a gap.

## Network control
- Stub third parties and slow or flaky dependencies (`cy.intercept`, `page.route`); keep a few journeys against the
  real backend as a contract smoke test.
- Fixtures live next to the specs and are derived from the real API schema so stubs do not drift.
- Test error paths by stubbing 4xx, 5xx, timeouts and empty responses.

## Test isolation and state
- Every test runs alone and in any order. Cypress `testIsolation` stays on; Playwright gives each test a fresh context.
  Check it regularly with `npx playwright test --shuffle` (1.64+) and keep the printed seed to reproduce a failure.
- Tests that must not run at the same time because they touch a shared resource declare a Playwright test `lock`
  (1.63+) instead of forcing the whole file to run serially.
- Set up state through the API or database seeding, not through the UI of earlier tests.
- Authentication:
  - Cypress: `cy.session()` with a `validate` callback, logging in through the API. Credentials and tokens are read
    with `cy.env()`, which keeps them in the Node process; `Cypress.expose()` is only for non-sensitive values because
    they are readable in the browser. `Cypress.env()` was removed in Cypress 16;
  - Playwright: a setup project that saves `storageState`, reused by dependent projects. Keep `.auth/` gitignored.
- One UI login test covers the login form itself; every other test starts authenticated.
- Reset the state a test needs before it runs (API or seed call in `beforeEach`), and give each run unique data (run id
  in names, emails). Do not rely on `after` hooks for cleanup: they do not run when the test or the runner stops early.

## Structuring test code
- Cypress: app actions (custom commands that call the app or the API directly) for setup, small page helpers for
  repeated UI steps. Avoid deep page object hierarchies.
- Playwright: fixtures (`test.extend`) to inject page objects, API clients and seeded data; page objects stay thin
  (locators plus user-level methods, no assertions hidden inside unless named as checks).
- Tag tests (`@smoke`, `@regression`, `@a11y`) and run subsets by tag (`--grep` in Playwright, `@cypress/grep`).

## Test data management
- Builders or factories with sensible defaults (`buildUser({ role: 'admin' })`), never shared mutable fixtures.
- Synthetic data only; no production personal data in test environments (GDPR). Mask anything copied from prod.
- Seed scripts are versioned and idempotent; environments can be reset to a known baseline on demand.
- Dates, time zones and locales are fixed in tests (`cy.clock`, Playwright `clock` and `timezoneId`).

## Parallelization and CI
- Playwright: `fullyParallel: true`, workers per CPU, `--shard=i/n` across CI machines, merge blob reports.
- Cypress: split specs across machines (Cypress Cloud or a spec splitting script); keep specs balanced in duration.
- Run against a production-like build, on Linux in CI, with browsers installed by the official command or image.
- Cypress 16: pass `--browser chrome` (or `firefox`) in CI, the default Electron browser is deprecated and will be removed.
  Cypress 16 needs Node.js 22, 24 or 26+; Node 20 is no longer supported. `cy.exec()` was removed, use `cy.task()`.
- Keep traces, videos and screenshots only on failure (`trace: 'on-first-retry'`, Cypress screenshots on failure).
- Fail the build on `test.only` / `it.only` (Playwright `forbidOnly: !!process.env.CI`, an ESLint rule for Cypress).

## Retries and flake management
- The verdict uses retries 0 (`retries: 0`; Cypress `retries: { runMode: 0, openMode: 0 }`). A bounded
  rerun only reproduces a flake. It is logged as an incident, and it never turns the suite green.
- A test that passes only on retry is an incident (`iso-29119`), not a green run. It is fixed at the root before the change is done. Quarantine is never a way to get green; an exception needs a written
  decision from the user and is reported as a deviation.
- Hunting an intermittent failure: rerun the single test in a bounded loop that stops at the first failure, and keep
  the artefacts of that first failure before anything overwrites them. Read the failed attempt itself, not the last
  retry, which may have passed. Twenty green runs do not prove the test is stable. Re-read every new failure instead
  of assuming it is the same one; a failure that moves from step to step points at load or environment, not at a
  timeout to raise.
- Typical root causes: missing wait on a request, shared data, animation, time, test order, environment instability.
- Watch the flake rate per test over time (Playwright report history, Cypress Cloud flaky detection).

## Repairing a broken test
Before editing a failing test, decide which case it is, and write it in the defect report:
- Technical drift (locator, wrapper element, timing, data leaking between runs) and the user-visible behaviour is
  unchanged: fix the test, rerun it alone, then the full suite.
- The product behaviour changed on purpose (ticket, decision, release note): update the test and the spec scenario
  together, keeping the scenario id.
- Not sure whether the product is wrong or the spec is out of date: stop. Report the scenario, the expected result
  and what the app now does. Never change an expected value just to match what the app does today.
A test is never skipped, marked `fixme` or deleted to get past this point.

## Visual testing
- Playwright `toHaveScreenshot()` or a visual service; Cypress through a visual plugin or service.
- Stable rendering: fixed viewport, fonts installed in the CI image, animations disabled, dynamic areas masked.
- Baselines generated in the same OS image as CI and reviewed like code. Since Playwright 1.64,
  `--update-snapshots=missing` passes the run, so a blocking CI job must not use it: new baselines go through review.

## Accessibility checks
- axe-core on key pages and states: `@axe-core/playwright` (`AxeBuilder`) or `cypress-axe` (`cy.checkA11y`),
  with WCAG 2.2 A and AA tags. Fail on new serious and critical violations.
- Automated checks find part of the issues; add keyboard navigation tests for main flows and a manual pass on new UI.

## API testing
- Playwright `request` fixture or `cy.request` for API tests and for fast setup.
- Check status, schema (Zod, JSON Schema or OpenAPI validation), key fields, auth failures and error formats.
- Keep API tests in their own project or folder so they run first and fast.

## Reporting
- JUnit XML for CI, HTML report (Playwright HTML, Mochawesome) as an artifact, a short summary in the job output.
- Every failure links to its trace, video or screenshot and the commit under test.

## Commits and approval
- Commits are short and simple, with a natural description in French (`Cas de la carte expirée au paiement`).
- Nothing is pushed or merged without explicit approval from the user. Quarantining or deleting a test is proposed, not done silently.

## Sources
- ISTQB CTAL-TAE v2.0 syllabus: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTAL-TAE_Syllabus_v2.0.pdf
- Cypress best practices: https://docs.cypress.io/app/core-concepts/best-practices
- Cypress test isolation and cy.session: https://docs.cypress.io/app/core-concepts/test-isolation, https://docs.cypress.io/api/commands/session
- Cypress test retries: https://docs.cypress.io/app/guides/test-retries
- Cypress changelog (16.0.0 breaking changes, 16.2.0 `cy.getByRole`): https://docs.cypress.io/app/references/changelog
- Cypress 16 migration guide: https://docs.cypress.io/app/references/migration-guide
- Playwright best practices: https://playwright.dev/docs/best-practices
- Playwright release notes (1.63 test locks and `locator.visible()`, 1.64 `--shuffle`): https://playwright.dev/docs/release-notes
- Playwright authentication: https://playwright.dev/docs/auth
- Playwright sharding and retries: https://playwright.dev/docs/test-sharding, https://playwright.dev/docs/test-retries
- Playwright accessibility testing: https://playwright.dev/docs/accessibility-testing
- Playwright visual comparisons: https://playwright.dev/docs/test-snapshots
- Testing trophy: https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
