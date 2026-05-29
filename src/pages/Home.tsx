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
      <header className="px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Brain className="w-8 h-8 text-blue-600" />
          <span className="text-xl font-bold text-gray-800">{t.home.appName}</span>
        </div>
        <button
          onClick={toggleLanguage}
          className="flex items-center gap-2 px-4 py-2 bg-white border-2 border-blue-200 text-blue-600 font-medium rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all shadow-sm"
          title={language === 'zh-CN' ? 'Switch to English' : '切换到中文'}
        >
          <Languages className="w-5 h-5" />
          <span>{t.common.languageSwitch}</span>
        </button>
      </header>

      <main className="max-w-6xl mx-auto px-8 py-16">
        <section className="text-center mb-20">
          <h1 className="text-5xl font-bold text-gray-900 mb-6 animate-fade-in">
            {t.home.title}
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            {t.home.subtitle}
          </p>
          <button
            onClick={() => navigate('/input')}
            className="px-8 py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-lg font-semibold rounded-full shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 pulse-animation"
          >
            {t.home.startButton}
          </button>
        </section>

        <section className="grid md:grid-cols-3 gap-8">
          {t.home.features.map((feature, index) => {
            const IconComponent = featureIcons[index]
            return (
              <div
                key={index}
                className="bg-white rounded-2xl p-8 shadow-md hover:shadow-xl transform hover:-translate-y-2 transition-all duration-300"
              >
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${gradientClasses[index]} flex items-center justify-center mb-6`}>
                  <IconComponent className="w-7 h-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-800 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
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
