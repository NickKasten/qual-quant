const BACKEND_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const API_KEY = process.env.API_KEY || '';

const ENDPOINT_MAP = {
  portfolio: '/api/portfolio',
  trades: '/api/trades',
  performance: '/api/performance',
  signals: '/api/signals',
  status: '/status'
};

export default async function handler(req, res) {
  const { endpoint } = req.query;
  const targetPath = ENDPOINT_MAP[endpoint];

  if (!targetPath) {
    return res.status(404).json({ error: 'Unsupported proxy endpoint' });
  }

  const baseUrl = BACKEND_BASE_URL.replace(/\/$/, '');
  const url = new URL(`${baseUrl}${targetPath}`);

  const forwardedQuery = { ...req.query };
  delete forwardedQuery.endpoint;

  Object.entries(forwardedQuery).forEach(([key, value]) => {
    if (Array.isArray(value)) {
      value.forEach((v) => url.searchParams.append(key, v));
    } else if (value !== undefined) {
      url.searchParams.append(key, value);
    }
  });

  const headers = {
    'Content-Type': 'application/json'
  };

  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  const init = {
    method: req.method,
    headers
  };

  if (req.method !== 'GET' && req.body) {
    init.body = JSON.stringify(req.body);
  }

  try {
    const response = await fetch(url, init);
    const contentType = response.headers.get('content-type') || '';
    const isJSON = contentType.includes('application/json');
    const payload = isJSON ? await response.json() : await response.text();

    if (!response.ok) {
      return res.status(response.status).send(payload);
    }

    if (isJSON) {
      return res.status(response.status).json(payload);
    }

    res.status(response.status).send(payload);
  } catch (error) {
    res.status(502).json({ error: 'Upstream request failed', detail: error.message });
  }
}
