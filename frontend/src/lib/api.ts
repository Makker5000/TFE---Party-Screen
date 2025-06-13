// Fonction wrapper pour fetch vers notre backend
export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers: Record<string,string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`/api${endpoint}`, { headers, ...options });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || JSON.stringify(err));
  }
  return res.json();
}

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';