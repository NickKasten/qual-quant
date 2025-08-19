import Head from 'next/head';
import SignalsPanel from '../components/SignalsPanel';

export default function Signals() {
  return (
    <>
      <Head>
        <title>Trading Signals - QualQuant</title>
        <meta name="description" content="Current trading signals and technical indicators from the AI trading strategy" />
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Trading Signals</h1>
          <p className="mt-2 text-sm text-gray-600">
            Current signals and technical analysis from the AI trading strategy
          </p>
        </div>

        <SignalsPanel />
      </div>
    </>
  );
}