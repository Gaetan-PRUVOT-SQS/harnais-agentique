---
name: react-spa
description: 'Use when building or reviewing a React SPA (TypeScript, Vite): React 19 patterns, state, data fetching, accessibility, performance, security and tests. Complements the react skill.'
---

# React SPA

## Stack defaults
- React 19 (19.3.x) with the React Compiler enabled (stable since 1.0, available in the Vite templates). Pin the
  compiler to an exact version if test coverage is thin, and run the e2e suite after each compiler upgrade.
- TypeScript (7.x, native compiler) in `strict` mode plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
  `noImplicitOverride`, `verbatimModuleSyntax`. No `any`; prefer `unknown` and narrow. A remaining `any` is justified in `docs/justifications/`. TypeScript 7 changed defaults
  (`strict` on, `types: []`, `rootDir: "./"`) and turns `baseUrl`, `moduleResolution: node10` and `target: es5` into
  errors: list needed `types` explicitly and set `rootDir` when upgrading.
- Vite for dev and build, `@vitejs/plugin-react`. Environment values through `import.meta.env.VITE_*` only, typed in `vite-env.d.ts`.
- One package manager per repo with its lockfile committed (npm only), Node LTS pinned in `.nvmrc` or `engines`.

## Component design
- Small function components with one job; split when a component mixes data loading, state logic and layout.
- Props typed with a `type Props = {...}`; pass data down, callbacks up. Avoid prop drilling past 2 or 3 levels,
  use composition (`children`, slots) before reaching for context.
- Custom hooks hold reusable logic (`useCart`, `useDebouncedValue`), components stay mostly markup.
- Follow the Rules of React: pure render, no mutation of props or state, hooks at top level. The compiler relies on them.
- `useEffect` is for synchronizing with external systems only. Derive values during render, handle user actions in
  event handlers, use `useEffectEvent` (19.2) for non-reactive logic inside effects.
- Keys are stable ids, never array indexes for lists that change.
- Error boundaries around routes and risky widgets; `Suspense` boundaries with meaningful fallbacks.
- Never define a component inside another component: it gets a new identity on each render, so React remounts it and
  its state is lost. Move it out and pass props.

## State management (pick by kind of state)
| Kind | Tool |
|---|---|
| Server state (anything fetched) | TanStack Query: caching, dedup, retries, invalidation after mutations |
| URL state (filters, page, tab) | router search params, so it is shareable and survives reload |
| Form state | React 19 actions + `useActionState`, or React Hook Form for complex forms |
| Local UI state | `useState` / `useReducer` |
| Shared client state | context for low frequency values (theme, auth user), Zustand when updates are frequent |
- Do not copy server data into a global store. Query keys are arrays built by small factory functions per feature.
- Optimistic updates with `useOptimistic` or the TanStack Query `onMutate` pattern, with rollback on error.

## Routing
- React Router (v7, library or framework mode) or TanStack Router for fully typed routes and search params.
- Lazy load route modules; each route has its own error element and loading state.
- Guard protected routes in loaders or a layout route, and still enforce authorization on the server.

## Forms and validation
- One schema (Zod or Valibot) shared by form validation and API response parsing; infer types from it.
- Validate on submit and on blur, not on every keystroke for long forms; show errors next to fields with `aria-describedby`.
- Disable double submit with the pending state; keep user input on server errors.

## Accessibility (WCAG 2.2 AA)
- Semantic HTML first (`button`, `a`, `label`, `nav`, `main`, headings in order); ARIA only to fill gaps.
- Everything works with the keyboard, focus is visible and not hidden by sticky headers (2.4.11), focus moves to the
  new content after route change and is returned when a dialog closes.
- Target size at least 24x24 CSS px (2.5.8), no drag-only interactions (2.5.7), no re-entering the same data (3.3.7),
  accessible authentication without puzzles (3.3.8).
- Contrast 4.5:1 for text, respect `prefers-reduced-motion`. Use tested primitives (Radix, React Aria) for complex widgets.
- Lint with `eslint-plugin-jsx-a11y`, check with axe in component and e2e tests, and do a short manual screen reader pass on new flows.

## Performance
- Measure first: Core Web Vitals (LCP under 2.5 s, INP under 200 ms, CLS under 0.1) with the `web-vitals` library in
  production and Lighthouse or the Performance panel locally (React Performance Tracks in 19.2).
- Code split by route with `lazy`, and split heavy widgets (charts, editors) behind interaction.
- With the compiler on, do not add `useMemo`, `useCallback` or `memo` by default; use them only as measured escape
  hatches (for example an effect dependency). Keep existing memoization unless tests cover its removal.
