import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="description" content="AI Trading Bot Dashboard - Monitor your automated trading performance" />
        <meta name="theme-color" content="#1f2937" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}