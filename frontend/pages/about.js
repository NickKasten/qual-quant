import Head from 'next/head';

export default function About() {
  return (
    <>
      <Head>
        <title>About - QualQuant Strategy</title>
        <meta name="description" content="Learn about the AI trading strategy, methodology, and risk management" />
      </Head>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">About Our Trading Strategy</h1>
          <p className="mt-2 text-sm text-gray-600">
            Understanding the methodology behind our AI trading bot
          </p>
        </div>

        <div className="bg-white shadow rounded-lg divide-y divide-gray-200">
          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Trading Strategy</h2>
            <div className="prose max-w-none">
              <p className="text-gray-600">
                Our AI trading bot employs a systematic approach based on technical analysis indicators:
              </p>
              <ul className="mt-4 space-y-2 text-gray-600">
                <li><strong>SMA Crossover:</strong> Uses 20-day and 50-day Simple Moving Averages to identify trend direction</li>
                <li><strong>RSI Filter:</strong> Relative Strength Index (70/30 levels) to avoid overbought/oversold conditions</li>
                <li><strong>Paper Trading:</strong> All trades are simulated - no real capital at risk</li>
                <li><strong>Data Delay:</strong> Uses delayed market data (≥15 minutes) as per regulations</li>
              </ul>
            </div>
          </div>

          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Risk Management</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Position Sizing</h3>
                <p className="text-gray-600">Maximum 2% of account equity per trade</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Stop Loss</h3>
                <p className="text-gray-600">Automatic 5% stop-loss on all positions</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Position Limits</h3>
                <p className="text-gray-600">Maximum 3 open positions at any time</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Market Hours</h3>
                <p className="text-gray-600">Trading only during regular market hours</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Data Sources</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Market Data</h3>
                <p className="text-gray-600">
                  Primary: Tiingo API for OHLCV data<br />
                  Fallback: Alpha Vantage for backup data<br />
                  Historical: Yahoo Finance for backtesting
                </p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Execution</h3>
                <p className="text-gray-600">
                  Alpaca Markets paper trading API for simulated order execution
                </p>
              </div>
            </div>
          </div>

          <div className="p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Returns</h3>
                <p className="text-gray-600">Total return percentage over time</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Sharpe Ratio</h3>
                <p className="text-gray-600">Risk-adjusted return measurement</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">Maximum Drawdown</h3>
                <p className="text-gray-600">Largest peak-to-trough decline</p>
              </div>
            </div>
          </div>

          <div className="p-6 bg-yellow-50">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Important Disclaimers</h2>
            <div className="space-y-3 text-sm text-gray-700">
              <p>
                <strong>Educational Purpose Only:</strong> This dashboard is for educational and demonstration purposes only. 
                All trading results are simulated and do not represent actual trading performance.
              </p>
              <p>
                <strong>Not Investment Advice:</strong> The information provided here should not be considered as investment advice. 
                Past performance does not guarantee future results.
              </p>
              <p>
                <strong>Data Delays:</strong> All market data is delayed by at least 15 minutes and should not be used for real-time trading decisions.
              </p>
              <p>
                <strong>Risk Warning:</strong> Trading involves substantial risk of loss and is not suitable for all investors. 
                Please consult with a qualified financial advisor before making any investment decisions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}