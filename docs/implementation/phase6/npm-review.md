# Fresh npm findings and Docker review

The 2026-10-08 registry audit succeeded as a JSON response. Exit 1 represents
findings, not a network failure. Full tree: 106 package groups (3 low, 36 moderate,
65 high, 2 critical). Production-declared: 2 moderate groups. This independently
confirms the Phase 0 cached totals; it does not supersede their historical evidence.
`npm-review.json` records fresh counts, selected findings and the unchanged lock hash.

`frontend/Dockerfile` still runs `npm start`, executing CRA development-server
packages at runtime. Loopback Compose binding restricts access but is not proof
that dependency defects are harmless. Build tooling also executes during CI and
installation. Compiled browser output has a different execution surface. Default
Docker behavior was preserved; no container security or reachability claim is made.
The Docker binary is unavailable here, so a native container build/runtime check
remains unverified.

The current critical advisories have narrow compatible patched versions:
[proxy-addr 2.0.8](https://github.com/advisories/GHSA-jqcg-44mw-7w3h) addresses a
proxy trust-subnet interpretation defect, and
[shell-quote 1.11.0](https://github.com/advisories/GHSA-pqg4-j6r4-53mv) addresses a
command quoting defect. `npm explain` confirms both arrive through the development
server/editor graph. These findings remain open; patched versions must be checked
against the graph and covered by build/test/server regression checks before a
scoped lock update. No untrusted-input exploit was executed.

The production React Router navigation finding affects the current 6.30.6 graph:
[maintainer advisory](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6).
The audit proposes react-router-dom 7.18.4, a major upgrade. The app uses
BrowserRouter with client rendering, so SSR exposure is not established, but that
observation cannot dismiss a navigation issue. Review actual navigation targets
and patched compatible releases before selecting a router upgrade. No navigation
or authentication semantics were changed.

`npm audit fix --force` also proposes react-scripts 0.0.0 and a major Tailwind
upgrade. These are not safe drop-in repairs for this established CRA app. The
appropriate separate remediation is a reviewed patch of compatible transitive
packages, a tested router decision and an optional static production container
that serves SPA routes with the same API configuration and port. Dev/toolchain
findings still apply at build time. No forced upgrade/toolchain migration was
performed, and all 106 findings remain open. Exact commands used:

```bash
npm audit --json --prefix frontend
npm audit --omit=dev --json --prefix frontend
npm explain proxy-addr --json --prefix frontend
npm explain shell-quote --json --prefix frontend
npm explain react-router --json --prefix frontend
```

Raw registry responses/explanation graphs are ignored in `.local/phase6-*.json`.
These are dependency findings, not demonstrated application exploits.
