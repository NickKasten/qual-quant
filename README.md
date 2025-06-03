# Summer 2025 Personal Project: "Vibe"-Trading System

An informed, agent-assisted, "vibe-coded" investment trading agent for local use.

Current trading system: combined SAC (Soft Actor-Critic) reinforcement learning with LLM-based decision validation.

Current portfolio: Top 5 Dow Jones tickers.

## Project Structure

```
vibe-trading/
├── data/
│   ├── raw/                 # Raw data from different sources
│   ├── processed/           # Processed and merged data
│   └── news/               # Historical news data
├── models/
│   ├── sac/                # SAC model implementation
│   └── llm/                # LLM integration
├── src/
│   ├── data_collection.py  # Data fetching and preprocessing
│   ├── environment.py      # Trading environment
│   ├── sac_agent.py        # SAC implementation
│   ├── llm_validator.py    # LLM decision validation
│   └── trading.py          # Trading execution
└── config/
    └── config.yaml         # Configuration parameters
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with your API keys:
```
YH_FINANCE_API_KEY=your_key
TIINGO_API_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
NEWS_API_KEY=your_key
```

3. Run the system:
```bash
python src/main.py
```

## Features

- Multi-source data collection (Yahoo Finance, Tiingo, Alpha Vantage)
- Cross-verified OHLCV data
- SAC reinforcement learning model
- LLM-based decision validation
- Historical news analysis
- Portfolio optimization
- Risk management
- Performance monitoring

## Data Sources

- Yahoo Finance
- Tiingo
- Alpha Vantage
- Historical news archives

## Model Architecture

1. SAC Model:
   - State space: Market data, technical indicators
   - Action space: Trading decisions
   - Reward function: Portfolio returns

2. LLM Validator:
   - Input: SAC decisions + news context
   - Output: Final trading decision
   - Training: Historical news and market data

## Long-term Goal: 

Generate a team of agents to form an agentic-hedge fund.

## License

MIT License 