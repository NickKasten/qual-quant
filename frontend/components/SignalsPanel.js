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
    if (signal === 'BUY') return 'text-green-600 bg-green-100';
    if (signal === 'SELL') return 'text-red-600 bg-red-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getSignalIcon = (signal) => {
    if (signal === 'BUY') {
      return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414-1.414L9 5.586 7.707 4.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L10 4.414l2.293 2.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
        </svg>
      );
    }
    if (signal === 'SELL') {
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
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Trading Signals</h3>
            <button 
              onClick={fetchSignals}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Retry
            </button>
          </div>
          
          <div className="text-center py-12">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-sm">⚡</span>
                </div>
              </div>
            </div>
            <h4 className="text-xl font-medium text-gray-900 mb-3">
              📡 Signal Transmission Lost!
            </h4>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Our crystal ball seems to be a bit foggy right now. The trading signals are playing hide and seek, 
              but don't worry - they'll be back once our digital fortune teller gets its act together! 🔮
            </p>
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 inline-block max-w-lg">
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">Technical Details:</span>
              </div>
              <p className="mt-1 text-xs">{error}</p>
            </div>
          </div>

          <div className="mt-8 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6">
            <div className="text-center mb-6">
              <h5 className="text-lg font-medium text-purple-900 mb-2">
                🎪 Signal Preview Theater!
              </h5>
              <p className="text-sm text-purple-800">
                Here's what our AI's trading signals look like when they're feeling chatty:
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border border-purple-200 p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-gray-400">AAPL</h4>
                <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414-1.414L9 5.586 7.707 4.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4a1 1 0 00-1.414-1.414L10 4.414l2.293 2.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
                  </svg>
                  BUY
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-gray-400">
                <div>
                  <dt className="text-sm font-medium">SMA 20</dt>
                  <dd className="mt-1 text-sm">195.42</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">SMA 50</dt>
                  <dd className="mt-1 text-sm">190.18</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">RSI</dt>
                  <dd className="mt-1 text-sm">68.5</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Current Price</dt>
                  <dd className="mt-1 text-sm">$196.75</dd>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h5 className="text-sm font-medium text-gray-400 mb-2">Signal Conditions</h5>
                <div className="space-y-1">
                  <div className="flex items-center text-sm text-gray-400">
                    <div className="w-2 h-2 rounded-full mr-2 bg-green-400"></div>
                    <span>SMA CROSSOVER: Met ✨</span>
                  </div>
                  <div className="flex items-center text-sm text-gray-400">
                    <div className="w-2 h-2 rounded-full mr-2 bg-green-400"></div>
                    <span>RSI FILTER: Met 🎯</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <span className="text-2xl">🧠</span>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-900 mb-2">How Our AI Brain Works</h4>
                <p className="text-sm text-blue-800">
                  Our signals use a 20/50-day SMA crossover strategy with RSI filter. 
                  <strong>BUY</strong> signals fire when SMA20 &gt; SMA50 and RSI &lt; 70. 
                  <strong>SELL</strong> signals trigger when SMA20 &lt; SMA50 and RSI &gt; 30.
                  It's like having a very patient, mathematical friend who never gets tired of watching charts! 📊
                </p>
              </div>
            </div>
          </div>
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
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSignalColor(data.signal)}`}>
                      {getSignalIcon(data.signal)}
                      <span className="ml-1">{data.signal || 'HOLD'}</span>
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
          <div className="text-center py-16">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <svg className="w-20 h-20 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <span className="text-xs">🔍</span>
                </div>
              </div>
            </div>
            
            <h4 className="text-xl font-medium text-gray-900 mb-3">
              🤫 The Signals are Being Mysterious
            </h4>
            <p className="text-gray-600 mb-6 max-w-lg mx-auto">
              Our AI trading signals are currently in stealth mode! They might be cooking up something brilliant 
              in the background, or perhaps they're just taking a well-deserved break from all that intense market analysis. 🧐
            </p>
            
            <div className="bg-amber-50 rounded-lg p-6 max-w-lg mx-auto">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <span className="text-2xl">🎯</span>
                </div>
                <div className="ml-3 text-left">
                  <h5 className="text-sm font-medium text-amber-900 mb-2">What's Coming Next?</h5>
                  <p className="text-sm text-amber-800">
                    Signals will appear here when our AI detects trading opportunities using the SMA crossover + RSI strategy. 
                    The system analyzes market data hourly but only executes trades once per day during trading hours.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mt-8 flex justify-center space-x-6 text-sm text-gray-400">
              <div className="flex items-center">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                <span>BUY signals</span>
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-red-400 rounded-full mr-2"></span>
                <span>SELL signals</span>
              </div>
              <div className="flex items-center">
                <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                <span>HOLD signals</span>
              </div>
            </div>
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