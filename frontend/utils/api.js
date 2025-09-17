const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL.replace(/\/$/, '');
  }

  async request(endpoint, options = {}) {
    const base = this.baseURL || '';
    const url = `${base}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`API endpoint not found: ${endpoint}`);
        }
        if (response.status === 401) {
          throw new Error('Authentication failed - check API key in environment variables');
        }
        if (response.status === 403) {
          throw new Error('Access forbidden - invalid API key or insufficient permissions');
        }
        if (response.status >= 500) {
          throw new Error('Backend server error - please try again later');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Cannot connect to backend - check if API server is running');
      }
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getPortfolio() {
    return this.request('/api/proxy/portfolio');
  }

  async getTrades(page = 1, pageSize = 20, symbol = null) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString()
    });
    
    if (symbol) {
      params.append('symbol', symbol);
    }
    
    return this.request(`/api/proxy/trades?${params}`);
  }

  async getPerformance(days = 30) {
    return this.request(`/api/proxy/performance?days=${days}`);
  }

  async getSignals() {
    return this.request('/api/proxy/signals');
  }

  async getStatus() {
    return this.request('/api/proxy/status');
  }
}

export default new ApiClient();
