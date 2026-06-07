import { useEffect } from 'react'
import { Activity, Users, HelpCircle, CheckCircle } from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'
import { useConsoleStore } from '@/store/useConsoleStore'
import { getConsoleHealth, getConsoleStats, getConsoleSessions } from '@/api/console'
import { formatShanghaiTime } from '@/lib/utils'

const Dashboard = () => {
  const { t } = useI18n()
  const { health, stats, sessions, setHealth, setStats, setSessions } = useConsoleStore()

  useEffect(() => {
    getConsoleHealth().then(setHealth).catch(() => {})
    getConsoleStats().then(setStats).catch(() => {})
    getConsoleSessions(5).then(setSessions).catch(() => {})
  }, [setHealth, setStats, setSessions])

  const statusCards = [
    {
      icon: Activity,
      title: t.console.dashboard.serviceStatus,
      value: health?.ai_enabled ? t.console.dashboard.aiEnabled : t.console.dashboard.aiDisabled,
      subtitle: `${t.console.dashboard.provider}: ${health?.ai_provider || '-'} | ${t.console.dashboard.model}: ${health?.ai_model || '-'}`,
      gradient: 'from-blue-500 to-blue-700',
      indicator: health?.ai_enabled ? 'bg-green-400' : 'bg-red-400',
    },
    {
      icon: Users,
      title: t.console.dashboard.activeSessions,
      value: health?.session_count ?? 0,
      subtitle: t.console.dashboard.activeSessions,
      gradient: 'from-green-500 to-green-700',
      indicator: null,
    },
    {
      icon: HelpCircle,
      title: t.console.dashboard.totalQuestions,
      value: stats?.total_questions ?? 0,
      subtitle: t.console.dashboard.totalQuestions,
      gradient: 'from-purple-500 to-purple-700',
      indicator: null,
    },
    {
      icon: CheckCircle,
      title: t.console.dashboard.correctRate,
      value: stats ? `${stats.correct_rate.toFixed(1)}%` : '0%',
      subtitle: t.console.dashboard.correctRate,
      gradient: 'from-amber-500 to-amber-700',
      indicator: null,
      progress: (stats?.correct_rate ?? 0) / 100,
    },
  ]

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statusCards.map((card, index) => {
          const IconComponent = card.icon
          return (
            <div
              key={index}
              className="bg-gray-800 rounded-xl p-6 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${card.gradient} flex items-center justify-center`}>
                  <IconComponent className="w-6 h-6 text-white" />
                </div>
                {card.indicator && (
                  <div className={`w-3 h-3 rounded-full ${card.indicator}`} />
                )}
              </div>
              <p className="text-gray-400 text-sm mb-1">{card.title}</p>
              <p className="text-2xl font-bold text-white">{card.value}</p>
              <p className="text-gray-500 text-xs mt-2 truncate">{card.subtitle}</p>
              {card.progress !== undefined && card.progress > 0 && (
                <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-amber-500 h-2 rounded-full transition-all"
                    style={{ width: `${card.progress * 100}%` }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">{t.console.dashboard.recentActivity}</h2>
        {sessions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">{t.console.dashboard.noData}</p>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="flex items-center justify-between bg-gray-750 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex-1 min-w-0 mr-4">
                  <p className="text-white truncate">{session.problem}</p>
                  <p className="text-gray-500 text-sm mt-1">
                    {formatShanghaiTime(session.created_at)}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    session.is_completed
                      ? 'bg-green-900/30 text-green-400 border border-green-800'
                      : 'bg-blue-900/30 text-blue-400 border border-blue-800'
                  }`}
                >
                  {session.is_completed ? t.console.sessions.completed : t.console.sessions.active}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
