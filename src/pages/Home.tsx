import { useNavigate } from 'react-router-dom'
import { Brain, Lightbulb, Target, Languages } from 'lucide-react'
import { useI18n } from '@/i18n/I18nContext'

const Home = () => {
  const navigate = useNavigate()
  const { t, toggleLanguage, language } = useI18n()

  const featureIcons = [Brain, Lightbulb, Target]

  const gradientClasses = [
    'from-blue-500 to-cyan-400',
    'from-amber-500 to-orange-400',
    'from-green-500 to-emerald-400',
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <header className="px-4 py-3 sm:px-8 sm:py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 sm:w-8 sm:h-8 text-blue-600" />
          <span className="text-lg sm:text-xl font-bold text-gray-800">{t.home.appName}</span>
        </div>
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-1 sm:gap-2 px-3 py-1.5 sm:px-4 sm:py-2 bg-white border-2 border-blue-200 text-blue-600 font-medium rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm text-sm sm:text-base"
          title={language === 'zh-CN' ? 'Switch to English' : '切换到中文'}
        >
          <Languages className="w-4 h-4 sm:w-5 sm:h-5" />
          <span>{t.common.languageSwitch}</span>
        </button>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-8 py-8 sm:py-16">
        <section className="text-center mb-12 sm:mb-20">
          <h1 className="text-3xl sm:text-5xl font-bold text-gray-900 mb-4 sm:mb-6 animate-fade-in px-2">
            {t.home.title}
          </h1>
          <p className="text-base sm:text-xl text-gray-600 max-w-2xl mx-auto mb-6 sm:mb-10 px-4">
            {t.home.subtitle}
          </p>
          <button
            onClick={() => navigate('/input')}
            className="px-6 py-3 sm:px-8 sm:py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-base sm:text-lg font-semibold rounded-full shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 pulse-animation active:scale-95"
          >
            {t.home.startButton}
          </button>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-8">
          {t.home.features.map((feature, index) => {
            const IconComponent = featureIcons[index]
            return (
              <div
                key={index}
                className="bg-white rounded-2xl p-6 sm:p-8 shadow-md hover:shadow-xl transform hover:-translate-y-2 transition-all duration-300"
              >
                <div className={`w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br ${gradientClasses[index]} flex items-center justify-center mb-4 sm:mb-6`}>
                  <IconComponent className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-semibold text-gray-800 mb-2 sm:mb-3">
                  {feature.title}
                </h3>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </section>
      </main>
    </div>
  )
}

export default Home
