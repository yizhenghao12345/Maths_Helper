import { useState } from 'react'
import { CheckCircle, XCircle, ChevronRight, RefreshCw, AlertTriangle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { answerQuestion } from '@/api'
import { useStore } from '@/store/useStore'

const QuestionPanel = () => {
  const navigate = useNavigate()
  const deduction = useStore((state) => state.deduction)
  const setQuestion = useStore((state) => state.setQuestion)
  const setFeedback = useStore((state) => state.setFeedback)
  const setCompleted = useStore((state) => state.setCompleted)
  const appendNodesAndEdges = useStore((state) => state.appendNodesAndEdges)

  const [lastAnswerCorrect, setLastAnswerCorrect] = useState<boolean | null>(null)
  const [needsRetreat, setNeedsRetreat] = useState(false)

  const handleAnswer = async (answer: string) => {
    if (!deduction.sessionId) return

    const questionNodes = deduction.nodes.filter((n) => n.type === 'question')
    const currentNodeId = questionNodes[deduction.deductionStep ?? 0]?.id ?? ''

    try {
      const response = await answerQuestion(
        deduction.sessionId,
        answer.charAt(0),
        currentNodeId
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
    } catch (err) {
      setFeedback('提交失败,请重试')
    }
  }

  const handleRestart = () => {
    navigate('/input')
  }

  if (deduction.isCompleted) {
    return (
      <div className="w-96 bg-white border-l border-gray-200 h-full flex flex-col">
        <div className="p-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white">
          <div className="flex items-center gap-3 mb-3">
            <CheckCircle className="w-8 h-8" />
            <h3 className="text-xl font-bold">推演完成!</h3>
          </div>
          <p className="text-green-50">恭喜你完成了这道题的思维推演</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <h4 className="font-semibold text-gray-800 mb-3">完整解题思路</h4>
          <div className="bg-gray-50 rounded-xl p-4 text-gray-700 leading-relaxed whitespace-pre-wrap">
            {deduction.finalSolution}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleRestart}
            className="w-full py-3 bg-blue-500 text-white font-semibold rounded-xl hover:bg-blue-600 transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-5 h-5" />
            继续下一题
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="w-96 bg-white border-l border-gray-200 h-full flex flex-col">
      <div className="p-6 bg-gradient-to-r from-blue-500 to-cyan-500 text-white">
        <h3 className="text-lg font-bold mb-1">思维引导</h3>
        <p className="text-blue-100 text-sm">跟着问题一步步思考</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {deduction.currentQuestion && (
          <div className="mb-6">
            <div className="flex items-start gap-3 mb-4">
              <ChevronRight className="w-6 h-6 text-blue-500 flex-shrink-0 mt-0.5" />
              <h4 className="text-gray-800 font-semibold leading-relaxed">
                {deduction.currentQuestion}
              </h4>
            </div>
          </div>
        )}

        {deduction.currentOptions && (
          <div className="space-y-3">
            {deduction.currentOptions.map((option, index) => {
              return (
                <button
                  key={index}
                  onClick={() => handleAnswer(option)}
                  disabled={lastAnswerCorrect === true}
                  className="w-full text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-gray-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {option}
                </button>
              )
            })}
          </div>
        )}

        {deduction.feedback && (
          <div
            className={`mt-6 px-4 py-3 rounded-xl ${
              lastAnswerCorrect === true
                ? 'bg-green-50 text-green-700 border border-green-200'
                : needsRetreat
                ? 'bg-red-50 text-red-700 border border-red-200'
                : 'bg-orange-50 text-orange-700 border border-orange-200'
            }`}
          >
            <div className="flex items-start gap-2">
              {lastAnswerCorrect === true ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : needsRetreat ? (
                <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{deduction.feedback}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default QuestionPanel
