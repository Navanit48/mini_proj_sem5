import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Create an Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    // We store the access token in memory/state via AuthContext, 
    // but for simplicity in non-component context, we could fall back to localStorage.
    // However, best practice is to inject it, so we'll grab it from window if set.
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
    // If we get a 401, we could dispatch a global event to trigger logout/refresh
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized request, token might be expired.");
      // Trigger custom event that AuthContext can listen to
      window.dispatchEvent(new Event('aidflow:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default api;
