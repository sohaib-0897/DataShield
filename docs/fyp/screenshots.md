# Final screenshot plan

## Capture status

Application captures are pending the existing demo login. During the presentation pass, `DATASHIELD_DEMO_ADMIN_PASSWORD` was unavailable, so no authenticated screenshots were captured. Do not reseed, change a password, fabricate UI values, or substitute debug captures to fill this gap.

Use the existing synthetic scenario: `synthetic.employee`, `synthetic-workstation`, machine `SYNTHETIC-ENDPOINT-001`, and `synthetic-sensitive.txt`. Confirm every visible row belongs to synthetic activity before sharing. The seven seeded events are recorded history, not a new live hardware demonstration.

## Consistent framing

Use a 1440 x 900 desktop viewport at 100% browser zoom. Capture browser content without tabs, address bar, desktop, developer tools, or terminal. Keep 16-24 px around panel boundaries. Prefer scrolling and a focused crop over shrinking text. Use 90% only where noted and only if headings remain readable; never change displayed data to improve a frame.

Retain complete labels, counts, dates, units, and source states. A vertical scroll between captures is expected. Avoid full-page images with excessive empty space. Preview each export at its intended README or slide size.

| Shot / intended filename | Visible content and selected scenario | Keep out of frame | Crop, zoom, sidebar |
| --- | --- | --- | --- |
| 1. Overview / `overview.png` | Security overview, persisted counts, severity and recent synthetic alerts. Use the existing scenario; do not claim a zero-alert starting state. | Other users/endpoints, stale loading or error panels, password-manager prompts. | Top of dashboard with complete metric cards and the first complete row of panels; 100%; sidebar visible. |
| 2. Alerts / `alerts.png` | Filter to `synthetic.employee`; show existing USB transfer and upload alerts, risk, severity, status, and Investigate links. | Unrelated smoke/benchmark rows, personal resources, clipped table columns. | Heading, active filters, and a small number of complete rows; 100% (90% only if needed); sidebar visible. |
| 3. Investigation / `investigation.png` | Select the synthetic `UPLOAD_ATTEMPT` for `synthetic-sensitive.txt`; include identity, event, risk, and analysis source cards. Keep the same alert for shots 4-6. | Any non-synthetic hostname/path; raw payloads; partial cards. | Top investigation panels and source labels; 100%; sidebar visible if cards fit, otherwise crop the content area. |
| 4. Risk breakdown / `risk-breakdown.png` | Same upload alert: contributions, total score, policy threshold, `weighted-v1`, and `HEURISTIC` reason. | A crop that hides the source label or presents risk as a probability. | Focused risk/source panel crop with complete headings; 100%; sidebar unnecessary. |
| 5. Masked evidence / `masked-evidence.png` | Same upload alert: DETECTIONS block, CNIC type, count, masked value, and RULE source. Show stored evidence, not input sample text. | Any unmasked CNIC/email, large unrelated JSON blocks, sensitive clipboard or notes. | Scroll to the relevant evidence block; keep its title/context; 100%; sidebar unnecessary. |
| 6. Supporting activity / `supporting-activity.png` | Same alert: supporting FILE, USB, UPLOAD events and timestamps. Earlier normal windows are shown separately in User activity. | Claims that the surrounding-hour timeline contains all earlier normal windows; unrelated rows. | Complete Supporting event timeline panel with event names/times; 100%; sidebar unnecessary. |
| 7. Reports / `reports.png` | Select a range that includes the original demo date; show Alerts over time, Event volume, and Analyst decisions. Verify every aggregate is from synthetic data. | Mixed personal data, misleading zero counts from an excluded date range, clipped chart labels. | Heading, range selector, and complete chart panels; 100% or 90%; sidebar visible. |
| 8. System / `system-status.png` | Database health, `HEURISTIC`, production trained model Not available, sensitivity source/version, feature schema, and synthetic endpoint only. | Keys, tokens, configuration dumps, a staged ONLINE claim when the endpoint is stale/offline. | Heading plus complete health/model cards; 100%; sidebar visible. |
| 9. Architecture / `architecture.png` | Render the Mermaid diagram in [Architecture](../architecture/architecture.md), including decision polling and cooperating-client enforcement. | Editor file paths, unrelated tabs, clipped arrows, or a claim that RESOLVE blocks uploads. | Diagram only with a small border; fit at readable size, export at 2x if available; no sidebar. |

## Acceptance and publication

Before accepting any image, confirm: no clipped cards, horizontal scrollbar, loading spinner, error panel, awkward blank area, or duplicate demo noise. Check labels at normal reading size. Reject a shot if the underlying screen cannot be framed honestly; do not paint over values or simulate application evidence.

Review for passwords, JWTs, API keys, `.env`, database credentials, terminal output, raw identifiers, personal Windows paths, and browser notifications. Synthetic labels and masked matches must be obvious. Reports aggregate across users: if any real data is included, do not publish that frame.

Keep provisional captures and Playwright output outside tracked documentation. Put only reviewed publication images in `docs/assets/screenshots/`, creating it when images are ready. Do not add empty image files or broken Markdown placeholders. Use one Overview image in README, optionally Investigation and Reports; link the remaining gallery from this document. Caption each with the synthetic scenario and capture date. Record the commit and whether it is stored history or live collection in the caption notes.

The remaining manual work is to sign in with the existing credential, capture/review these shots, and record the [portfolio video](portfolio-video-script.md). Hardware footage requires the separate [USB procedure](../operations/usb-testing.md).
