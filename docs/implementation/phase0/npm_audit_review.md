# npm audit scope review — 2026-10-08

The user's successful `npm ci` reported **106 vulnerable package groups: 3 low,
36 moderate, 65 high, 2 critical**. The advisory and metavulnerability entries cached
by that install were read without modifying the cache. Matching their affected-version
lists against the unchanged `frontend/package-lock.json` reproduces those exact totals.
`npm_audit_review.json` records all affected package names/versions/scopes, selected
advisory details, and input hashes. These counts include indirect dependency findings;
they are not 106 distinct exploitable defects in application code.

Fresh `npm audit --json` failed because registry.npmjs.org could not be resolved.
This review is based on the install's cached evidence, not a newly fetched audit.
No `npm audit fix`, forced upgrade, package edit, lockfile edit, or toolchain migration
was performed. The earlier September audit in `docs/security/security.md` remains
historical evidence and does not describe the current full dependency tree.

| Scope from package lock | Low | Moderate | High | Critical | Total |
|---|---:|---:|---:|---:|---:|
| Production-declared dependencies | 0 | 2 | 0 | 0 | 2 |
| Exclusively marked dev dependencies | 3 | 34 | 65 | 2 | 104 |
| Full tree | 3 | 36 | 65 | 2 | 106 |

The production-declared findings are `react-router@6.30.6` and its dependent
`react-router-dom@6.30.6`. Cached advisories describe
[SSR hydration constructor injection](https://github.com/advisories/GHSA-337j-9hxr-rhxg)
and [navigation open redirect](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6).
Code inspection finds `BrowserRouter` and client rendering, without an SSR hydration
entry point. That observation does not establish absence of exposure to the separate
navigation issue; no exploit or comprehensive reachability test was performed.

The two critical package findings are:

- `proxy-addr@2.0.7`, reached through Express in the development-server tooling:
  [trusted-subnet IP spoofing advisory](https://github.com/advisories/GHSA-jqcg-44mw-7w3h).
- `shell-quote@1.10.0`, reached through `launch-editor` and `react-dev-utils`:
  [command-quoting injection advisory](https://github.com/advisories/GHSA-pqg4-j6r4-53mv).

The current `frontend/Dockerfile` launches **`npm start`**, which runs the CRA development
server. Therefore "dev dependency" does not mean "never executes in the current Compose
runtime." Build/test tools also execute during installation, tests, and compilation.
The compiled static JavaScript artifact does not itself deploy the Node development
server. Treat installation scope, browser-bundle scope, and deployed-process scope
separately; this review does not claim those critical findings are harmless or exploitable.

The findings predate this implementation phase and remain unresolved. Their remediation
needs a scoped compatibility review and regression checks; forced dependency upgrades
would conflict with the user's preservation requirement. This phase records the
baseline and risk scope, without changing the established application or deployment.

Local evidence and review commands (run from repository root):

```bash
npm explain proxy-addr --json --prefix frontend
npm explain shell-quote --json --prefix frontend
npm audit --json --prefix frontend
npm audit --omit=dev --json --prefix frontend
git diff --exit-code -- frontend/package.json frontend/package-lock.json
```

`npm audit` commands require registry access and return nonzero for findings or registry
failure. They must not be described as successful live audits in this restricted session.
Detailed cached matching data remains in ignored `.local/npm-cached-vulnerability-review.json`;
the summarized committed report is sufficient to identify every matched package group.
