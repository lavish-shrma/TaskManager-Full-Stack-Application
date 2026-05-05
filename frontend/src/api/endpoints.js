import apiClient from './client';

export const authAPI = {
  signup: (data) =>
    apiClient.post('/auth/signup', data),
  login: (data) =>
    apiClient.post('/auth/login', data),
  me: () => apiClient.get('/auth/me'),
};

export const projectsAPI = {
  list: () => apiClient.get('/projects'),
  get: (id) => apiClient.get(`/projects/${id}`),
  create: (data) =>
    apiClient.post('/projects', data),
  update: (id, data) =>
    apiClient.patch(`/projects/${id}`, data),
  delete: (id) => apiClient.delete(`/projects/${id}`),
  addMember: (id, data) =>
    apiClient.post(`/projects/${id}/members`, data),
  removeMember: (projectId, userId) =>
    apiClient.delete(`/projects/${projectId}/members/${userId}`),
};

export const tasksAPI = {
  list: (projectId, params) =>
    apiClient.get(`/projects/${projectId}/tasks`, { params }),
  get: (projectId, taskId) =>
    apiClient.get(`/projects/${projectId}/tasks/${taskId}`),
  create: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/tasks`, data),
  update: (projectId, taskId, data) =>
    apiClient.patch(`/projects/${projectId}/tasks/${taskId}`, data),
  delete: (projectId, taskId) =>
    apiClient.delete(`/projects/${projectId}/tasks/${taskId}`),
};

export const dashboardAPI = {
  getStats: () => apiClient.get('/dashboard'),
};
