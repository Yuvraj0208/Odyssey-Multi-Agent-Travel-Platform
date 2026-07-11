// Client-side auth state (JWT in localStorage). Optional: the app works signed-out
// (demo), but signing in scopes trips + preferences to a real account.

export interface AuthUser {
  id: string;
  email: string;
  name?: string | null;
}

const TOKEN_KEY = "odyssey-token";
const USER_KEY = "odyssey-authuser";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: AuthUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
