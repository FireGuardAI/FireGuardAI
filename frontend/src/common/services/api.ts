import { env } from '../config/env'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function configuredBaseUrlOrThrow(): string {
  if (!env.apiBaseUrl) {
    // Without this guard, a missing VITE_API_BASE_URL turns into a relative
    // fetch that (behind the frontend's own nginx container) comes back as a
    // baffling "405 Not Allowed" HTML page instead of a clear error.
    throw new ApiError(
      0,
      'This app is not configured with a backend API URL (VITE_API_BASE_URL). ' +
        'Set it in fireguard-frontend/.env and rebuild the app.',
    )
  }
  return env.apiBaseUrl
}

async function extractErrorDetail(response: Response): Promise<string> {
  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('application/json')) {
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') return body.detail
      if (Array.isArray(body?.detail)) {
        return body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(', ') || response.statusText
      }
    } catch {
      // fall through to status text below
    }
  } else if (!contentType.includes('text/html')) {
    try {
      const text = await response.text()
      if (text) return text
    } catch {
      // ignore
    }
  }
  // Anything else (including an HTML error page from a reverse proxy) isn't
  // fit to show a user directly — surface the HTTP status instead.
  return response.statusText || `Request failed with status ${response.status}`
}

interface ApiRequestOptions extends RequestInit {
  token?: string
}

export async function apiRequest<T>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
  const baseUrl = configuredBaseUrlOrThrow()
  const { token, headers, body, ...rest } = options
  const isFormBody = body instanceof FormData
  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...rest,
    body,
    headers: {
      ...(isFormBody ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorDetail(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

/** application/x-www-form-urlencoded POST — used for OAuth2PasswordRequestForm login. */
export async function apiFormRequest<T>(endpoint: string, fields: Record<string, string>): Promise<T> {
  const baseUrl = configuredBaseUrlOrThrow()
  const response = await fetch(`${baseUrl}${endpoint}`, {
    method: 'POST',
    body: new URLSearchParams(fields),
  })
  if (!response.ok) {
    throw new ApiError(response.status, await extractErrorDetail(response))
  }
  return (await response.json()) as T
}
