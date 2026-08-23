const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL

export const apiBaseUrl = configuredBaseUrl ?? 'http://localhost:8000/api/v1'

interface SuccessEnvelope<T> {
  success: true
  data: T
  error: null
  meta: Record<string, unknown>
}

interface ErrorEnvelope {
  success: false
  data: null
  error: {
    code: string
    message: string
    details: Record<string, unknown>
  }
  meta: Record<string, unknown>
}

type AuthRecoveryHandler = () => Promise<boolean>

let accessToken: string | null = null
let authRecoveryHandler: AuthRecoveryHandler | null = null

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly details: Record<string, unknown> = {},
  ) {
    super(`API request failed with code ${code}.`)
    this.name = 'ApiError'
  }
}

export function setApiAccessToken(token: string | null): void {
  accessToken = token
}

export function setAuthRecoveryHandler(handler: AuthRecoveryHandler | null): void {
  authRecoveryHandler = handler
}

interface ApiRequestOptions {
  skipAuthRecovery?: boolean
}

async function executeRequest(path: string, init: RequestInit): Promise<Response> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (
    init.body !== undefined
    && !(init.body instanceof FormData)
    && !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }
  if (accessToken !== null) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  return fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: 'include',
    headers,
  })
}

async function decodeResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T
  }

  const body = (await response.json()) as SuccessEnvelope<T> | ErrorEnvelope
  if (!response.ok || !body.success) {
    const error = body.success ? undefined : body.error
    throw new ApiError(response.status, error?.code ?? 'INTERNAL_ERROR', error?.details)
  }

  return body.data
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: ApiRequestOptions = {},
): Promise<T> {
  let response = await executeRequest(path, init)

  if (
    response.status === 401 &&
    !options.skipAuthRecovery &&
    authRecoveryHandler !== null
  ) {
    const recovered = await authRecoveryHandler()
    if (recovered) {
      response = await executeRequest(path, init)
    }
  }

  return decodeResponse<T>(response)
}
