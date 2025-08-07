import axios from 'axios';

// Base API configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// PUBLIC_INTERFACE
export const authAPI = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  }
};

// PUBLIC_INTERFACE
export const documentsAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getAll: async () => {
    const response = await api.get('/documents');
    return response.data;
  },
  
  getById: async (id) => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },
  
  delete: async (id) => {
    const response = await api.delete(`/documents/${id}`);
    return response.data;
  }
};

// PUBLIC_INTERFACE
export const chatAPI = {
  sendMessage: async (message, sessionId = null, documentIds = [], useContext = true) => {
    const response = await api.post('/chat', {
      message,
      session_id: sessionId,
      document_ids: documentIds,
      use_context: useContext
    });
    return response.data;
  },
  
  getSessions: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },
  
  getSession: async (id) => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
  },
  
  deleteSession: async (id) => {
    const response = await api.delete(`/sessions/${id}`);
    return response.data;
  },
  
  exportSession: async (id, format = 'json') => {
    const response = await api.get(`/sessions/${id}/export?format=${format}`, {
      responseType: 'blob'
    });
    return response.data;
  }
};

// PUBLIC_INTERFACE
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

export default api;
