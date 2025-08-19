import '../styles/globals.css'
import DisclaimerBanner from '../components/DisclaimerBanner'

export default function App({ Component, pageProps }) {
  return (
    <>
      <DisclaimerBanner />
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <h1 className="text-3xl font-bold text-primary-900">QualQuant</h1>
                <span className="ml-3 text-sm text-primary-600 bg-primary-100 px-2 py-1 rounded">AI Bot Dashboard</span>
              </div>
              <nav className="flex space-x-8">
                <a href="/" className="text-primary-600 hover:text-primary-900">Dashboard</a>
                <a href="/trades" className="text-primary-600 hover:text-primary-900">Trades</a>
                <a href="/signals" className="text-primary-600 hover:text-primary-900">Signals</a>
                <a href="/about" className="text-primary-600 hover:text-primary-900">About</a>
              </nav>
            </div>
          </div>
        </header>
        <main>
          <Component {...pageProps} />
        </main>
      </div>
    </>
  )
}