import { useEffect, useState, useCallback, useRef } from 'react'
import { Trash2, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'
import { useConsoleStore } from '@/store/useConsoleStore'
import { getConsoleSessions, getConsoleSessionDetail, deleteConsoleSession, cleanupExpiredSessions } from '@/api/console'
import type { ConsoleSessionDetail } from '@/types/console'

const Sessions = () => {
  const { t } = useI18n()
  const { sessions, setSessions } = useConsoleStore()
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'completed'>('all')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ConsoleSessionDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getConsoleSessions(50, 0, statusFilter)
      setSessions(data)
    } catch {
      // ignore
    }
  }, [statusFilter, setSessions])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchSessions, 30000)
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current)
      }
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [autoRefresh, fetchSessions])

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null)
      setDetail(null)
      return
    }
    setExpandedId(id)
    setLoadingDetail(true)
    try {
      const data = await getConsoleSessionDetail(id)
      setDetail(data)
    } catch {
      setDetail(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!window.confirm(t.console.sessions.confirmDelete)) return
    try {
      await deleteConsoleSession(id)
      setSessions(sessions.filter((s) => s.id !== id))
      if (expandedId === id) {
        setExpandedId(null)
        setDetail(null)
      }
    } catch {
      // ignore
    }
  }

  const handleCleanup = async () => {
    try {
      const result = await cleanupExpiredSessions()
      alert(`${t.console.sessions.cleanupDone}: ${result.deleted}`)
      fetchSessions()
    } catch {
      // ignore
    }
  }

  const filterTabs: { key: 'all' | 'active' | 'completed'; label: string }[] = [
    { key: 'all', label: t.console.sessions.all },
    { key: 'active', label: t.console.sessions.active },
    { key: 'completed', label: t.console.sessions.completed },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-2">
          {filterTabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                statusFilter === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              autoRefresh
                ? 'bg-green-600/20 text-green-400 border border-green-700'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {t.console.sessions.autoRefresh}
          </button>
          <button
            onClick={handleCleanup}
            className="px-3 py-2 bg-red-600/20 text-red-400 border border-red-800 rounded-lg text-sm hover:bg-red-600/30 transition-colors"
          >
            {t.console.sessions.cleanup}
          </button>
        </div>
      </div>

      {sessions.length === 0 ? (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-12 text-center">
          <p className="text-gray-500">{t.console.sessions.noSessions}</p>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.id}</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.problem}</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.steps}</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.status}</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.created}</th>
                <th className="text-left px-4 py-3 text-gray-400 text-sm font-medium">{t.console.sessions.lastActive}</th>
                <th className="text-right px-4 py-3 text-gray-400 text-sm font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <>
                  <tr
                    key={session.id}
                    className="border-b border-gray-700/50 hover:bg-gray-750 cursor-pointer transition-colors"
                    onClick={() => handleExpand(session.id)}
                  >
                    <td className="px-4 py-3 text-gray-300 text-sm font-mono">
                      <div className="flex items-center gap-2">
                        {expandedId === session.id ? (
                          <ChevronDown className="w-4 h-4 text-gray-500" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-500" />
                        )}
                        {session.id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="px-4 py-3 text-white text-sm max-w-[200px] truncate">{session.problem}</td>
                    <td className="px-4 py-3 text-gray-300 text-sm">{session.current_step}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                          session.is_completed
                            ? 'bg-green-900/30 text-green-400'
                            : 'bg-blue-900/30 text-blue-400'
                        }`}
                      >
                        {session.is_completed ? t.console.sessions.completed : t.console.sessions.active}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-sm">{new Date(session.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-400 text-sm">{new Date(session.last_active).toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(session.id)
                        }}
                        className="p-1.5 text-red-400 hover:bg-red-900/30 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                  {expandedId === session.id && (
                    <tr key={`${session.id}-detail`}>
                      <td colSpan={7} className="px-6 py-4 bg-gray-900/50">
                        {loadingDetail ? (
                          <p className="text-gray-500 text-sm">...</p>
                        ) : detail?.questions && detail.questions.length > 0 ? (
                          <table className="w-full">
                            <thead>
                              <tr className="border-b border-gray-700">
                                <th className="text-left px-3 py-2 text-gray-400 text-xs font-medium">{t.console.sessions.question}</th>
                                <th className="text-left px-3 py-2 text-gray-400 text-xs font-medium">{t.console.sessions.answer}</th>
                                <th className="text-left px-3 py-2 text-gray-400 text-xs font-medium">{t.console.sessions.feedback}</th>
                                <th className="text-left px-3 py-2 text-gray-400 text-xs font-medium">{t.console.sessions.status}</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detail.questions.map((q) => (
                                <tr key={q.id} className="border-b border-gray-800/50">
                                  <td className="px-3 py-2 text-gray-300 text-xs max-w-[200px] truncate">{q.question}</td>
                                  <td className="px-3 py-2 text-gray-300 text-xs max-w-[150px] truncate">{q.answer}</td>
                                  <td className="px-3 py-2 text-gray-300 text-xs max-w-[200px] truncate">{q.feedback}</td>
                                  <td className="px-3 py-2">
                                    <span
                                      className={`px-2 py-0.5 rounded-full text-xs ${
                                        q.is_correct
                                          ? 'bg-green-900/30 text-green-400'
                                          : 'bg-red-900/30 text-red-400'
                                      }`}
                                    >
                                      {q.is_correct ? t.console.sessions.correct : t.console.sessions.incorrect}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <p className="text-gray-500 text-sm">-</p>
                        )}
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Sessions
