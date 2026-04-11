import axios from 'axios';

// Empty string = relative URLs → works behind Nginx proxy in production.
// For local dev, set VITE_API_URL=http://127.0.0.1:8000 in frontend/.env.local
const API_BASE = import.meta.env.VITE_API_URL ?? '';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // 5 min — agents can take a while
});

// ── Project ──────────────────────────────────────────────────────────
export const createProject = (idea, userId = null) =>
  api.post('/api/brand/project', { idea, user_id: userId });

export const getProject = (projectId) =>
  api.get(`/api/brand/project/${projectId}`);

export const listProjects = () =>
  api.get('/api/brand/projects');

// ── Workflow ─────────────────────────────────────────────────────────
export const runFullWorkflow = (projectId) =>
  api.post(`/api/brand/project/${projectId}/run`);

export const runNextStep = (projectId) =>
  api.post(`/api/brand/project/${projectId}/step`);

// ── Regenerate ───────────────────────────────────────────────────────
export const regenerate = (projectId, agentName, feedback) =>
  api.post('/api/regenerate/', { project_id: projectId, agent_name: agentName, feedback });

export const regenerateVariant = (projectId, variantIndex, colorPalette, headingFont, bodyFont) => {
  const body = { variant_index: variantIndex, color_palette: colorPalette };
  if (headingFont) body.heading_font = headingFont;
  if (bodyFont)    body.body_font    = bodyFont;
  return api.post(`/api/brand/project/${projectId}/variant-regenerate`, body);
};

// ── Export ────────────────────────────────────────────────────────────
export const getExport = (projectId) =>
  api.get(`/api/brand/project/${projectId}/export`);

export default api;
