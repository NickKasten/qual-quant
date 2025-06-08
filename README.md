# Summer 2025 Personal Project: "Vibe"-Trading System

An informed, agent-assisted, "vibe-coded" investment trading agent for local use.

Current trading system: combined SAC (Soft Actor-Critic) reinforcement learning with LLM-based decision validation.

Current portfolio: Top 5 Dow Jones tickers (AAPL, MSFT, JPM, V, WMT).

## Project Structure

```
vibe-trading/
├── data/
│   ├── raw/                 # Raw data from different sources
│   ├── processed/           # Processed and merged data
│   ├── training_metrics/   # Training performance metrics
│   └── training_plots/     # Training visualization plots
├── models/
│   ├── sac/                # SAC model implementation and saved models
│   └── llm/                # LLM integration
├── src/
│   ├── data_collection.py  # Data fetching and preprocessing
│   ├── environment.py      # Trading environment with technical indicators
│   ├── sac_agent.py        # SAC implementation
│   ├── llm_validator.py    # LLM decision validation
│   ├── trading.py          # Trading execution and system management
│   └── main.py            # Main entry point with train/live modes
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
OPENAI_API_KEY=your_key  # Required for LLM validation
```

3. Run the system:
```bash
# Training mode
python src/main.py --mode train

# Live trading mode with LLM validation
python src/main.py --mode live
```

## Features

- Multi-source data collection and cross-verification
  - Yahoo Finance
  - Tiingo
  - Alpha Vantage
  - Historical news archives
- Advanced technical analysis
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
- SAC reinforcement learning model
  - Continuous action space for portfolio allocation
  - Sophisticated reward function with trading penalties
  - Comprehensive training metrics and visualization
- LLM-based decision validation
  - Real-time trading decision validation
  - Historical validation tracking
  - Fallback to SAC decisions if validation fails
- Portfolio management
  - Dynamic position sizing
  - Cash management
  - Risk-adjusted returns
- Performance monitoring
  - Training metrics tracking
  - Portfolio value history
  - Validation decision history
  - Automated performance visualization

## Model Architecture

1. SAC Model:
   - State space:
     - Market data (OHLCV)
     - Technical indicators (RSI, MACD, Bollinger Bands)
     - Portfolio state (positions + cash)
   - Action space: Continuous portfolio allocation for each ticker
   - Reward function: Portfolio returns with trading penalties

2. LLM Validator:
   - Input: SAC decisions + market context
   - Output: Validated trading decisions
   - Features: News sentiment, market conditions, historical patterns

## Long-term Goal

Generate a team of agents to form an agentic-hedge fund.

## License

Apache License 
