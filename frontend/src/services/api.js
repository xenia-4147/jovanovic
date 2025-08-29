import axios from 'axios';

// Use relative URLs if no backend URL is configured (production environment)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
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

// Handle auth errors - Let AuthContext handle redirects instead of automatic redirects
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear tokens but don't auto-redirect - let AuthContext handle it
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      
      // Dispatch custom event to notify AuthContext
      window.dispatchEvent(new CustomEvent('auth-expired'));
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await api.put('/auth/profile', profileData);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }
};

// Business Cards API
export const cardsApi = {
  create: async (cardData) => {
    const response = await api.post('/cards', cardData);
    return response.data;
  },

  getAll: async () => {
    const response = await api.get('/cards');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/cards/${id}`);
    return response.data;
  },

  update: async (id, cardData) => {
    const response = await api.put(`/cards/${id}`, cardData);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/cards/${id}`);
    return response.data;
  },

  generateQR: (id) => {
    return `${API_BASE}/cards/${id}/qr`;
  },

  downloadVCard: (id) => {
    return `${API_BASE}/cards/${id}/vcard`;
  }
};

// Privacy & GDPR API
export const privacyApi = {
  getReport: async () => {
    const response = await api.get('/privacy/report');
    return response.data;
  },

  exportData: async () => {
    const response = await api.get('/privacy/export');
    return response.data;
  },

  deleteAccount: async (deletionData) => {
    const response = await api.delete('/privacy/delete', { data: deletionData });
    return response.data;
  }
};

// Utility functions
export const generateVCard = (cardData) => {
  let vcard = `BEGIN:VCARD
VERSION:3.0
FN:${cardData.name}`;

  if (cardData.company) {
    vcard += `\nORG:${cardData.company}`;
  }
  if (cardData.position) {
    vcard += `\nTITLE:${cardData.position}`;
  }

  // Add phone numbers
  if (cardData.phones) {
    cardData.phones.forEach(phone => {
      if (phone.number) {
        vcard += `\nTEL;TYPE=${phone.label}:${phone.number}`;
      }
    });
  }

  // Add email addresses
  if (cardData.emails) {
    cardData.emails.forEach(email => {
      if (email.address) {
        vcard += `\nEMAIL;TYPE=${email.label}:${email.address}`;
      }
    });
  }

  if (cardData.website) {
    vcard += `\nURL:${cardData.website}`;
  }

  if (cardData.description) {
    vcard += `\nNOTE:${cardData.description}`;
  }

  vcard += '\nEND:VCARD';
  return vcard;
};

export const downloadVCardFile = (cardData) => {
  const vcard = generateVCard(cardData);
  const blob = new Blob([vcard], { type: 'text/vcard' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${cardData.name.replace(/\s+/g, '_')}.vcf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export default api;