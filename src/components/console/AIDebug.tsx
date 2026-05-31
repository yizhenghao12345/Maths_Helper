import { useEffect, useState, useMemo } from 'react'
import {
  Settings,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  Loader2,
  Edit3,
  X,
  Search,
  Play,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'
import { useConsoleStore } from '@/store/useConsoleStore'
import {
  getAILogs,
  updateAIConfig,
  getConsoleHealth,
  getProviderPresets,
  testConnection,
  getAIConfig,
} from '@/api/console'
import type { AIConfigUpdate, ProviderPresets, AIFullConfig, ConnectionTestResult } from '@/types/console'

const AIDebug = () => {
  const { t } = useI18n()
  const { health, setHealth, aiLogs, setAILogs } = useConsoleStore()

  const [fullConfig, setFullConfig] = useState<AIFullConfig | null>(null)
  const [presets, setPresets] = useState<ProviderPresets>({})
  const [isEditing, setIsEditing] = useState(false)
  const [logOffset, setLogOffset] = useState(0)
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null)
  const [updateSuccess, setUpdateSuccess] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const [editProvider, setEditProvider] = useState('')
  const [editModel, setEditModel] = useState('')
  const [editApiKey, setEditApiKey] = useState('')
  const [editBaseUrl, setEditBaseUrl] = useState('')
  const [showApiKey, setShowApiKey] = useState(false)
  const [isCustomModel, setIsCustomModel] = useState(false)
  const [customModelName, setCustomModelName] = useState('')

  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(null)
  const [isTesting, setIsTesting] = useState(false)

  useEffect(() => {
    getAILogs(50, 0).then(setAILogs).catch(() => {})
    if (!health) {
      getConsoleHealth().then(setHealth).catch(() => {})
    }
    getProviderPresets().then(setPresets).catch(() => {})
    getAIConfig().then(setFullConfig).catch(() => {})
  }, [setAILogs, health, setHealth])

  const presetKeys = useMemo(() => Object.keys(presets), [presets])

  const currentPresetModels = useMemo(() => {
    if (!editProvider || editProvider === 'custom' || !presets[editProvider]) return []
    return presets[editProvider].models || []
  }, [editProvider, presets])

  const handleEdit = () => {
    if (fullConfig) {
      setEditProvider(fullConfig.provider)
      setEditModel(fullConfig.model)
      setEditApiKey('')
      setEditBaseUrl(fullConfig.base_url)
      setIsCustomModel(false)
      setCustomModelName('')
    } else {
      setEditProvider('')
      setEditModel('')
      setEditApiKey('')
      setEditBaseUrl('')
      setIsCustomModel(false)
      setCustomModelName('')
    }
    setTestResult(null)
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setTestResult(null)
  }

  const handleProviderChange = (value: string) => {
    setEditProvider(value)
    setTestResult(null)
    if (value === 'custom') {
      setEditBaseUrl('')
      setEditModel('')
      setIsCustomModel(true)
      setCustomModelName('')
    } else if (presets[value]) {
      setEditBaseUrl(presets[value].base_url)
      const models = presets[value].models || []
      if (models.length > 0) {
        setEditModel(models[0])
        setIsCustomModel(false)
        setCustomModelName('')
      } else {
        setEditModel('')
        setIsCustomModel(true)
        setCustomModelName('')
      }
    }
  }

  const handleModelSelect = (value: string) => {
    if (value === '__custom__') {
      setIsCustomModel(true)
      setCustomModelName('')
      setEditModel('')
    } else {
      setIsCustomModel(false)
      setEditModel(value)
      setCustomModelName('')
    }
    setTestResult(null)
  }

  const handleTestConnection = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const model = isCustomModel ? customModelName : editModel
      const result = await testConnection({
        provider: editProvider,
        api_key: editApiKey,
        base_url: editBaseUrl,
        model,
      })
      setTestResult(result)
    } catch {
      setTestResult({ success: false, message: 'Request failed' })
    } finally {
      setIsTesting(false)
    }
  }

  const handleSave = async () => {
    const model = isCustomModel ? customModelName : editModel
    const config: AIConfigUpdate = {
      provider: editProvider,
      model,
      base_url: editBaseUrl,
    }
    if (editApiKey) {
      config.api_key = editApiKey
    }
    try {
      await updateAIConfig(config)
      setUpdateSuccess(true)
      setTimeout(() => setUpdateSuccess(false), 3000)
      const newHealth = await getConsoleHealth()
      setHealth(newHealth)
      const newConfig = await getAIConfig()
      setFullConfig(newConfig)
      setIsEditing(false)
      setTestResult(null)
    } catch {
      // ignore
    }
  }

  const handleLoadMore = async () => {
    const newOffset = logOffset + 50
    try {
      const moreLogs = await getAILogs(50, newOffset)
      setAILogs([...aiLogs, ...moreLogs])
      setLogOffset(newOffset)
    } catch {
      // ignore
    }
  }

  const filteredLogs = useMemo(() => {
    if (!searchQuery.trim()) return aiLogs
    const q = searchQuery.toLowerCase()
    return aiLogs.filter(
      (log) =>
        log.method.toLowerCase().includes(q) ||
        log.provider.toLowerCase().includes(q) ||
        (log.session_id && log.session_id.toLowerCase().includes(q))
    )
  }, [aiLogs, searchQuery])

  const activeModel = isCustomModel ? customModelName : editModel

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Settings className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-semibold text-white">{t.console.aiDebug.config}</h2>
            </div>
            {fullConfig && (
              <span
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                  fullConfig.enabled
                    ? 'bg-green-900/30 text-green-400'
                    : 'bg-red-900/30 text-red-400'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    fullConfig.enabled ? 'bg-green-400' : 'bg-red-400'
                  }`}
                />
                {fullConfig.enabled ? t.console.aiDebug.enabled : t.console.aiDebug.disabled}
              </span>
            )}
          </div>

          {!isEditing ? (
            <div className="space-y-4">
              <div className="bg-gray-900/50 rounded-lg p-4 space-y-3">
                <h3 className="text-sm font-medium text-gray-300">
                  {t.console.aiDebug.currentConfig}
                </h3>
                {fullConfig ? (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">{t.console.aiDebug.provider}</span>
                      <span className="text-white">{fullConfig.provider}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">{t.console.aiDebug.model}</span>
                      <span className="text-white">{fullConfig.model}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">{t.console.aiDebug.apiKey}</span>
                      <span className="text-white">
                        {fullConfig.api_key_masked
                          ? `${t.console.aiDebug.maskedKey} (${fullConfig.api_key_masked})`
                          : t.console.aiDebug.noKey}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">{t.console.aiDebug.baseUrl}</span>
                      <span className="text-white text-xs break-all">{fullConfig.base_url}</span>
                    </div>
                  </>
                ) : (
                  <p className="text-gray-500 text-sm">-</p>
                )}
              </div>
              <button
                onClick={handleEdit}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Edit3 className="w-4 h-4" />
                {t.console.aiDebug.editConfig}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">
                  {t.console.aiDebug.provider}
                </label>
                <select
                  value={editProvider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
                >
                  <option value="">{t.console.aiDebug.providerPlaceholder}</option>
                  {presetKeys.map((key) => (
                    <option key={key} value={key}>
                      {presets[key].name || key}
                    </option>
                  ))}
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">
                  {t.console.aiDebug.model}
                </label>
                {currentPresetModels.length > 0 ? (
                  <select
                    value={isCustomModel ? '__custom__' : editModel}
                    onChange={(e) => handleModelSelect(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
                  >
                    <option value="" disabled>
                      {t.console.aiDebug.modelPlaceholder}
                    </option>
                    {currentPresetModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                    <option value="__custom__">{t.console.aiDebug.customModel}</option>
                  </select>
                ) : (
                  <input
                    type="text"
                    value={isCustomModel ? customModelName : editModel}
                    onChange={(e) => {
                      if (isCustomModel) {
                        setCustomModelName(e.target.value)
                      } else {
                        setEditModel(e.target.value)
                      }
                    }}
                    placeholder={t.console.aiDebug.modelPlaceholder}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
                  />
                )}
                {isCustomModel && currentPresetModels.length > 0 && (
                  <input
                    type="text"
                    value={customModelName}
                    onChange={(e) => setCustomModelName(e.target.value)}
                    placeholder={t.console.aiDebug.modelPlaceholder}
                    className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm mt-2"
                  />
                )}
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">
                  {t.console.aiDebug.apiKey}
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={editApiKey}
                    onChange={(e) => {
                      setEditApiKey(e.target.value)
                      setTestResult(null)
                    }}
                    placeholder="sk-..."
                    className="w-full px-3 py-2 pr-10 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                  >
                    {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-1">
                  {t.console.aiDebug.baseUrl}
                </label>
                <input
                  type="text"
                  value={editBaseUrl}
                  onChange={(e) => {
                    setEditBaseUrl(e.target.value)
                    setTestResult(null)
                  }}
                  placeholder={t.console.aiDebug.baseUrlPlaceholder}
                  className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
                />
              </div>

              {testResult && (
                <div
                  className={`rounded-lg p-3 ${
                    testResult.success
                      ? 'bg-green-900/20 border border-green-800/50'
                      : 'bg-red-900/20 border border-red-800/50'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {testResult.success ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-400" />
                    )}
                    <span
                      className={`text-sm font-medium ${
                        testResult.success ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {testResult.success ? t.console.aiDebug.testSuccess : t.console.aiDebug.testFailed}
                    </span>
                  </div>
                  <p
                    className={`text-xs ${
                      testResult.success ? 'text-green-300/70' : 'text-red-300/70'
                    }`}
                  >
                    {testResult.message}
                  </p>
                  {testResult.response_preview && (
                    <pre className="mt-2 text-xs bg-gray-800/50 rounded p-2 text-gray-300 overflow-x-auto whitespace-pre-wrap">
                      {testResult.response_preview}
                    </pre>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center gap-1.5 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                  {t.console.aiDebug.cancelEdit}
                </button>
                <button
                  onClick={handleTestConnection}
                  disabled={isTesting || !editProvider || !activeModel || !editBaseUrl}
                  className="flex items-center gap-1.5 px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isTesting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  {isTesting ? t.console.aiDebug.testing : t.console.aiDebug.testConnection}
                </button>
                <button
                  onClick={handleSave}
                  disabled={!editProvider || !activeModel || !editBaseUrl}
                  className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {t.console.aiDebug.saveConfig}
                </button>
                {updateSuccess && (
                  <span className="text-green-400 text-sm">{t.console.aiDebug.updateSuccess}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="lg:col-span-3">
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-white">{t.console.aiDebug.logs}</h2>
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.console.aiDebug.searchLogs}
                className="w-full pl-9 pr-3 py-1.5 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
              />
            </div>
          </div>
          {filteredLogs.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500">{t.console.aiDebug.noLogs}</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.time}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.session}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.method}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.provider}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.duration}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.status}
                      </th>
                      <th className="text-left px-4 py-3 text-gray-400 text-xs font-medium">
                        {t.console.aiDebug.response}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredLogs.map((log) => (
                      <>
                        <tr
                          key={log.id}
                          className="border-b border-gray-700/50 hover:bg-gray-750 cursor-pointer transition-colors"
                          onClick={() =>
                            setExpandedLogId(expandedLogId === log.id ? null : log.id)
                          }
                        >
                          <td className="px-4 py-3 text-gray-300 text-xs">
                            <div className="flex items-center gap-1">
                              {expandedLogId === log.id ? (
                                <ChevronDown className="w-3 h-3 text-gray-500" />
                              ) : (
                                <ChevronRight className="w-3 h-3 text-gray-500" />
                              )}
                              {new Date(log.created_at).toLocaleString()}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-300 text-xs font-mono">
                            {log.session_id ? log.session_id.slice(0, 8) + '...' : '-'}
                          </td>
                          <td className="px-4 py-3 text-gray-300 text-xs">{log.method}</td>
                          <td className="px-4 py-3 text-gray-300 text-xs">{log.provider}</td>
                          <td className="px-4 py-3 text-gray-300 text-xs">{log.duration_ms}ms</td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs ${
                                log.success
                                  ? 'bg-green-900/30 text-green-400'
                                  : 'bg-red-900/30 text-red-400'
                              }`}
                            >
                              {log.success ? t.console.aiDebug.success : t.console.aiDebug.failed}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-xs max-w-[200px] truncate">
                            {log.response_summary}
                          </td>
                        </tr>
                        {expandedLogId === log.id && (
                          <tr key={`${log.id}-detail`}>
                            <td colSpan={7} className="px-6 py-4 bg-gray-900/50">
                              <div className="space-y-3">
                                <div>
                                  <p className="text-gray-400 text-xs mb-1">Request:</p>
                                  <pre className="text-gray-300 text-xs bg-gray-800 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                                    {log.request_summary}
                                  </pre>
                                </div>
                                <div>
                                  <p className="text-gray-400 text-xs mb-1">Response:</p>
                                  <pre className="text-gray-300 text-xs bg-gray-800 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                                    {log.response_summary}
                                  </pre>
                                </div>
                                {log.error_message && (
                                  <div>
                                    <p className="text-red-400 text-xs mb-1">Error:</p>
                                    <pre className="text-red-300 text-xs bg-red-900/20 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                                      {log.error_message}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 text-center border-t border-gray-700">
                <button
                  onClick={handleLoadMore}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm rounded-lg transition-colors"
                >
                  {t.console.aiDebug.loadMore}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AIDebug
