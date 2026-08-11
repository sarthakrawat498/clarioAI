import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8001/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// Request interceptor to attach Authorization token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});


export const authAPI = {
  register: async (full_name, email, password) => {
    const response = await apiClient.post('/auth/register', { full_name, email, password });
    return response.data;
  },
  login: async (email, password) => {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

export const profileAPI = {
  getProfile: async () => {
    const response = await apiClient.get('/profile');
    return response.data;
  },
  updateProfile: async (profileData) => {
    const response = await apiClient.put('/profile', profileData);
    return response.data;
  },
};

export const chatAPI = {
  sendQuery: async (message, session_id = null) => {
    const payload = { message };
    if (session_id) payload.session_id = session_id;
    const response = await apiClient.post('/chat/query', payload);
    return response.data;
  },
  getSessions: async () => {
    const response = await apiClient.get('/chat/sessions');
    return response.data;
  },
  deleteSession: async (sessionId) => {
    const response = await apiClient.delete(`/chat/sessions/${sessionId}`);
    return response.data;
  },
  clearAllSessions: async () => {
    const response = await apiClient.delete('/chat/sessions');
    return response.data;
  },
};


export const policyAPI = {
  getPolicies: async () => {
    const response = await apiClient.get('/policies');
    return response.data;
  },
  comparePolicies: async (policy_id_1, policy_id_2) => {
    const response = await apiClient.get('/compare', { params: { policy_id_1, policy_id_2 } });
    return response.data;
  },
  getRecommendations: async () => {
    const response = await apiClient.get('/recommendations');
    return response.data;
  },
};

export const claimAPI = {
  checkEligibility: async (claimPayload) => {
    const response = await apiClient.post('/claims/check-eligibility', claimPayload);
    return response.data;
  },
};

export const premiumAPI = {
  estimatePremium: async (premiumPayload) => {
    const response = await apiClient.post('/premium/estimate', premiumPayload);
    return response.data;
  },
};

export const faqAPI = {
  getFaqs: async () => {
    const response = await apiClient.get('/faqs');
    return response.data;
  },
};

export default apiClient;
