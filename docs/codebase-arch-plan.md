vibe-trading/
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/              # API route definitions (e.g., /portfolio, /trades)
│   │   ├── core/             # Config, constants, environment variables
│   │   ├── db/               # Supabase/Postgres DB interaction layer
│   │   ├── models/           # Pydantic models (requests, responses, DB schemas)
│   │   ├── services/         # Business logic (fetcher, strategy, trading logic)
│   │   ├── utils/            # Helper functions (logging, retry, etc.)
│   │   └── main.py           # FastAPI app entry point
│   │
│   └── tests/                # Unit + integration tests
│       ├── api/
│       ├── services/
│       ├── db/
│       └── conftest.py       # Pytest setup
│
├── bot/                      # AI trading bot logic
│   ├── strategy/             # SMA/RSI logic
│   ├── risk/                 # Risk model (2% equity, stop-loss, etc.)
│   ├── executor/             # Trade execution + paper trading loop
│   ├── backtest/             # Backtest logic using backtesting.py
│   └── run_bot.py            # Entrypoint for cron/container
│
├── frontend/                 # Next.js app (deployed to Vercel)
│   ├── components/           # Reusable UI components (table, charts, etc.)
│   ├── pages/                # Routes: index.tsx, /about, etc.
│   ├── public/               # Static assets (icons, legal disclaimer, etc.)
│   ├── styles/               # Tailwind config & global CSS
│   └── utils/                # Fetchers, constants, API helpers
│
├── deployments/              # Docker, cron, and Vercel configs
│   ├── Dockerfile.backend
│   ├── docker-compose.yml
│   ├── vercel.json
│   └── supabase_schema.sql   # Schema migration script (optional)
│
├── .env                      # Root env (do not commit!)
├── .gitignore
├── README.md
└── pyproject.toml            # Shared Python config (backend & bot)
