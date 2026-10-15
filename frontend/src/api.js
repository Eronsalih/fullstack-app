// Relative by default: nginx (Docker) and the Vite dev server both proxy /api to the backend.
const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.status === 204 ? null : res.json();
}

export const api = {
  health: () => request("/health"),
  list: () => request("/tasks"),
  create: (title) => request("/tasks", { method: "POST", body: JSON.stringify({ title }) }),
  toggle: (id, done) => request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify({ done }) }),
  remove: (id) => request(`/tasks/${id}`, { method: "DELETE" }),
};
