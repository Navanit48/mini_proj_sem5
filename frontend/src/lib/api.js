import axios from 'axios';

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;
const localHosts = new Set(['localhost', '127.0.0.1', '::1']);
const pageIsRemote = !localHosts.has(window.location.hostname);
const configuredApiHost = configuredBaseUrl
  ? new URL(configuredBaseUrl, window.location.origin).hostname
  : null;
const API_BASE_URL = pageIsRemote && (!configuredApiHost || localHosts.has(configuredApiHost))
  ? '/api/v1'
  : configuredBaseUrl || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = window.__AIDFLOW_TOKEN__;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling 401s globally
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      window.dispatchEvent(new Event('aidflow:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default api;
