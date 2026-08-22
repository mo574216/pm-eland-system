import {
  apiRequest,
  setApiAccessToken,
  setAuthRecoveryHandler,
} from './client'

function jsonResponse(body: object, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiRequest', () => {
  afterEach(() => {
    setApiAccessToken(null)
    setAuthRecoveryHandler(null)
    vi.unstubAllGlobals()
  })

  it('attaches the in-memory bearer token and includes refresh cookies', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({ success: true, data: { id: 'user-1' }, error: null, meta: {} }),
    )
    vi.stubGlobal('fetch', fetchMock)
    setApiAccessToken('access-token')

    await expect(apiRequest<{ id: string }>('/auth/me')).resolves.toEqual({ id: 'user-1' })

    const init = fetchMock.mock.calls[0]?.[1] as RequestInit
    expect(init.credentials).toBe('include')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer access-token')
  })

  it('exposes stable error codes without exposing the public message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            success: false,
            data: null,
            error: { code: 'AUTH_INVALID_CREDENTIALS', message: 'safe', details: {} },
            meta: {},
          },
          401,
        ),
      ),
    )

    await expect(
      apiRequest('/auth/login', {}, { skipAuthRecovery: true }),
    ).rejects.toMatchObject({ status: 401, code: 'AUTH_INVALID_CREDENTIALS' })
  })

  it('recovers once from a global 401 and retries with the rotated access token', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            data: null,
            error: { code: 'AUTH_TOKEN_EXPIRED', message: 'expired', details: {} },
            meta: {},
          },
          401,
        ),
      )
      .mockResolvedValueOnce(
        jsonResponse({ success: true, data: { value: 42 }, error: null, meta: {} }),
      )
    vi.stubGlobal('fetch', fetchMock)
    setApiAccessToken('expired-token')
    setAuthRecoveryHandler(() => {
      setApiAccessToken('rotated-token')
      return Promise.resolve(true)
    })

    await expect(apiRequest<{ value: number }>('/protected')).resolves.toEqual({ value: 42 })
    const retriedInit = fetchMock.mock.calls[1]?.[1] as RequestInit
    expect(new Headers(retriedInit.headers).get('Authorization')).toBe('Bearer rotated-token')
  })
})
