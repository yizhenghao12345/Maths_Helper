import { useEffect, useState } from 'react'
import { Settings, Save } from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'
import { getSiteSettings, updateSiteSettings, type SiteSettings } from '@/api/console'

const SettingsPage = () => {
  const { t } = useI18n()
  const [settings, setSettings] = useState<SiteSettings>({ copyright: '' })
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    getSiteSettings()
      .then((data) => setSettings({ copyright: data.copyright || '' }))
      .catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setSaveSuccess(false)
    try {
      const nextSettings = await updateSiteSettings(settings)
      setSettings(nextSettings)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch {
      // ignore
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">{t.console.settings.title}</h2>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-gray-400 text-sm mb-2">
              {t.console.settings.copyright}
            </label>
            <input
              type="text"
              value={settings.copyright}
              onChange={(e) => setSettings({ ...settings, copyright: e.target.value })}
              placeholder={t.console.settings.copyrightPlaceholder}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 outline-none text-sm"
            />
            <p className="mt-1.5 text-xs text-gray-500">
              {t.console.settings.copyrightHint}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? t.console.settings.saving : t.console.settings.save}
            </button>
            {saveSuccess && (
              <span className="text-green-400 text-sm">{t.console.settings.saveSuccess}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
