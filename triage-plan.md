# Gap Analysis: Codebase vs PRD.md

## 1. Backend (Python, FastAPI, Supabase/Postgres)

### What Exists
- API Endpoints: `performance.py`, `portfolio.py`, `signals.py`, `status.py`, `trades.py` in `backend/app/api/endpoints/` — covers portfolio, trades, signals, performance, and status.
- DB Layer: `db/` folder with `schema.sql`, `operations.py`, `models.py`, `supabase.py`, `init_db.py`, `client.py`, `config.py` — covers schema, DB ops, and Supabase integration.
- Broker Integration: `services/broker/paper.py` — likely for paper trading (Alpaca).
- Core Logic: `core/config.py`, `utils/helpers.py` — config and helpers.
- Bot Logic: `bot/` contains `strategy/signals.py`, `risk/risk.py`, `backtest/backtest.py`, and corresponding tests.

### What's Missing or Incomplete
- No clear market data fetcher: PRD requires fetching OHLCV from Tiingo/AlphaVantage/yfinance. There is a `services/fetcher.py` file, but its contents are unknown. If it's not implemented, this is a gap.
- No explicit cron/loop for 5-min bot run: PRD requires the bot to run every 5 min (cron/container). No clear evidence of a scheduler or cron integration.
- No clear risk model enforcement: While `risk.py` exists, it's unclear if 2% equity per trade, 5% stop-loss, and max 3 open positions are enforced.
- No explicit API field for `data_delay_minutes`: PRD requires this in the API.
- No clear retry/backoff logic for API errors: PRD requires reliability features.
- No clear separation for "Edge" API (Vercel Edge Functions): PRD mentions Edge API, but FastAPI is not edge-native.
- No clear legal disclaimer in API responses: PRD requires disclaimers everywhere.

---

## 2. Bot (Strategy, Backtest, Risk, Executor)

### What Exists
- Strategy: `signals.py` (SMA/RSI logic likely here).
- Backtest: `backtest.py` and test.
- Risk: `risk.py` and test.
- Executor: Exists, with test.

### What's Missing or Incomplete
- No clear integration with live data fetcher: Strategy/backtest/risk modules need to be wired to real data.
- No clear paper-trade loop: Should be a loop or cron job that fetches data, runs strategy, executes trades, and writes to DB.
- No clear stats computation (Sharpe, P/L): PRD requires backtest stats.
- No clear enforcement of risk model in executor.

---

## 3. Frontend (Next.js, TailwindCSS, Vercel)

### What Exists
- Directory structure only: `components/`, `pages/`, `public/`, `styles/`, `utils/` exist, but all are empty.

### What's Missing or Incomplete
- All frontend features are missing: No dashboard, portfolio table, trade feed, performance chart, signal panel, about/methodology, or disclaimer banner.
- No TailwindCSS setup or styles.
- No API integration for fetching backend data.
- No legal disclaimers or tooltips.
- No accessibility or responsive layout.

---

## 4. Testing

### What Exists
- Backend tests: Good coverage in `backend/tests/` (API, DB, utils, integration, e2e, deployment).
- Bot tests: Present for backtest, risk, strategy, executor.

### What's Missing or Incomplete
- No frontend tests (unit/integration).
- No explicit test for 5-min cron job or end-to-end bot-to-dashboard flow.
- No test for legal disclaimer presence.

---

## 5. Other Gaps

- No clear documentation for API endpoints (OpenAPI/Swagger).
- No clear deployment scripts for Vercel (frontend) or Render (backend).
- No explicit cost monitoring or analytics integration.
- No persistent trade history analytics dashboard.
- No explicit accessibility (WCAG 2.1) checks.

---

## Summary Table

| Area         | Exists? | Missing/Incomplete? |
|--------------|---------|---------------------|
| Backend API  |   ✔     | Edge/cron, delay field, retry/backoff, legal disclaimer, OpenAPI |
| DB Layer     |   ✔     | -                   |
| Data Fetcher |   ?     | Tiingo/AV/yfinance fetch, retry/backoff |
| Bot Logic    |   ✔     | Live loop, risk enforcement, stats, integration |
| Frontend     |   ✗     | All pages/components, styles, API integration, disclaimers, accessibility |
| Testing      |   ✔     | Frontend, E2E, disclaimer, cron job |
| Deployment   |   ?     | Vercel/Render scripts, cost monitoring |
| Docs         |   ?     | API docs, architecture diagrams (except PRD) |

---

## Next Steps

1. [ ] Implement the missing backend features (cron, data fetcher, risk enforcement, API fields, retry logic).
    - [x] **Cron/Loop for 5-Minute Bot Run**: Create a script to run the bot loop and set up a cron job or background scheduler to execute it every 5 minutes.
    - [x] **Market Data Fetcher**: Implement or complete the fetcher module to retrieve OHLCV data from providers (e.g., yfinance), with retry/backoff logic.
    - [x] **Risk Model Enforcement**: Ensure 2% equity per trade, 5% stop-loss, and max 3 open positions are enforced in the bot logic.
    - [x] **API Field for `data_delay_minutes`**: Add this field to relevant API responses and update models and logic accordingly.
    - [x] **Retry/Backoff Logic for API Errors**: Add retry and backoff logic to all critical external API calls (data fetch, trade execution).
    - [x] **Legal Disclaimer in API Responses**: Add a legal disclaimer field to all API responses and update models and logic.
    - [x] **Edge API Separation (Optional/Stretch)**: Document FastAPI's limitations for edge, and scaffold a placeholder if needed.
    - [x] **Fix DB test failures**: Update result handling for Supabase client API, check DB schema for upsert constraints, and resolve test errors.
    - [x] **(Optional) Add/expand tests for bot runner and cron integration**: Ensure the new trading loop and cron job are covered by tests.
    - [ ] **Update documentation**: Document new backend features and cron job integration.
    - [ ] **Fix remaining test errors**:
        - [ ] Update Trade creation and tests to always provide a unique, non-null order_id.
        - [ ] Set valid SUPABASE_URL and SUPABASE_KEY in test environment.
2. [ ] Scaffold and build the entire frontend.
3. [ ] Add legal disclaimers everywhere.
4. [ ] Add missing tests (especially frontend and E2E).
5. [ ] Add deployment/config scripts and documentation.