- Virtualize long lists (TanStack Virtual), lazy load images with width and height set, preload the LCP image and fonts.
- Watch bundle size in CI (`vite build` report or a size limit check); avoid importing whole libraries.
- Start independent requests together (`Promise.all`, route loaders, prefetching with TanStack Query) instead of
  chaining them through nested components that each fetch after rendering.

## Security
- Never use `dangerouslySetInnerHTML` with untrusted data; if HTML must be rendered, sanitize with DOMPurify.
- Validate URLs before using them in `href` or `src` (block `javascript:`), and use `rel="noopener noreferrer"` on external links.
- Content Security Policy from the server: `default-src 'self'`, no `unsafe-inline` scripts, `frame-ancestors 'none'`,
  plus Trusted Types (`require-trusted-types-for 'script'`) where supported. React 19.3+ accepts Trusted Types values,
  so HTML reaches the DOM only through a policy that wraps DOMPurify output.
- If a project uses React Server Components packages (`react-server-dom-webpack`, `-parcel`, `-turbopack`), they must
  be at a patched version for GHSA-xqc2-xf4c-x3h3 (critical RCE, fixed in 19.3.1, 19.2.9, 19.1.10, 19.0.9). A pure
  client SPA without these packages is not affected.
- Auth: prefer the backend for frontend pattern with `HttpOnly; Secure; SameSite` cookies. If tokens must live in the
  browser, keep the access token in memory, use short lifetimes and refresh rotation, never `localStorage`. OAuth uses PKCE.
- Anything in the bundle is public: no secrets in `VITE_*` variables.
- Run `npm audit` or equivalent in CI and keep dependencies current (see the devops skill).
- Anything read back from `localStorage` or `sessionStorage` is untrusted input: version the keys, store only the
  fields needed, parse with the shared schema and fall back to defaults on failure. Never store tokens or personal
  data there.

## Testing
| Level | Tools |
|---|---|
| Unit and component | Vitest (5.x, needs Node 22.12+) + Testing Library + `@testing-library/user-event`, jsdom or Vitest Browser Mode |
| Network | MSW handlers shared by tests, Storybook and local dev |
| E2E | The runner already in the repo (Playwright or Cypress, `qa-e2e`), against the built app (`vite preview`) |
- Query by role and label (`getByRole('button', { name: /save/i })`), assert what the user sees, not internal state.
- Test hooks through a component or `renderHook`; wrap providers (QueryClient with `retry: false`) in a test util.
- Contract the API with the shared schema so MSW handlers and real responses stay in sync.

## Tooling
- ESLint flat config (`eslint.config.js`) with `typescript-eslint` (type aware), `eslint-plugin-react-hooks`
  (recommended, includes the compiler rules), `jsx-a11y`, and import ordering. Prettier for formatting with
  `eslint-config-prettier` so they do not fight.
- TypeScript 7 has no programmatic API before 7.1, so type-aware linting cannot use it directly. Follow the TypeScript
  7.0 release notes: install the official `@typescript/typescript6` package as an npm alias for the linter and keep
  `tsc` 7 for type checking.
- `tsc --noEmit` in CI, lint and type check on staged files with a pre-commit hook.

## Folder structure (by feature)
```
src/
  app/          # providers, router, global styles, entry
  features/
    orders/     # components/, hooks/, api.ts (queries), schema.ts, routes.tsx, orders.test.tsx
  shared/       # ui primitives, lib (fetch client, formatting), hooks used by several features
  test/         # test utils, msw handlers, setup
```
- Features import from `shared`, never from another feature's internals; expose a small `index.ts` per feature.

## Commits and approval
- Commits are short and simple, with a natural description in French (`Filtre par statut sur les commandes`).
- Nothing is pushed, merged or deployed without explicit approval from the user.

## Sources
- React Compiler 1.0: https://react.dev/blog/2025/10/07/react-compiler-1
- React 19.2: https://react.dev/blog/2025/10/01/react-19-2
- React releases (19.3, security patches): https://github.com/facebook/react/releases
- GHSA-xqc2-xf4c-x3h3: https://github.com/facebook/react/security/advisories/GHSA-xqc2-xf4c-x3h3
- TypeScript 7.0: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- You might not need an effect: https://react.dev/learn/you-might-not-need-an-effect
- TanStack Query: https://tanstack.com/query/latest
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- Web Vitals: https://web.dev/articles/vitals
- OWASP Cheat Sheets (XSS, CSP, session): https://cheatsheetseries.owasp.org/
- Vitest 5: https://vitest.dev/blog/vitest-5
- Testing Library guiding principles: https://testing-library.com/docs/guiding-principles
- ESLint flat config: https://eslint.org/docs/latest/use/configure/configuration-files
