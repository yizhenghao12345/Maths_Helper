import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LayoutDashboard, Monitor, Bot, BarChart3, Settings, LogOut, Home, Brain } from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'
import { useConsoleStore } from '@/store/useConsoleStore'
import { CONSOLE_AUTH_EXPIRED_EVENT, logoutConsole } from '@/api/console'
import ConsoleLogin from '@/components/console/ConsoleLogin'
import Dashboard from '@/components/console/Dashboard'
import Sessions from '@/components/console/Sessions'
import AIDebug from '@/components/console/AIDebug'
import Analytics from '@/components/console/Analytics'
import SettingsPage from '@/components/console/Settings'

const tabs = [
  { key: 'dashboard', icon: LayoutDashboard },
  { key: 'sessions', icon: Monitor },
  { key: 'aiDebug', icon: Bot },
  { key: 'analytics', icon: BarChart3 },
  { key: 'settings', icon: Settings },
] as const

type TabKey = (typeof tabs)[number]['key']

const Console = () => {
  const navigate = useNavigate()
  const { t } = useI18n()
  const { isAuthenticated, setAuthenticated, reset } = useConsoleStore()
  const [activeTab, setActiveTab] = useState<TabKey>('dashboard')

  useEffect(() => {
    const resetAuth = () => {
      setAuthenticated(false)
      reset()
    }
    const handleUnauthorized = (e: StorageEvent) => {
      if (e.key === 'console_token' && !e.newValue) {
        resetAuth()
      }
    }
    window.addEventListener(CONSOLE_AUTH_EXPIRED_EVENT, resetAuth)
    window.addEventListener('storage', handleUnauthorized)
    return () => {
      window.removeEventListener(CONSOLE_AUTH_EXPIRED_EVENT, resetAuth)
      window.removeEventListener('storage', handleUnauthorized)
    }
  }, [setAuthenticated, reset])

  if (!isAuthenticated) {
    return <ConsoleLogin />
  }

  const handleLogout = async () => {
    try {
      await logoutConsole()
    } catch {
      // ignore
    }
    localStorage.removeItem('console_token')
    setAuthenticated(false)
    reset()
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return <Dashboard />
      case 'sessions': return <Sessions />
      case 'aiDebug': return <AIDebug />
      case 'analytics': return <Analytics />
      case 'settings': return <SettingsPage />
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-blue-400" />
            <span className="text-lg font-bold text-white">{t.console.title}</span>
          </div>
          <div className="h-6 w-px bg-gray-700" />
          <nav className="flex gap-1">
            {tabs.map((tab) => {
              const IconComponent = tab.icon
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  <IconComponent className="w-4 h-4" />
                  {t.console.tabs[tab.key as keyof typeof t.console.tabs]}
                </button>
              )
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded-lg text-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            {t.console.backHome}
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded-lg text-sm transition-colors"
          >
            <LogOut className="w-4 h-4" />
            {t.console.logout}
          </button>
        </div>
      </header>

      <main className="flex-1 p-6 overflow-auto">
        {renderContent()}
      </main>
    </div>
  )
}

export default Console
