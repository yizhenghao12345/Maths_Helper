import { useState } from 'react'
import { CheckCircle, XCircle, ChevronRight, RefreshCw, AlertTriangle, Loader2, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { answerQuestion } from '@/api'
import { useStore } from '@/store/useStore'
import { useI18n } from '@/i18n/I18nContext'

const QuestionPanel = () => {
  const navigate = useNavigate()
  const { t, language } = useI18n()
  const deduction = useStore((state) => state.deduction)
  const setQuestion = useStore((state) => state.setQuestion)
  const setFeedback = useStore((state) => state.setFeedback)
  const setCompleted = useStore((state) => state.setCompleted)
  const appendNodesAndEdges = useStore((state) => state.appendNodesAndEdges)

  const [lastAnswerCorrect, setLastAnswerCorrect] = useState<boolean | null>(null)
  const [needsRetreat, setNeedsRetreat] = useState(false)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [isAnswering, setIsAnswering] = useState(false)

  const handleAnswer = async (answer: string) => {
    if (!deduction.sessionId || isAnswering) return

    setSelectedOption(answer)
    setIsAnswering(true)

    const questionNodes = deduction.nodes.filter((n) => n.type === 'question')
    const currentNodeId = questionNodes[deduction.deductionStep ?? 0]?.id ?? ''

    try {
      const response = await answerQuestion(
        deduction.sessionId,
        answer.charAt(0),
        currentNodeId,
        language
      )

      setLastAnswerCorrect(response.isCorrect)
      setNeedsRetreat(response.needsRetreat || false)

      if (response.nextNodes && response.nextEdges) {
        appendNodesAndEdges(response.nextNodes, response.nextEdges)
      }

      if (response.needsRetreat && response.retreatMessage) {
        setFeedback(response.retreatMessage)
      } else {
        setFeedback(response.feedback || null)
      }

      if (response.isCompleted) {
        setCompleted(true, response.finalSolution)
      } else if (response.nextQuestion && response.options) {
        setQuestion(response.nextQuestion, response.options)
      }
    } catch {
      setFeedback(t.deduction.submitError)
    } finally {
      setSelectedOption(null)
      setIsAnswering(false)
    }
  }

  const handleRestart = () => {
    navigate('/input')
  }

  const panelClasses = "w-full sm:w-96 flex-shrink-0 bg-white border-l border-gray-200 h-full flex flex-col"

  if (deduction.isCompleted) {
    return (
      <div className={panelClasses}>
        <div className="p-4 sm:p-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="w-7 h-7 sm:w-8 sm:h-8" />
            <h3 className="text-lg sm:text-xl font-bold">{t.deduction.completedTitle}</h3>
          </div>
          <p className="text-green-50 text-sm sm:text-base">{t.deduction.completedDesc}</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          <h4 className="font-semibold text-gray-800 mb-3 text-sm sm:text-base">{t.deduction.solutionTitle}</h4>
          <div className="bg-gray-50 rounded-xl p-4 text-sm sm:text-base text-gray-700 leading-relaxed whitespace-pre-wrap">
            {deduction.finalSolution}
          </div>
        </div>

        <div className="p-3 sm:p-4 border-t border-gray-200">
          <button
            onClick={handleRestart}
            className="w-full py-3 bg-blue-500 text-white font-semibold rounded-xl hover:bg-blue-600 transition-colors flex items-center justify-center gap-2 text-sm sm:text-base active:bg-blue-600"
          >
            <RefreshCw className="w-5 h-5" />
            {t.deduction.nextProblem}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={panelClasses}>
      <div className="p-4 sm:p-6 bg-gradient-to-r from-blue-500 to-cyan-500 text-white">
        <h3 className="text-base sm:text-lg font-bold mb-1">{t.deduction.thinkingGuide}</h3>
        <p className="text-blue-100 text-xs sm:text-sm">{t.deduction.followThinking}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 sm:p-6">
        {isAnswering ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-6 relative">
              <div className="w-14 h-14 sm:w-16 sm:h-16 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
                <Sparkles className="w-7 h-7 sm:w-8 sm:h-8 text-white" />
              </div>
              <div className="absolute inset-0 w-14 h-14 sm:w-16 sm:h-16 bg-blue-300 rounded-full animate-ping opacity-20" />
            </div>
            <p className="text-gray-600 font-semibold text-base sm:text-lg mb-2">{t.deduction.aiThinking}</p>
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 animate-spin" />
              <span className="text-xs sm:text-sm">{t.deduction.aiThinkingSub}</span>
            </div>
          </div>
        ) : (
          <>
            {deduction.currentQuestion && (
              <div className="mb-6">
                <div className="flex items-start gap-3 mb-4">
                  <ChevronRight className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500 flex-shrink-0 mt-0.5" />
                  <h4 className="text-sm sm:text-base text-gray-800 font-semibold leading-relaxed">
                    {deduction.currentQuestion}
                  </h4>
                </div>
              </div>
            )}

            {deduction.currentOptions && (
              <div className="space-y-2 sm:space-y-3" key={deduction.currentQuestion}>
                {deduction.currentOptions.map((option, index) => {
                  const isSelected = selectedOption === option
                  return (
                    <button
                      key={index}
                      onClick={() => handleAnswer(option)}
                      disabled={isAnswering}
                      className={`w-full text-left px-3 sm:px-4 py-2.5 sm:py-3 rounded-xl border-2 transition-all duration-200 text-sm sm:text-base ${
                        isAnswering
                          ? 'opacity-40 cursor-not-allowed border-gray-200' +
                            (isSelected ? ' ring-2 ring-blue-500 border-blue-400 opacity-70 font-bold' : '')
                          : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50 active:bg-blue-50'
                      } text-gray-700 disabled:cursor-not-allowed`}
                    >
                      {option}
                    </button>
                  )
                })}
              </div>
            )}

            {deduction.feedback && (
              <div
                className={`mt-4 sm:mt-6 px-3 sm:px-4 py-2.5 sm:py-3 rounded-xl text-sm sm:text-base ${
                  lastAnswerCorrect === true
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : needsRetreat
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-orange-50 text-orange-700 border border-orange-200'
                }`}
              >
                <div className="flex items-start gap-2">
                  {lastAnswerCorrect === true ? (
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0 mt-0.5" />
                  ) : needsRetreat ? (
                    <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0 mt-0.5" />
                  ) : (
                    <XCircle className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0 mt-0.5" />
                  )}
                  <p className="leading-relaxed whitespace-pre-wrap">{deduction.feedback}</p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default QuestionPanel
