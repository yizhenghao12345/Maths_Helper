import { createContext, useContext, useState, useCallback } from 'react'
import { zhCN } from './zh-CN'
import { enUS } from './en-US'

export type Language = 'zh-CN' | 'en-US'

type Translations = typeof zhCN

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: Translations
  toggleLanguage: () => void
}

const translations = { 'zh-CN': zhCN, 'en-US': enUS }

const I18nContext = createContext<I18nContextType | null>(null)

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('zh-CN')

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => (prev === 'zh-CN' ? 'en-US' : 'zh-CN'))
  }, [])

  return (
    <I18nContext.Provider
      value={{ language, setLanguage, t: translations[language], toggleLanguage }}
    >
      {children}
    </I18nContext.Provider>
  )
}

export const useI18n = () => {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used within I18nProvider')
  return ctx
}
