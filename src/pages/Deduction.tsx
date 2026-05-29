import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import DeductionFlow from '@/components/DeductionFlow'
import QuestionPanel from '@/components/QuestionPanel'
import { useI18n } from '@/i18n/I18nContext'

const Deduction = () => {
  const navigate = useNavigate()
  const { t } = useI18n()

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="px-6 py-3 bg-white border-b border-gray-200 flex items-center gap-4">
        <button
          onClick={() => navigate('/input')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>{t.deduction.back}</span>
        </button>
        <h2 className="text-lg font-semibold text-gray-800">{t.deduction.title}</h2>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <DeductionFlow />
        <QuestionPanel />
      </div>
    </div>
  )
}

export default Deduction
