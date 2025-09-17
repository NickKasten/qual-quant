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
    const equity = portfolio?.current_equity || 0;
    if (!equity) {
      return '0.00%';
    }
    const percent = (value / equity) * 100;
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
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Portfolio Summary</h3>
            <button
              onClick={fetchPortfolio}
              className="text-sm text-primary-600 hover:text-primary-800"
            >
              Retry
            </button>
          </div>

          <p className="text-sm text-gray-600">
            We couldn’t retrieve the latest portfolio snapshot. Confirm the trading API is reachable and that the
            frontend has a valid API key configured.
          </p>
          <p className="mt-3 text-xs text-red-600 bg-red-50 rounded px-3 py-2 font-mono break-all">
            {error}
          </p>
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
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
                        {formatCurrency(position.current_price || 0)}
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
