# AI Trading Bot & Live Dashboard — Unified MVP PRD (7‑Day Sprint)

## 1. Purpose & Vision

Create an end‑to‑end, **transparent sandbox** where an AI trading bot both **generates trades** (paper‑trading via Alpaca) and **broadcasts its portfolio, trade log, and performance** through a public web dashboard.  The build must finish in **one calendar week**, leveraging autonomous **AI developer agents** for boiler‑plate coding, testing, and documentation, while the human developer handles product direction, design tweaks, and final QA.

---

## 2. Goals & Success Metrics

| Goal                      | KPI / Target                                                      |
| ------------------------- | ----------------------------------------------------------------- |
| Functional AI bot         | Generates at least one simulated trade in live mode by Day 7      |
| Transparent dashboard     | Portfolio & equity curve refresh ≤ 15 min after data is available |
| Educational, not advisory | Disclaimers on 100 % of screens                                   |
| Cost‑efficient            | Run‑time cloud costs ≤ $25 month                                 |
| Fast build                | **All core features shipped by Day 7**                            |
| Resilient                 | 99 % uptime during U.S. market hours                              |

---

## 3. Assumptions

- Paper‑trading only; no real capital at risk.
- Bot trades U.S. equities/ETFs with delayed quotes (≥ 15 min).
- Free/cheap tiers (Render, Vercel, Supabase) are acceptable.
- No end‑user accounts; optional email capture at most.

---

## 4. Scope (MVP)

### 4.1 Core User Stories

1. As a visitor, I see an up‑to‑date snapshot of the bot’s portfolio when I land on the site.
2. As a visitor, I can inspect a time‑stamped feed of every simulated order.
3. As a curious engineer, I can read how the strategy works and view back‑test stats.
4. As a compliance‑minded user, I see a clear disclaimer on every page.

### 4.2 Features

| Page / Component        | Functionality                                           |
| ----------------------- | ------------------------------------------------------- |
| **Home / Dashboard**    | Portfolio table, current equity, P/L, delayed timestamp |
| **Performance Chart**   | Equity curve vs. S&P 500 (delayed)                      |
| **Trade Feed**          | Ticker, side, quantity, fill price, time                |
| **Signal Panel**        | Latest SMA/RSI signals & status                         |
| **About / Methodology** | Strategy logic, data sources, risk limits               |
| **Footer / Banner**     | Always‑on legal & educational disclaimers               |

### 4.3 Out of Scope (Week‑1)

- Real‑time (< 60 s) quotes
- Multi‑asset support (crypto, FX)
- User log‑ins or watchlists
- Mobile app

---

## 5. Functional Requirements

| #    | Requirement                                                                               |
| ---- | ----------------------------------------------------------------------------------------- |
| FR‑1 | Fetch OHLCV data from Tiingo (primary) or Alpha Vantage (fallback) respecting rate limits |
| FR‑2 | Bot runs every 5 min (cron/container); writes trades & positions to Postgres              |
| FR‑3 | Strategy = 20‑ / 50‑day SMA crossover **AND** RSI filter (70/30)                          |
| FR‑4 | Risk: 2 % account equity per trade, 5 % stop‑loss, max 3 open positions                   |
| FR‑5 | REST Edge API exposes portfolio, trades, and `data_delay_minutes` field                   |
| FR‑6 | Dashboard refresh interval ≤ 15 min, TTFB ≤ 1 s on Vercel edge                            |
| FR‑7 | Banner disclaimer visible on every route                                                  |

---

## 6. Non‑Functional Requirements

| Category      | Requirement                                               |
| ------------- | --------------------------------------------------------- |
| Performance   | ≤ 1 s TTFB; page interactive ≤ 2 s                        |
| Reliability   | Automatic retry / exponential back‑off on data/API errors |
| Security      | No browser access to secrets; env vars stored server‑side |
| Accessibility | WCAG 2.1 AA; full keyboard nav                            |
| Cost          | ≤ $25 month (free tiers preferred)                       |

---

