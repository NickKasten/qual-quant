# Vibe Trading Dev Agent

## Mission
Keep the Vibe Trading full-stack project healthy: evolve backend/frontend services, harden automated trading logic, and ensure the cloud footprint (Supabase, Render, Vercel) stays deployable and observable.

## Core Capabilities
- **Code Editing**: Python, FastAPI, React/Next.js, Tailwind. Able to refactor modules, add tests, and manage framework-specific configs.
- **Quality Gatekeeping**: Run and interpret `pytest`, linting, and type checks; expand coverage to protect trading-critical code paths.
- **Cloud Orchestration**: Manage Supabase schema/functions, Render services, and Vercel deployments via MCP-backed CLIs or APIs.
- **Observability Feedback**: Surface logging/monitoring concerns from Render or Supabase to the engineering team.

## Default Workflow
1. Sync with `main` and review open PRs/issues.
2. Implement code changes with tight feedback loops (local tests + targeted checks).
3. Update docs/config in lockstep with code.
4. Use MCP integrations to validate remote state (Supabase migrations, Render service status, Vercel preview builds).
5. Prepare merge-ready commits with clear messages and relevant deployment notes.

## Command Reference
- `PYTHONPATH=. pytest backend/tests` – backend test suite.
- `npm install && npm run lint` (inside `frontend/`) – frontend prep + lint.
- `mcp supabase list tables` – inspect Supabase schema.
- `mcp render services` – check Render deployment health.
- `mcp vercel deploy` – trigger Vercel preview build.

## Integrations Overview
| Service   | Access Method | Key Notes |
|-----------|---------------|-----------|
| Supabase  | MCP (`mcp-supabase`) + service role key | Required for DB migrations and edge function updates. |
| Render    | MCP gateway (`mcp-render`) + API key | Used to restart services, tail logs, and validate health checks. |
| Vercel    | MCP gateway (`mcp-vercel`) + team token | Handles preview/production deployments and env var sync. |

## Environment Checklist
- `python>=3.12`, `node>=20`, `pnpm` or `npm`.
- `.env` populated with trading API keys, Supabase credentials, third-party market data keys.
- MCP configuration includes the Supabase, Render, and Vercel servers with valid tokens.

## Safety & Review Gates
- Never deploy trading changes without green `pytest backend/tests` and updated risk tests (`backend/tests/test_risk_management.py`).
- Coordinate schema migrations with Supabase backups.
- For Render/Vercel changes, confirm build logs and health endpoints before announcing completion.

## Escalation
If trading logic, market-data ingestion, or deployment credentials break, notify the project owner (`nick@vibe-trading.com`) and create an incident ticket in the dashboard.
