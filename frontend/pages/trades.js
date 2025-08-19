import Head from 'next/head';
import TradeFeed from '../components/TradeFeed';

export default function Trades() {
  return (
    <>
      <Head>
        <title>Trade History - QualQuant</title>
        <meta name="description" content="Complete trading history and transaction log from the AI trading bot" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Trade History</h1>
          <p className="mt-2 text-sm text-gray-600">
            Complete log of all trades executed by the AI bot
          </p>
        </div>

        <TradeFeed />
      </div>
    </>
  );
}