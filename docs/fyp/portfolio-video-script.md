# Portfolio video: 60-90 seconds

Target 85-90 seconds with about 145 spoken words and short navigation pauses. Record actual synthetic screens at 1440 x 900. Use clean cuts and a slow cursor; keep source labels readable. No fake typing, simulated metrics, or fabricated incoming events. Authentication and configuration stay off camera.

| Time | Picture | On-screen text | Voiceover |
| --- | --- | --- | --- |
| 0-5 s | DataShield title, then Overview | DataShield / DLP and insider-risk prototype | "A file event needs context. DataShield brings that context into one analyst workflow." |
| 5-15 s | Architecture diagram; follow endpoint to API to dashboard | Collect. Explain. Review. | "Python collectors send endpoint telemetry to FastAPI. PostgreSQL persists the investigation records, and React makes them available to analysts." |
| 15-30 s | User activity; move from earlier normal events to the later synthetic sequence | Recorded synthetic scenario | "This recorded scenario follows a synthetic employee from ordinary file activity to a sensitive file, removable-media activity, and an upload attempt." |
| 30-45 s | Investigation source labels and contribution panel | RULE sensitivity / HEURISTIC behavior | "Masked detections show the sensitivity finding. Behavior uses a labeled heuristic. The risk breakdown explains how the activity and history contribute to the alert." |
| 45-60 s | Identity, event, evidence, supporting timeline; use separate readable crops | Evidence in context | "The investigation connects the employee, endpoint, event, and supporting activity. An analyst can review the evidence before recording a response." |
| 60-75 s | Existing BLOCK and review note, then audit entry and Reports | Recorded response / Audit history | "BLOCK can stop a pending upload through a cooperating client. The decision and audit record persist, and reports summarize the stored activity." |
| 75-90 s | System status, then project title and repository URL | FastAPI / PostgreSQL / React / Docker | "This is an academic prototype. No trained behavior model is active, and authentic CERT evaluation remains future work. DataShield makes the analysis and its limits visible." |

Use the existing BLOCK if it is already recorded. Do not imply that a real transfer was blocked by footage of a seeded event. If no live collection is shown, retain the "Recorded synthetic scenario" caption. End card: `github.com/sohaib-0897/DataShield`.

Before publishing, apply the [screenshot privacy and quality review](screenshots.md). Capture and recording remain pending access to the existing demo login; this script is not evidence that a video has been produced.
