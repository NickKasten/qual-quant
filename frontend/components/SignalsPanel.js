import { useState, useEffect } from 'react';
import ApiClient from '../utils/api';

export default function SignalsPanel() {
  const [signals, setSignals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSignals();
  }, []);

  const fetchSignals = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getSignals();
      setSignals(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal) => {
    const normalized = (signal || '').toUpperCase();
    if (normalized === 'BUY') return 'text-green-600 bg-green-100';
    if (normalized === 'SELL') return 'text-red-600 bg-red-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getSignalIcon = (signal) => {
    const normalized = (signal || '').toUpperCase();
    if (normalized === 'BUY') {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414-1.414L9 5.586 7.707 4.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L10 4.414l2.293 2.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
        </svg>
      );
    }
    if (normalized === 'SELL') {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-11a1 1 0 112 0v2a1 1 0 11-2 0V7zm0 6a1 1 0 112 0 1 1 0 01-2 0z" clipRule="evenodd" />
      </svg>
    );
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return '---.--';
    }
    if (typeof value === 'number') {
      return value.toFixed(2);
    }
    return value?.toString() || '---.--';
  };

  const formatPrice = (value) => {
    if (value === null || value === undefined) {
      return '$---.--';
    }
    if (typeof value === 'number') {
      return `$${value.toFixed(2)}`;
    }
    return value?.toString() || '$---.--';
  };

  if (loading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="h-3 bg-gray-200 rounded"></div>
                    <div className="h-3 bg-gray-200 rounded"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Trading Signals</h3>
            <button
              onClick={fetchSignals}
              className="text-sm text-primary-600 hover:text-primary-800"
            >
              Retry
            </button>
          </div>
          <p className="text-sm text-gray-600">
            Signals could not be refreshed. Make sure the API is reachable and that market-data credentials are valid.
          </p>
          <p className="mt-3 text-xs text-red-600 bg-red-50 rounded px-3 py-2 font-mono break-all">
            {error}
          </p>
        </div>
      </div>
    );
  }

  const signalsData = signals?.signals || {};

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Trading Signals</h3>
          <div className="text-sm text-gray-500">
            Data delayed {signals?.data_delay_minutes || 15} minutes
          </div>
        </div>

        {Object.keys(signalsData).length > 0 ? (
          <div className="space-y-6">
            {Object.entries(signalsData).map(([symbol, data]) => (
              <div key={symbol} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-medium text-gray-900">{symbol}</h4>
                  {data.error ? (
                    <span className="text-red-600 text-sm">Error: {data.error}</span>
                  ) : (
                  {(() => {
                    const normalizedSignal = (data.signal || 'HOLD').toUpperCase();
                    return (
                      <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSignalColor(normalizedSignal)}`}>
                        {getSignalIcon(normalizedSignal)}
                        <span className="ml-1">{normalizedSignal}</span>
                      </div>
                    );
                  })()}
                    </div>
                  )}
                </div>

                {!data.error && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <dt className="text-sm font-medium text-gray-500">SMA 20</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatValue(data.sma_20)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">SMA 50</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatValue(data.sma_50)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">RSI</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatValue(data.rsi)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Current Price</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatPrice(data.current_price)}
                      </dd>
                    </div>
                  </div>
                )}

                {!data.error && data.conditions && (
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-500 mb-2">Signal Conditions</h5>
                    <div className="space-y-1">
                      {Object.entries(data.conditions).map(([condition, met]) => (
                        <div key={condition} className="flex items-center text-sm">
                          <div className={`w-2 h-2 rounded-full mr-2 ${met ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                          <span className={met ? 'text-green-700' : 'text-gray-600'}>
                            {condition.replace(/_/g, ' ').toUpperCase()}: {met ? 'Met' : 'Not Met'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-sm text-gray-600">
            No live signals are available yet. The strategy publishes updated guidance after the next analysis cycle.
          </div>
        )}

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Strategy Information</h4>
          <p className="text-sm text-blue-800">
            Signals are generated using a 20/50-day SMA crossover strategy with RSI filter. 
            BUY signals require SMA20 &gt; SMA50 and RSI &lt; 70. SELL signals require SMA20 &lt; SMA50 and RSI &gt; 30.
          </p>
        </div>

        {signals?.timestamp && (
          <div className="mt-4 text-xs text-gray-400">
            Last updated: {new Date(signals.timestamp).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}
