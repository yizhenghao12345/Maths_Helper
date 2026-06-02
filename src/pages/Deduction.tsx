import { useState } from 'react'
import { ArrowLeft, Map, MessageSquare } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import DeductionFlow from '@/components/DeductionFlow'
import QuestionPanel from '@/components/QuestionPanel'
import { useI18n } from '@/i18n/I18nContext'

const Deduction = () => {
  const navigate = useNavigate()
  const { t } = useI18n()
  const [activeTab, setActiveTab] = useState<'flow' | 'question'>('question')

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <header className="px-4 py-2.5 sm:px-6 sm:py-3 bg-white border-b border-gray-200 flex items-center gap-3 sm:gap-4">
        <button
          onClick={() => navigate('/input')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors active:text-blue-600"
        >
          <ArrowLeft className="w-5 h-5" />
          <span className="hidden sm:inline">{t.deduction.back}</span>
        </button>
        <h2 className="text-base sm:text-lg font-semibold text-gray-800 flex-1 truncate">{t.deduction.title}</h2>

        {/* Mobile Tab Switcher */}
        <div className="flex sm:hidden bg-gray-100 rounded-lg p-0.5">
          <button
            onClick={() => setActiveTab('question')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'question'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-500'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>{t.deduction.mobileTabQuestion}</span>
          </button>
          <button
            onClick={() => setActiveTab('flow')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'flow'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-500'
            }`}
          >
            <Map className="w-3.5 h-3.5" />
            <span>{t.deduction.mobileTabFlow}</span>
          </button>
        </div>
      </header>

      {/* Desktop: side-by-side | Mobile: tab switch */}
      <div className="flex-1 min-h-0 overflow-hidden hidden sm:flex">
        <DeductionFlow />
        <QuestionPanel />
      </div>

      {/* Mobile: both components always mounted, CSS toggles visibility */}
      <div className="flex-1 min-h-0 overflow-hidden sm:hidden relative">
        <div className={`absolute inset-0 ${activeTab === 'flow' ? 'block' : 'hidden'}`}>
          <DeductionFlow visible={activeTab === 'flow'} />
        </div>
        <div className={`absolute inset-0 ${activeTab === 'question' ? 'block' : 'hidden'}`}>
          <QuestionPanel />
        </div>
      </div>
    </div>
  )
}

export default Deduction
