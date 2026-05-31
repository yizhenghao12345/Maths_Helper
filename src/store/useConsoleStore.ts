import { create } from 'zustand'
import type { ConsoleSession, AILog, ConsoleStats, ConsoleHealth } from '@/types/console'

interface ConsoleState {
  isAuthenticated: boolean
  health: ConsoleHealth | null
  sessions: ConsoleSession[]
  currentSession: ConsoleSession | null
  aiLogs: AILog[]
  stats: ConsoleStats | null
  isLoading: boolean
  error: string | null

  setAuthenticated: (auth: boolean) => void
  setHealth: (health: ConsoleHealth) => void
  setSessions: (sessions: ConsoleSession[]) => void
  setCurrentSession: (session: ConsoleSession | null) => void
  setAILogs: (logs: AILog[]) => void
  setStats: (stats: ConsoleStats) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useConsoleStore = create<ConsoleState>((set) => ({
  isAuthenticated: !!localStorage.getItem('console_token'),
  health: null,
  sessions: [],
  currentSession: null,
  aiLogs: [],
  stats: null,
  isLoading: false,
  error: null,

  setAuthenticated: (auth) => set({ isAuthenticated: auth }),
  setHealth: (health) => set({ health }),
  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (session) => set({ currentSession: session }),
  setAILogs: (logs) => set({ aiLogs: logs }),
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  reset: () => set({
    isAuthenticated: !!localStorage.getItem('console_token'),
    health: null,
    sessions: [],
    currentSession: null,
    aiLogs: [],
    stats: null,
    isLoading: false,
    error: null,
  }),
}))
