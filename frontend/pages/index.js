import Head from 'next/head';
import PortfolioSummary from '../components/PortfolioSummary';
import PerformanceChart from '../components/PerformanceChart';

export default function Dashboard() {
  return (
    <>
      <Head>
        <title>Vibe Trading - AI Bot Dashboard</title>
        <meta name="description" content="Live AI trading bot dashboard showing portfolio performance, trades, and signals" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Trading Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600">
            Real-time view of your AI trading bot's performance and portfolio
          </p>
        </div>

        <div className="space-y-8">
          <PortfolioSummary />
          <PerformanceChart />
        </div>
      </div>
    </>
  );
}