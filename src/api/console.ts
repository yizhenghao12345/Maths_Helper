import type { ConsoleSession, ConsoleSessionDetail, AILog, ConsoleStats, ConsoleHealth, AIConfigUpdate, ProviderPresets, ConnectionTestResult, AIFullConfig } from '@/types/console'

const CONSOLE_BASE = '/api/console'

async function consoleFetch(path: string, options?: RequestInit): Promise<Response> {
  const token = localStorage.getItem('console_token')
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  if (!headers['Content-Type'] && options?.body) {
    headers['Content-Type'] = 'application/json'
  }
  const response = await fetch(`${CONSOLE_BASE}${path}`, { ...options, headers })
  if (response.status === 401) {
    localStorage.removeItem('console_token')
    throw new Error('UNAUTHORIZED')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail || 'Request failed')
  }
  return response
}

export async function loginConsole(password: string): Promise<{ token: string }> {
  const response = await fetch(`${CONSOLE_BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  })
  if (!response.ok) {
    throw new Error('Invalid password')
  }
  return response.json()
}

export async function logoutConsole(): Promise<void> {
  await consoleFetch('/logout', { method: 'POST' })
  localStorage.removeItem('console_token')
}

export async function getConsoleHealth(): Promise<ConsoleHealth> {
  const response = await consoleFetch('/health')
  return response.json()
}

export async function getConsoleSessions(limit = 20, offset = 0, status = 'all'): Promise<ConsoleSession[]> {
  const response = await consoleFetch(`/sessions?limit=${limit}&offset=${offset}&status=${status}`)
  const data = await response.json()
  return data.sessions || data
}

export async function getConsoleSessionDetail(id: string): Promise<ConsoleSessionDetail> {
  const response = await consoleFetch(`/sessions/${id}`)
  const data = await response.json()
  return { ...data.session, questions: data.question_history || [] }
}

export async function deleteConsoleSession(id: string): Promise<void> {
  await consoleFetch(`/sessions/${id}`, { method: 'DELETE' })
}

export async function cleanupExpiredSessions(): Promise<{ deleted: number }> {
  const response = await consoleFetch('/sessions', { method: 'DELETE' })
  const data = await response.json()
  const match = (data.message || '').match(/(\d+)/)
  return { deleted: match ? parseInt(match[1]) : 0 }
}

export async function getConsoleStats(): Promise<ConsoleStats> {
  const response = await consoleFetch('/stats')
  return response.json()
}

export async function getAILogs(limit = 50, offset = 0): Promise<AILog[]> {
  const response = await consoleFetch(`/ai-logs?limit=${limit}&offset=${offset}`)
  const data = await response.json()
  return data.logs || data
}

export async function updateAIConfig(config: AIConfigUpdate): Promise<{ success: boolean }> {
  const response = await consoleFetch('/ai-config', {
    method: 'PATCH',
    body: JSON.stringify(config),
  })
  const data = await response.json()
  return { success: !!data.provider }
}

export async function getProviderPresets(): Promise<ProviderPresets> {
  const response = await consoleFetch('/providers')
  return response.json()
}

export async function testConnection(params: { provider: string; api_key?: string; base_url: string; model: string; target?: 'ai' | 'ocr' }): Promise<ConnectionTestResult> {
  const response = await consoleFetch('/test-connection', {
    method: 'POST',
    body: JSON.stringify(params),
  })
  return response.json()
}

export async function getAIConfig(): Promise<AIFullConfig> {
  const response = await consoleFetch('/ai-config')
  return response.json()
}
