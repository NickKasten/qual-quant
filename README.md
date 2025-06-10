# Summer 2025 Personal Project: "Vibe"-Trading System

An informed, agent-assisted, "vibe-coded" investment trading agent for local use.

## Current trading system: 

Combined SAC (Soft Actor-Critic) or PPO (Proximal Policy Optimization) reinforcement learning with LLM-based decision validation using Google's Gemini.

## Current portfolio: 

Top 5 Dow Jones tickers (AAPL, MSFT, JPM, V, WMT).

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
│   └── ppo/                # PPO model implementation and saved models
├── src/
│   ├── data_collection.py  # Data fetching and preprocessing
│   ├── environment.py      # Trading environment with technical indicators
│   ├── sac_agent.py        # SAC implementation
│   ├── ppo_agent.py        # PPO implementation
│   ├── llm_validator.py    # LLM decision validation using Gemini
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
GOOGLE_API_KEY=your_key  # Required for Gemini LLM validation
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
- Dual reinforcement learning models
  - SAC (Soft Actor-Critic)
    - Continuous action space for portfolio allocation
    - Sophisticated reward function with trading penalties
  - PPO (Proximal Policy Optimization)
    - Stable policy updates
    - Adaptive learning rate
  - Comprehensive training metrics and visualization
- LLM-based decision validation using Google's Gemini
  - Real-time trading decision validation
  - Historical validation tracking
  - Fallback to RL model decisions if validation fails
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

2. PPO Model:
   - State space: Same as SAC
   - Action space: Continuous portfolio allocation
   - Proximal policy optimization for stable learning
   - Adaptive learning rate mechanism

3. LLM Validator (Gemini):
   - Input: RL model decisions + market context
   - Output: Validated trading decisions
   - Features: News sentiment, market conditions, historical patterns

## Current thoughts

SAC took much longer to train (and proved difficult to vibe), so swapped to PPO for efficiency.
Waiting to test out Gemini's performance as a validator.
Excited for (but wary of) refactoring the project so I can add the web-app to display the agent's "abilities".

## Long-term Goal

Generate a team of agents to form an agentic-hedge fund.

## License

Apache License 
