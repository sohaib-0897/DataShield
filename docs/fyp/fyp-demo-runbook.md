# FYP demonstration runbook

Use this alongside the [spoken script](demo-script.md), [technical facts](technical-facts.md), [defense questions](defense-questions.md), and [screenshot plan](screenshots.md). Target 3-5 minutes. The scenario is synthetic and already persisted; describe it as a recorded walkthrough unless agents are actually collecting new activity during the presentation.

## Before presenting

1. Reuse the validated stack, its Compose project, and its existing volume override. Check services with the same Compose arguments used to start them. Do not substitute the default volume configuration for an existing installation.
2. Verify `http://localhost:8001/ready` reports `ready` and `http://localhost:3001` returns HTTP 200. Keep terminals and configuration files off the recording.
3. Sign in as the existing `demo.admin` with its existing password. This ADMIN account can demonstrate analyst decisions and the admin-only Audit log. Do not display credentials or browser storage.
4. Select `synthetic.employee` / `synthetic-workstation`. Confirm the original scenario date and use a report range that includes it. Counts may include earlier synthetic smoke checks; do not promise fixed dashboard totals.
5. Identify the existing `UPLOAD_ATTEMPT` for `synthetic-sensitive.txt`, verify its source labels, and note whether a BLOCK decision already exists. Do not manufacture a new pending state for the recording.
6. Use 1440 x 900 at 100% zoom. Close notifications, developer tools, and password-manager overlays. Rehearse navigation before recording.

The current demo password was unavailable during the presentation documentation pass. **E2E NOT RERUN - existing demo password required.** No reseed or account change is needed to resolve that limitation. Playwright requires `DATASHIELD_DEMO_ADMIN_PASSWORD` in the shell and `DATASHIELD_FRONTEND_URL=http://localhost:3001`; it records a synthetic BLOCK action.

For a new disposable installation only, see [first-time demo setup](../operations/demo.md). Existing accounts and databases should use their preserved credentials and data.

## Scenario landmarks

The seed uses seven stable source IDs, `synthetic-demo-v2-0` through `synthetic-demo-v2-6`, and calls the same ingestion service function used by the API. It does not simulate transport from a physical device.

| Recorded phase | What to point out |
| --- | --- |
| Three earlier normal events | `synthetic-normal-1.txt`, `synthetic-normal-2.txt`, and `synthetic-normal-3.txt`, originally six, four, and two hours before seeding. |
| Sensitive file | `FILE_CREATE` for `synthetic-sensitive.txt`; the input was synthetic and the stored detection is masked. A sensitivity finding need not create an alert by itself. |
| Removable media | Synthetic `USB_INSERT`, then `USB_FILE_TRANSFER`; this proves pipeline handling, not a physical device test. |
| Upload attempt | `UPLOAD_ATTEMPT` for the same resource; select this alert for risk, evidence, and the decision demonstration. |

## Fourteen-step narrative

| Step | Screen / action | Explain |
| --- | --- | --- |
| 1 | Overview in its normal operating state | These are stored PostgreSQL counts. Existing alerts are expected; this is not an empty database or a staged zero-alert baseline. |
| 2 | Briefly show the architecture diagram | Agents submit a common event contract; FastAPI validates, normalizes, analyzes, and persists it. |
| 3 | User activity, select `synthetic.employee` | Identify the three earlier normal events and their original timestamps. These provide earlier feature windows. |
| 4 | Follow the later activity in the same timeline | Introduce the sensitive file, synthetic USB insertion/transfer, and upload attempt as recorded events. |
| 5 | Open the upload investigation, Analysis sources | Sensitivity is RULE for this scenario; show the masked CNIC detection, not its raw input. |
| 6 | Behavior source and explanation | Say: "Current behavioral source is HEURISTIC." Compare recent counts with earlier windows; do not call this a trained anomaly model. |
| 7 | Risk factor contributions and Risk assessment | Explain the displayed component contributions, total score, and stored policy threshold. Risk is not a probability of theft. |
| 8 | Alerts, filter User to `synthetic.employee` | Show the generated USB/upload alert rows, severity, risk, and actual current status. |
| 9 | Return to the selected upload investigation | Connect the identity, event, source labels, risk breakdown, masked evidence, and supporting event timeline. The supporting timeline covers one hour before/after the event; earlier normal history is in User activity. |
| 10 | Analyst response | If a new response is appropriate, enter a synthetic review note, choose BLOCK, and confirm. If already blocked, show the existing decision. A recorded BLOCK is enforced only when an integrated upload caller polls and honors it; this seeded scenario alone does not stop a real transfer. |
| 11 | Decision and audit history, then Audit log | Show the recorded `ALERT_DECISION`, time, and notes. Wait for the normal refresh or reload if needed. |
| 12 | Reports | Choose a range including the seed date; connect alert distribution, event volume, and analyst decisions to the stored scenario. |
| 13 | System status | Show database health, HEURISTIC, no available production trained model, rule version, and feature schema. A synthetic endpoint may be stale; do not imply an agent is live. |
| 14 | Architecture / closing slide | Future work is licensed CERT preparation, held-out evaluation, reviewed artifact activation, and production hardening. Those results are not part of this demo. |

## Recovery without changing the scenario

- **Password unavailable:** pause authenticated capture and obtain the existing demo credential privately. Do not reseed or reset it for presentation polish.
- **No data in a report:** inspect the selected date range and the original event dates; do not generate replacement rows to make a chart look populated.
- **Mixed data:** use synthetic filters where available. Reports aggregate across users, so do not capture them if personal data is included.
- **Service unavailable:** inspect service status using the existing Compose configuration. Resolve startup separately before presenting; a screenshot of an earlier run is not evidence of current health.
- **Source differs from expectation:** present the visible label honestly. `INSUFFICIENT_HISTORY` or `UNAVAILABLE` is not MODEL or HEURISTIC. Investigate outside the presentation before making a different claim.
- **Already blocked:** explain the persisted review. Do not delete a decision or change workflow state merely to stage a first-time action.

Never use a demo reset, volume deletion, password replacement, or model training as a presentation recovery step. Physical USB footage requires the separate [manual procedure](../operations/usb-testing.md) and recorded hardware results.
