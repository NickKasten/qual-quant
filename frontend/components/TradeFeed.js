import { useState, useEffect } from 'react';
import ApiClient from '../utils/api';

export default function TradeFeed() {
  const [trades, setTrades] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [symbolFilter, setSymbolFilter] = useState('');

  useEffect(() => {
    fetchTrades();
  }, [currentPage, symbolFilter]);

  const fetchTrades = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getTrades(
        currentPage, 
        20, 
        symbolFilter || null
      );
      setTrades(data.trades || []);
      setPagination(data.pagination);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$---.--';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatDateTime = (timestamp) => {
    if (!timestamp) {
      return 'Unknown time';
    }
    try {
      return new Date(timestamp).toLocaleString();
    } catch (error) {
      return 'Invalid date';
    }
  };

  const safeNumber = (value) => {
    if (value === null || value === undefined || isNaN(value)) {
      return 0;
    }
    return Number(value);
  };

  const getSideColor = (side) => {
    return side?.toLowerCase() === 'buy' ? 'text-green-600' : 'text-red-600';
  };

  const getSideBadge = (side) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    const colorClasses = side?.toLowerCase() === 'buy' 
      ? 'bg-green-100 text-green-800' 
      : 'bg-red-100 text-red-800';
    
    return `${baseClasses} ${colorClasses}`;
  };

  const handleSymbolFilterChange = (e) => {
    setSymbolFilter(e.target.value);
    setCurrentPage(1);
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  if (loading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="grid grid-cols-6 gap-4">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded"></div>
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
            <h3 className="text-lg leading-6 font-medium text-gray-900">Trade Feed</h3>
            <button 
              onClick={fetchTrades}
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-sm">😵</span>
                </div>
              </div>
            </div>
            <h4 className="text-xl font-medium text-gray-900 mb-3">
              🚫 Houston, We Have a Problem!
            </h4>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Our trading history seems to have gone on vacation without telling us. 
              Don't worry though - it's probably just taking a coffee break! ☕
            </p>
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 inline-block max-w-lg">
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span className="font-medium">Error Details:</span>
              </div>
              <p className="mt-1 text-xs">{error}</p>
            </div>
          </div>

          <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
            <div className="text-center">
              <h5 className="text-lg font-medium text-indigo-900 mb-2">
                🎭 Preview Mode Activated!
              </h5>
              <p className="text-sm text-indigo-800 mb-4">
                Here's what your trade history will look like once everything is connected:
              </p>
              <div className="bg-white rounded-lg shadow-sm border border-indigo-200 p-4">
                <div className="grid grid-cols-6 gap-4 text-xs text-gray-500 mb-3 border-b pb-2">
                  <div>Timestamp</div>
                  <div>Symbol</div>
                  <div>Side</div>
                  <div>Quantity</div>
                  <div>Price</div>
                  <div>Total</div>
                </div>
                <div className="space-y-2 text-sm text-gray-400">
                  <div className="grid grid-cols-6 gap-4 py-2 bg-gray-50 rounded">
                    <div>2024-06-20 10:30</div>
                    <div>AAPL</div>
                    <div><span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs">BUY</span></div>
                    <div>10</div>
                    <div>$195.50</div>
                    <div>$1,955.00</div>
                  </div>
                  <div className="grid grid-cols-6 gap-4 py-2 bg-gray-50 rounded">
                    <div>2024-06-20 11:15</div>
                    <div>TSLA</div>
                    <div><span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">SELL</span></div>
                    <div>5</div>
                    <div>$180.25</div>
                    <div>$901.25</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Trade Feed</h3>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Filter by symbol"
              value={symbolFilter}
              onChange={handleSymbolFilterChange}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <span className="text-sm text-gray-500">
              {pagination?.total_count || 0} total trades
            </span>
          </div>
        </div>

        {trades.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Side
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fill Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Value
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {trades.map((trade, index) => (
                    <tr key={trade.id || index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(trade.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {trade.symbol || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getSideBadge(trade.side)}>
                          {trade.side?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {safeNumber(trade.quantity) || '--'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(trade.fill_price || trade.price)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(safeNumber(trade.quantity) * safeNumber(trade.fill_price || trade.price))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {pagination && pagination.total_pages > 1 && (
              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-700">
                  Showing page {pagination.page} of {pagination.total_pages}
                  ({pagination.total_count} total trades)
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage <= 1}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Previous
                  </button>
                  
                  {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => {
                    const page = i + 1;
                    return (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`px-3 py-1 text-sm border rounded-md ${
                          currentPage === page
                            ? 'bg-primary-600 text-white border-primary-600'
                            : 'border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage >= pagination.total_pages}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <svg className="w-20 h-20 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <span className="text-xs">💤</span>
                </div>
              </div>
            </div>
            
            {symbolFilter ? (
              <div>
                <h4 className="text-xl font-medium text-gray-900 mb-3">
                  📊 No {symbolFilter} Adventures Yet!
                </h4>
                <p className="text-gray-600 mb-4 max-w-md mx-auto">
                  Looks like our AI bot hasn't taken a swing at <span className="font-semibold">{symbolFilter}</span> yet. 
                  Maybe it's being picky, or perhaps it's waiting for the perfect moment to strike! 🎯
                </p>
                <button
                  onClick={() => setSymbolFilter('')}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  Show All Trades
                </button>
              </div>
            ) : (
              <div>
                <h4 className="text-xl font-medium text-gray-900 mb-3">
                  🤖 The Trading Bot is Feeling Shy
                </h4>
                <p className="text-gray-600 mb-4 max-w-md mx-auto">
                  No trades to show yet! Our AI is probably still analyzing the market, 
                  sipping digital coffee, and perfecting its strategy. Give it a moment to work its magic! ✨
                </p>
                <div className="bg-blue-50 rounded-lg p-4 max-w-lg mx-auto">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">💡</span>
                    </div>
                    <div className="ml-3 text-left">
                      <h5 className="text-sm font-medium text-blue-900">Pro Tip</h5>
                      <p className="text-sm text-blue-800 mt-1">
                        Trades appear here when market conditions trigger our SMA crossover + RSI strategy. 
                        The bot runs every 5 minutes during market hours (9:30 AM - 4:00 PM ET).
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="mt-8 flex justify-center space-x-4 text-sm text-gray-400">
              <span>🕘 Checking every 5 minutes</span>
              <span>•</span>
              <span>📈 SMA + RSI Strategy</span>
              <span>•</span>
              <span>🎯 Paper Trading Only</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}