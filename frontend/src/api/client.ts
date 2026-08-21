const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL

export const apiBaseUrl = configuredBaseUrl ?? 'http://localhost:8000/api/v1'

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}.`)
  }

  return (await response.json()) as T
}
