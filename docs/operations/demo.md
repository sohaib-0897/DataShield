# Synthetic demo

1. Start Docker Compose and run the README seed command.
2. Sign in as `demo.admin` at <http://localhost:3001>.
3. Overview shows stored events and alerts. Open an investigation.
4. Inspect source labels, risk contributors, masked CNIC evidence, endpoint, and audit trail.
5. Add a note and choose `BLOCK` or `ALLOW`; refresh to see the persisted decision.

Seeded identities and resources are explicitly synthetic. Three ordinary history windows make the later count-based behavior source `HEURISTIC`; this is a deterministic demo baseline, not trained ML. The scenario enters through the same service function as the event API and does not insert finished alerts. Repeated seeding uses the same source IDs.
