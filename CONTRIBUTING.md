# Development

Follow the root README to install Python and frontend dependencies. Keep backend changes in `backend/`, UI changes in `frontend/src/`, and isolated API tests in `tests/`.

Before opening a pull request, run `python -m pytest -q` from the repository root and `npm run build` from `frontend/`. Explain the user-visible change and include the validation result. Use synthetic events and never commit personal uploads, environment files, logs, or API credentials.

Manual scripts in `tests/manual/` require a running API and, for filesystem checks, a running desktop agent. Review their target folders before running them. They are not part of the isolated test suite.
