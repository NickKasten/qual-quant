import { useState, useEffect } from 'react';
import ApiClient from '../utils/api';

export default function PortfolioSummary() {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getPortfolio();
      setPortfolio(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercent = (value) => {
    const percent = (value / portfolio?.current_equity * 100) || 0;
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
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
            <h3 className="text-lg leading-6 font-medium text-gray-900">Portfolio Summary</h3>
            <button 
              onClick={fetchPortfolio}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Retry
            </button>
          </div>
          
          <div className="text-center py-8">
            <div className="flex justify-center mb-4">
              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">Portfolio Data Unavailable</h4>
            <p className="text-gray-500 mb-4">Unable to connect to trading backend</p>
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md inline-block">
              {error}
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6 opacity-50">
            <div>
              <dt className="text-sm font-medium text-gray-500">Current Equity</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-400">$--,---</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Total P/L</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-400">$--,---</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Open Positions</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-400">--</dd>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Portfolio Summary</h3>
          <div className="text-sm text-gray-500">
            Data delayed {portfolio?.data_delay_minutes || 15} minutes
          </div>
        </div>
        
        <div className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <dt className="text-sm font-medium text-gray-500">Current Equity</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">
                {formatCurrency(portfolio?.current_equity || 0)}
              </dd>
            </div>
            
            <div>
              <dt className="text-sm font-medium text-gray-500">Total P/L</dt>
              <dd className={`mt-1 text-3xl font-semibold ${
                (portfolio?.total_pl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(portfolio?.total_pl || 0)}
              </dd>
              <dd className={`text-sm ${
                (portfolio?.total_pl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercent(portfolio?.total_pl || 0)}
              </dd>
            </div>
            
            <div>
              <dt className="text-sm font-medium text-gray-500">Open Positions</dt>
              <dd className="mt-1 text-3xl font-semibold text-gray-900">
                {portfolio?.positions?.length || 0}
              </dd>
            </div>
          </div>
        </div>

        {portfolio?.positions && portfolio.positions.length > 0 && (
          <div className="mt-8">
            <h4 className="text-sm font-medium text-gray-500 mb-4">Current Positions</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Price</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market Value</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unrealized P/L</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {portfolio.positions.map((position, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {position.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {position.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(position.avg_price || 0)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCurrency(position.market_value || 0)}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm ${
                        (position.unrealized_pl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {formatCurrency(position.unrealized_pl || 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-4 text-xs text-gray-400">
          Last updated: {portfolio?.timestamp ? new Date(portfolio.timestamp).toLocaleString() : 'N/A'}
        </div>
      </div>
    </div>
  );
}