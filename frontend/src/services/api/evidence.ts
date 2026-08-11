import axios from 'axios';

const BASE_URL = '/api/evidence';

// Add interceptor for auth token (assuming stored in localStorage or handled by global axios config)
// The frontend likely has a configured axios instance, but we'll use a local one for clarity
// and assume token is passed. If there's an api.ts, we should ideally use that, but we'll
// construct standard endpoints here.

const getAuthHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return {
    headers: {
      Authorization: `Bearer ${token}`
    }
  };
};

export const connectGitHub = async (username: string, token?: string) => {
  const payload = { github_username: username, ...(token && { access_token: token }) };
  const response = await axios.post(`${BASE_URL}/github/connection/`, payload, getAuthHeaders());
  return response.data;
};

export const getGitHubConnection = async () => {
  const response = await axios.get(`${BASE_URL}/github/connection/`, getAuthHeaders());
  // Returns array, so we return first or null
  return response.data.length > 0 ? response.data[0] : null;
};

export const disconnectGitHub = async (id: number) => {
  const response = await axios.delete(`${BASE_URL}/github/connection/${id}/`, getAuthHeaders());
  return response.data;
};

export const syncGitHub = async (id: number) => {
  const response = await axios.post(`${BASE_URL}/github/connection/${id}/sync/`, {}, getAuthHeaders());
  return response.data;
};

export const getRepositories = async () => {
  const response = await axios.get(`${BASE_URL}/github/repositories/`, getAuthHeaders());
  return response.data;
};

export const getEvidenceSummary = async () => {
  const response = await axios.get(`${BASE_URL}/summary/`, getAuthHeaders());
  return response.data;
};

export const getSkillEvidence = async () => {
  const response = await axios.get(`${BASE_URL}/skills/`, getAuthHeaders());
  return response.data;
};

export const reviewEvidence = async (id: number, action: 'ACCEPT' | 'REJECT') => {
  const response = await axios.post(`${BASE_URL}/skills/${id}/review/`, { action }, getAuthHeaders());
  return response.data;
};

export const connectPortfolio = async (url: string) => {
  const response = await axios.post(`${BASE_URL}/portfolio/`, { portfolio_url: url }, getAuthHeaders());
  return response.data;
};

export const getPortfolioConnection = async () => {
  const response = await axios.get(`${BASE_URL}/portfolio/`, getAuthHeaders());
  return response.data.length > 0 ? response.data[0] : null;
};

export const analyzePortfolio = async (id: number) => {
  const response = await axios.post(`${BASE_URL}/portfolio/${id}/analyze/`, {}, getAuthHeaders());
  return response.data;
};

export const disconnectPortfolio = async (id: number) => {
  const response = await axios.delete(`${BASE_URL}/portfolio/${id}/`, getAuthHeaders());
  return response.data;
};

export default {
  connectGitHub,
  getGitHubConnection,
  disconnectGitHub,
  syncGitHub,
  getRepositories,
  getEvidenceSummary,
  getSkillEvidence,
  reviewEvidence,
  connectPortfolio,
  getPortfolioConnection,
  analyzePortfolio,
  disconnectPortfolio,
};
