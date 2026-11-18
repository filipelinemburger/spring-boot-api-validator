import { clearSession, getToken } from '../auth/session'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}`, ...init.headers },
  })
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    // Token missing or expired: drop the session and send the user to the login page.
    clearSession()
    window.location.assign('/login')
    throw new Error('Session expired')
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.message ?? `Request failed (${res.status})`)
  }
  return res.status === 204 ? (undefined as T) : res.json()
}