## 7. Data & API Plan

| Need                   | Source        | Rate Limit      | Mitigation         |
| ---------------------- | ------------- | --------------- | ------------------ |
| Intraday & daily OHLCV | Tiingo        | 500 calls / day | Cache in KV store  |
| Backup intraday        | Alpha Vantage | 5 calls / min   | Rotate free keys   |
| Historical daily       | yfinance      | Unlimited       | Fetch once nightly |

---

## 8. System Architecture (MVP)

```mermaid
graph TD
    subgraph Backend
        A[AI Trading Bot (Docker + Python)] -- writes --> B[Supabase /Postgres]
        C[Market‑Data Fetcher] -- writes --> B
    end
    subgraph API Edge (FastAPI)
        D[Read‑Only JSON Endpoints] -- fetch --> B
    end
    subgraph Frontend
        E[Next.js Site (Vercel)] -- request --> D
    end
    F(User Browser) -- HTTPS --> E
```

---

## 9. Development & Implementation Timeline (7 Days)

| Day              | Focus                | Key Tasks                                                                    | Owner          |
| ---------------- | -------------------- | ---------------------------------------------------------------------------- | -------------- |
| **0 (kick‑off)** | Project skeleton     | Finalise this PRD; repo + CI/CD; install deps                                | *Nick*         |
| **1**            | Data pipeline        | Build Tiingo/AV fetcher; seed DB with 1‑year history                         | *Agent*        |
| **2**            | Core strategy        | Implement SMA/RSI logic; unit tests                                          | *Agent*        |
| **3**            | Backtesting & risk   | Integrate `backtesting.py`; compute Sharpe, P/L stats; add 2 % risk model    | *Agent*        |
| **4**            | Paper‑trade loop     | Hook Alpaca paper API; cron job every 5 min; write to DB                     | *Agent*        |
| **5**            | Dashboard UI         | Scaffold Next.js pages; portfolio table, trade feed, chart; Tailwind styling | *Nick + Agent* |
| **6**            | Polish & disclaimers | Add legal banner; accessibility pass; lighthouse ≥ 90                        | *Nick*         |
| **7**            | E2E QA & deploy      | Smoke test; fix bugs; deploy on Vercel; announce beta                        | *Nick*         |

> **Timeboxing:** Each task is capped at 4 h; if overrun, cut scope before timeline slips.

---

## 10. UX & Content Guidelines

1. **Banner** (persistent):
   > “Simulated paper‑trading results. Prices delayed ≥ 15 minutes. Educational content only — *not* investment advice.”
2. Neutral greys/blues; avoid “casino” reds/greens.
3. Tooltips explain delayed data, risk limits, and P/L math.
4. Responsive Tailwind layout; test mobile ≤ 375 px.

---

## 11. Risks & Mitigations

| Area       | Risk                    | Mitigation                        |
| ---------- | ----------------------- | --------------------------------- |
| Data       | Tiingo trial expiry     | Swap to IEX Cloud or Polygon Lite |
| Compliance | Disclaimer insufficient | Quick legal review by Day 6       |
| Rate limit | Alpha Vantage 5 / min   | Rotate keys; back‑off logic       |
| Over‑scope | Dash features creep     | Daily stand‑ups; scope lock       |

---

## 12. Future Enhancements

- Advanced indicators (MACD, Bollinger)
- ML‑based pattern recognition
- Multi‑asset (crypto, FX)
- Mobile push / SMS alerts
- Cloud autoscale on AWS/GCP
- Persistent trade history + analytics dashboard

---

## 13. Glossary

- **SMA 20/50** — Simple moving averages over 20 & 50 trading days.
- **RSI** — Relative Strength Index; momentum oscillator (0‑100).
- **Paper Trade** — Simulated order without real execution.
- **P/L** — Profit & Loss, gross of costs.
- **Edge Function** — Serverless function deployed at CDN edge.

---

**Status:** Draft v0.2
**Prepared by:** Nick Kasten
**Iterated with:** ChatGPT and Perplexity
