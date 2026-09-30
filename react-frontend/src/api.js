import axios from "axios";

// Get API base URL from environment or default to localhost
const getApiBaseUrl = () => {
  // Support Vite environment variables
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Support standard fetch-style environment variables
  if (typeof window !== 'undefined' && window.__API_BASE_URL__) {
    return window.__API_BASE_URL__;
  }
  // Default for local development
  return "http://127.0.0.1:8001/api/v1";
};

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000,
});

// Request interceptor to attach Authorization token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor to handle 401 Unauthorized responses
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized
    if (error.response && error.response.status === 401) {
      // Clear auth state on 401
      localStorage.removeItem("token");
      localStorage.removeItem("needs_profile_onboarding");
      // Dispatch custom event to notify AuthContext
      window.dispatchEvent(new Event("auth-401-error"));
      // Optionally redirect to login, but let the app handle it via context
      console.warn("Unauthorized: token cleared", error.response?.data?.detail);
    } else if (!error.response) {
      // Network error or no response
      console.error("Network error - Backend may not be running at:", getApiBaseUrl());
      console.error("Error details:", error.message);
    }
    return Promise.reject(error);
  },
);

export const authAPI = {
  register: async (full_name, email, password) => {
    const response = await apiClient.post("/auth/register", {
      full_name,
      email,
      password,
    });
    return response.data;
  },
  login: async (email, password) => {
    const response = await apiClient.post("/auth/login", { email, password });
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },
};

export const profileAPI = {
  getProfile: async () => {
    const response = await apiClient.get("/profile");
    return response.data;
  },
  updateProfile: async (profileData) => {
    const response = await apiClient.put("/profile", profileData);
    return response.data;
  },
};

export const chatAPI = {
  sendQuery: async (message, session_id = null, options = {}) => {
    const payload = { message };
    if (session_id) payload.session_id = session_id;
    if (options.filter_company) payload.filter_company = options.filter_company;
    if (options.filter_policy) payload.filter_policy = options.filter_policy;
    if (options.claim_amount !== undefined && options.claim_amount !== null)
      payload.claim_amount = options.claim_amount;
    if (
      Array.isArray(options.compare_policy_ids) &&
      options.compare_policy_ids.length
    )
      payload.compare_policy_ids = options.compare_policy_ids;
    if (options.profile_session_id)
      payload.profile_session_id = options.profile_session_id;
    const response = await apiClient.post("/chat/query", payload);
    return response.data;
  },
  getSessions: async () => {
    const response = await apiClient.get("/chat/sessions");
    return response.data;
  },
  deleteSession: async (sessionId) => {
    const response = await apiClient.delete(`/chat/sessions/${sessionId}`);
    return response.data;
  },
  clearAllSessions: async () => {
    const response = await apiClient.delete("/chat/sessions");
    return response.data;
  },
  updateSessionTitle: async (sessionId, session_title) => {
    const response = await apiClient.put(`/chat/sessions/${sessionId}`, {
      session_title,
    });
    return response.data;
  },
};

export const uploadAPI = {
  uploadPolicyDocument: async (file, sessionId = null) => {
    const formData = new FormData();
    formData.append("file", file);
    if (sessionId !== null && sessionId !== undefined) {
      formData.append("session_id", String(sessionId));
    }
    const response = await apiClient.post(
      "/documents/upload-policy",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      },
    );
    return response.data;
  },
};

export const policyAPI = {
  getPolicies: async (budget_annual_max = null) => {
    const response = await apiClient.get("/policies", {
      params:
        budget_annual_max !== null &&
        budget_annual_max !== undefined &&
        budget_annual_max !== ""
          ? { budget_annual_max }
          : {},
    });
    return response.data;
  },
  comparePolicies: async (policy_id_1, policy_id_2) => {
    const response = await apiClient.post("/compare", {
      policy_ids: [policy_id_1, policy_id_2],
    });
    return response.data;
  },
  getRecommendations: async () => {
    const response = await apiClient.get("/recommendations");
    return response.data;
  },
};

export const claimAPI = {
  checkEligibility: async (claimPayload) => {
    const response = await apiClient.post(
      "/claims/check-eligibility",
      claimPayload,
    );
    return response.data;
  },
};

export const premiumAPI = {
  estimatePremium: async (premiumPayload) => {
    const response = await apiClient.post("/premium/estimate", premiumPayload);
    return response.data;
  },
};

export const faqAPI = {
  getFaqs: async () => {
    const response = await apiClient.get("/faqs");
    return response.data;
  },
};

export default apiClient;
