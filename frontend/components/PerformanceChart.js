import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ApiClient from '../utils/api';

export default function PerformanceChart() {
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState(30);

  useEffect(() => {
    fetchPerformance();
  }, [selectedPeriod]);

  const fetchPerformance = async () => {
    try {
      setLoading(true);
      const data = await ApiClient.getPerformance(selectedPeriod);
      setPerformance(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatChartData = (equityData) => {
    if (!equityData || equityData.length === 0) return [];
    
    return equityData.map(point => ({
      date: new Date(point.timestamp).toLocaleDateString(),
      equity: parseFloat(point.equity),
      timestamp: point.timestamp
    }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const periods = [
    { value: 7, label: '7D' },
    { value: 30, label: '30D' },
    { value: 90, label: '90D' },
    { value: 365, label: '1Y' }
  ];

  if (loading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
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
            <h3 className="text-lg leading-6 font-medium text-gray-900">Performance Chart</h3>
            <button 
              onClick={fetchPerformance}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Retry
            </button>
          </div>
          
          <div className="text-center py-12">
            <div className="flex justify-center mb-4">
              <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">Performance Data Unavailable</h4>
            <p className="text-gray-500 mb-4">Unable to load performance history</p>
            <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-md inline-block">
              {error}
            </div>
          </div>

          <div className="h-64 bg-gray-50 rounded flex items-center justify-center">
            <div className="text-gray-400 text-center">
              <svg className="w-16 h-16 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              <p className="text-sm">Chart unavailable</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const chartData = formatChartData(performance?.equity_curve || []);

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Performance Chart</h3>
          <div className="flex space-x-2">
            {periods.map(period => (
              <button
                key={period.value}
                onClick={() => setSelectedPeriod(period.value)}
                className={`px-3 py-1 text-sm rounded ${
                  selectedPeriod === period.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {period.label}
              </button>
            ))}
          </div>
        </div>

        {performance?.metrics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <dt className="text-sm font-medium text-gray-500">Initial Equity</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {formatCurrency(performance.metrics.initial_equity)}
              </dd>
            </div>
            <div className="text-center">
              <dt className="text-sm font-medium text-gray-500">Final Equity</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {formatCurrency(performance.metrics.final_equity)}
              </dd>
            </div>
            <div className="text-center">
              <dt className="text-sm font-medium text-gray-500">Total Return</dt>
              <dd className={`mt-1 text-lg font-semibold ${
                performance.metrics.total_return_percent >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {performance.metrics.total_return_percent >= 0 ? '+' : ''}
                {performance.metrics.total_return_percent.toFixed(2)}%
              </dd>
            </div>
            <div className="text-center">
              <dt className="text-sm font-medium text-gray-500">Period</dt>
              <dd className="mt-1 text-lg font-semibold text-gray-900">
                {performance.metrics.period_days} days
              </dd>
            </div>
          </div>
        )}

        <div className="h-64">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip 
                  formatter={(value) => [formatCurrency(value), 'Equity']}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="equity" 
                  stroke="#2563eb" 
                  strokeWidth={2}
                  name="Portfolio Equity"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              No performance data available for the selected period
            </div>
          )}
        </div>

        <div className="mt-4 text-xs text-gray-400">
          Data delayed {performance?.data_delay_minutes || 15} minutes
        </div>
      </div>
    </div>
  );
}