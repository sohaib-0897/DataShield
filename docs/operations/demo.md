# Synthetic demo setup

For an existing validated installation, use its preserved account, events, Compose project, and any volume override. Start with the [FYP runbook](../fyp/fyp-demo-runbook.md). Do not reseed simply to refresh a screenshot or recover a forgotten password during presentation preparation.

## First-time setup on a new disposable installation

Follow the root [Quick start](../../README.md#quick-start). Before seeding, securely populate `DATASHIELD_DEMO_ADMIN_PASSWORD` in the current process with a unique value of at least 12 characters. Avoid putting a literal password in shell history, recordings, or documentation.

```powershell
if (-not $env:DATASHIELD_DEMO_ADMIN_PASSWORD) { throw 'Set the demo password privately before first-time seeding.' }
docker compose exec -T -e "DATASHIELD_DEMO_ADMIN_PASSWORD=$env:DATASHIELD_DEMO_ADMIN_PASSWORD" backend python scripts/demo/seed_demo.py
```

The seed creates or updates `demo.admin` and sets its password on every run. Event IDs are stable, so repeated event delivery is idempotent; the account/password and seed audit action are not a read-only operation. After creating a new demo, sign in at <http://localhost:3001> using that supplied credential.

## What the scenario proves

Seven events for `synthetic.employee` enter through the same service function as the event API, rather than inserting finished alerts. Three ordinary history windows make the later count-based source `HEURISTIC`. Later sensitive file, USB, and upload activity supplies masked evidence and threshold alerts. This is a deterministic synthetic demonstration, not trained ML or proof of physical USB behavior.

Open the existing upload investigation, inspect the sources and contributions, and show the decision/audit workflow. A pending integrated upload caller must poll and honor ALLOW/BLOCK for enforcement. The seed alone does not execute or stop a transfer.

The destructive `scripts/demo/reset_demo.ps1` helper is only for deliberately disposable environments. It is not part of the presentation runbook and must not be used against a preserved PostgreSQL volume.
