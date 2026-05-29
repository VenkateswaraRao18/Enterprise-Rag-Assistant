import type { AskResponse, Persona } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") || "";
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined;

function apiUrl(path: string) {
  return `${API_BASE}${path}`;
}

function apiHeaders(): HeadersInit {
  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  return headers;
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch(apiUrl("/api/personas"));
  if (!res.ok) throw new Error("Failed to load personas");
  return res.json();
}

export async function fetchExampleQueries(): Promise<string[]> {
  const res = await fetch(apiUrl("/api/example-queries"));
  if (!res.ok) return [];
  return res.json();
}

export async function askQuestion(payload: {
  query: string;
  team: string;
  role: string;
  clearance: string;
  top_k: number;
}): Promise<AskResponse> {
  const res = await fetch(apiUrl("/api/ask"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...apiHeaders(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(apiUrl("/health"));
    return res.ok;
  } catch {
    return false;
  }
}
