const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";

export async function api<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  let token: string | null = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("access_token");
  }
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const get = <T = any>(path: string) => api<T>(path);
export const post = <T = any>(path: string, body: unknown) =>
  api<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
