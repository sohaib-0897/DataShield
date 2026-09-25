# FYP spoken demo: 3-5 minutes

Aim for about four and a half minutes at a conversational pace, including brief navigation pauses. Bracketed cues are directions, not narration. Rehearse against the actual stored scenario and use displayed values rather than memorized counts. The account for this walkthrough is the existing synthetic demo ADMIN account, which can also open the Audit log.

## 0:00-0:35 - Opening and problem

[Overview, with synthetic data already loaded.]

"This is DataShield, my data loss prevention and insider-risk prototype. It brings Windows endpoint activity and cooperating upload requests into one analyst workflow.

A single file event does not explain whether something needs attention. An analyst also needs to know who performed it, which endpoint was involved, whether sensitive information was detected, and how the activity compares with earlier behavior. DataShield stores that context alongside a risk explanation and the analyst's response."

## 0:35-1:05 - Architecture

[Show the architecture diagram briefly.]

"The endpoint collectors submit a common event format to FastAPI. The service validates the event, checks for duplicate delivery, analyzes sensitivity, builds activity features, and calculates risk. PostgreSQL holds the events and investigation records, and the React dashboard reads them through the API.

Network monitoring records connection metadata. It does not intercept HTTPS content. Upload approval is available to clients that explicitly integrate with DataShield."

## 1:05-1:45 - Recorded synthetic scenario

[User activity, select synthetic.employee.]

"For this walkthrough, I am using an existing synthetic scenario. These are stored events, so I am not claiming that a physical USB device is generating them now.

The earlier file activities provide three normal history windows. Later, the same synthetic employee creates a sensitive file, has removable-media activity, and attempts an upload. Notice the timestamps and channels: they let us follow the sequence without treating every event as an isolated warning.

Now I will open the upload alert and show why it crossed the configured threshold."

## 1:45-2:40 - Sensitivity, behavior, and risk

[Investigation: Analysis sources, contributions, then masked evidence.]

"The sensitivity source here is RULE. A bounded pattern scan found a synthetic CNIC, and the stored evidence contains a masked match. The scanned sample text is not retained as event metadata.

The current behavioral source is HEURISTIC. It compares activity counts with earlier feature windows. This is a deterministic rule, not a trained anomaly model. The source label makes that distinction visible.

The final risk score combines behavior, sensitivity, activity type, channel, and prior risk. These are the contributions stored for this particular assessment. The score is a triage priority, not a percentage chance that someone is malicious.

The investigation connects that explanation to the synthetic user, endpoint, event, and supporting timeline. The nearby timeline shows the surrounding activity; the earlier normal windows were visible in User activity."

## 2:40-3:25 - Analyst response and audit

[Use the existing upload alert. Record BLOCK only if appropriate; otherwise point to its existing BLOCK and review notes.]

"After reviewing the evidence, an analyst can record a decision and a note. Here I am showing the BLOCK response and its persisted status.

For a cooperating upload client that is waiting for approval, the client polls this decision and must stop the transfer. This seeded event demonstrates the review record and decision contract; it does not by itself prove that a real upload was prevented. A completed file copy cannot be reversed by this action.

The decision also appears in the audit history. I am using the synthetic admin account to show the full Audit log; the server enforces the role permissions."

## 3:25-4:00 - Reports and system status

[Reports with the original demo date included, then System status.]

"Reports summarize stored activity, alert distribution, and analyst decisions for the selected range. They use the same PostgreSQL records, rather than sample dashboard numbers.

System status separates database health from model availability. Here the behavior source is HEURISTIC and a production trained model is not available. A stale synthetic endpoint is not evidence of a running physical agent."

## 4:00-4:30 - ML status and conclusion

"The repository includes preparation, candidate training, and model-registry infrastructure. Authentic CERT evaluation is still future work. Activating a behavior artifact requires the documented provenance and reviewed evaluation checks; I am not claiming model accuracy today.

The implemented result is a traceable path from endpoint telemetry to an explainable assessment, a reviewable alert, and a persisted analyst response. The next work is evaluating genuine data and hardening deployment, while keeping those evidence and source boundaries clear."
