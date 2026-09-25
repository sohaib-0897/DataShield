# Screenshot capture plan

Capture screenshots manually after loading the synthetic demo. Do not create or edit synthetic screenshots to imply live application evidence. Keep the local synthetic labels visible where practical.

| Capture | Demo state and visible information | Keep out of frame |
| --- | --- | --- |
| Overview dashboard | Seeded events and alerts; summary counts, severity distribution, recent alerts, behavior source and system health | Browser password manager, terminal secrets, real user names or hostnames |
| Alerts list | Seeded sensitive file/USB/upload alerts, severity, risk, state and investigation links | Real identifiers or unrelated personal activity |
| Investigation risk breakdown | Alert ID, synthetic user/endpoint, event time/channel, score, contributions, scoring version and source labels | Raw sensitive values, auth tokens, API keys |
| Supporting evidence and timeline | Masked synthetic detection, supporting events and timestamps | Raw sample text, real documents, local file paths that reveal private data |
| Reports | Selected range, database-backed charts/breakdowns, decision counts and risky users | Real organizational data |
| System/model status | Healthy service/database, `HEURISTIC`, no production trained model, feature schema and synthetic endpoint | `.env`, agent key, JWT, DB credentials |
| Architecture diagram | `docs/architecture.md` Mermaid diagram rendered in GitHub or editor | Private repository URLs or workspace absolute paths |
