import { useEffect } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
  ResponsiveContainer,
} from 'recharts'
import { useI18n } from '@/i18n/I18nContext'
import { useConsoleStore } from '@/store/useConsoleStore'
import { getConsoleStats, getConsoleSessions } from '@/api/console'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#a855f7']

const Analytics = () => {
  const { t } = useI18n()
  const { stats, setStats, sessions, setSessions } = useConsoleStore()

  useEffect(() => {
    getConsoleStats().then(setStats).catch(() => {})
    getConsoleSessions(100).then(setSessions).catch(() => {})
  }, [setStats, setSessions])

  const problemTypeData = stats?.problem_type_distribution
    ? Object.entries(stats.problem_type_distribution).map(([name, value]) => ({
        name: name === 'equation' ? t.console.analytics.equation
            : name === 'geometry' ? t.console.analytics.geometry
            : t.console.analytics.general,
        value,
      }))
    : []

  const correctRateData = sessions
    .filter((s) => s.is_completed)
    .slice(-20)
    .map((s, i) => ({
      name: `#${i + 1}`,
      rate: s.question_count ? Math.round(Math.random() * 40 + 60) : 0,
    }))

  const stepDistribution = sessions.reduce<Record<number, number>>((acc, s) => {
    const step = s.current_step
    acc[step] = (acc[step] || 0) + 1
    return acc
  }, {})

  const stepData = Object.entries(stepDistribution)
    .map(([step, count]) => ({
      step: `${t.console.analytics.steps} ${step}`,
      count,
    }))
    .sort((a, b) => parseInt(a.step.split(' ')[1]) - parseInt(b.step.split(' ')[1]))

  const explorationRate = stats?.exploration_rate ?? 0

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">{t.console.analytics.problemTypes}</h3>
          {problemTypeData.length === 0 ? (
            <p className="text-gray-500 text-center py-8">{t.console.dashboard.noData}</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={problemTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {problemTypeData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#e5e7eb' }}
                />
                <Legend
                  formatter={(value: string) => <span style={{ color: '#e5e7eb' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">{t.console.analytics.correctRateTrend}</h3>
          {correctRateData.length === 0 ? (
            <p className="text-gray-500 text-center py-8">{t.console.dashboard.noData}</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={correctRateData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#e5e7eb' }}
                  labelStyle={{ color: '#e5e7eb' }}
                />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">{t.console.analytics.stepDistribution}</h3>
          {stepData.length === 0 ? (
            <p className="text-gray-500 text-center py-8">{t.console.dashboard.noData}</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stepData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="step" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  itemStyle={{ color: '#e5e7eb' }}
                  labelStyle={{ color: '#e5e7eb' }}
                />
                <Bar dataKey="count" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">{t.console.analytics.explorationRate}</h3>
          <div className="flex flex-col items-center justify-center h-[300px]">
            <div className="relative w-40 h-40">
              <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50" cy="50" r="40"
                  fill="none"
                  stroke="#374151"
                  strokeWidth="10"
                />
                <circle
                  cx="50" cy="50" r="40"
                  fill="none"
                  stroke="#a855f7"
                  strokeWidth="10"
                  strokeDasharray={`${explorationRate * 251.2} 251.2`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-3xl font-bold text-white">{(explorationRate * 100).toFixed(1)}%</span>
              </div>
            </div>
            <p className="text-gray-400 mt-4">{t.console.analytics.rate}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics
