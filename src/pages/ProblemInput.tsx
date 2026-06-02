import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Upload, Image, X, Loader2, Sparkles } from 'lucide-react'
import { submitProblem, recognizeImage } from '@/api'
import { useStore } from '@/store/useStore'
import { useI18n } from '@/i18n/I18nContext'

const ProblemInput = () => {
  const navigate = useNavigate()
  const { t, language } = useI18n()
  const [problem, setProblem] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState<'submitting' | 'thinking'>('submitting')
  const [error, setError] = useState('')
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const setSessionId = useStore((state) => state.setSessionId)
  const setNodesAndEdges = useStore((state) => state.setNodesAndEdges)
  const setQuestion = useStore((state) => state.setQuestion)
  const resetDeduction = useStore((state) => state.resetDeduction)

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError(t.input.selectImageError)
      return
    }

    setImageFile(file)
    const reader = new FileReader()
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
    }
    reader.readAsDataURL(file)
    setError('')
  }

  const handleRecognize = async () => {
    if (!imageFile) return

    setIsRecognizing(true)
    setError('')

    try {
      const result = await recognizeImage(imageFile, language)
      if (result.text) {
        setProblem((prev) => (prev ? prev + '\n' + result.text : result.text))
      } else {
        setError(t.input.noTextRecognized)
      }
    } catch {
      setError(t.input.recognizeError)
    } finally {
      setIsRecognizing(false)
    }
  }

  const handleRemoveImage = () => {
    setImageFile(null)
    setImagePreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSubmit = async () => {
    if (!problem.trim()) {
      setError(t.input.pleaseInput)
      return
    }

    setIsLoading(true)
    setError('')
    setLoadingStage('submitting')

    try {
      const response = await submitProblem(problem, undefined, language)
      setLoadingStage('thinking')
      resetDeduction()
      setSessionId(response.sessionId)
      setNodesAndEdges(response.initialNodes, response.initialEdges)
      const question = response.firstQuestion || t.input.firstQuestion
      const options = response.firstOptions || (t.input.firstOptions as string[])
      setQuestion(question, options)

      setTimeout(() => {
        setIsLoading(false)
        navigate('/deduction')
      }, 2000)
    } catch (e) {
      console.error('handleSubmit catch:', e)
      setError(t.input.submitError)
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <header className="px-4 py-3 sm:px-8 sm:py-4">
        <button
          onClick={() => navigate('/')}
          disabled={isLoading}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors active:text-blue-600"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>{t.input.backHome}</span>
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-4 sm:px-8 py-6 sm:py-12">
        {isLoading ? (
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
            <div className="flex flex-col items-center justify-center py-12 sm:py-16 text-center">
              {loadingStage === 'submitting' ? (
                <>
                  <div className="mb-6 sm:mb-8 relative">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
                      <Send className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
                    </div>
                    <div className="absolute inset-0 w-16 h-16 sm:w-20 sm:h-20 bg-blue-300 rounded-full animate-ping opacity-20" />
                  </div>
                  <p className="text-gray-600 font-semibold text-lg sm:text-xl mb-3">{t.input.submitting}</p>
                  <div className="flex items-center gap-2 text-gray-400">
                    <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                    <span className="text-xs sm:text-sm">{t.deduction.analyzing}</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="mb-6 sm:mb-8 relative">
                    <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center animate-pulse">
                      <Sparkles className="w-8 h-8 sm:w-10 sm:h-10 text-white" />
                    </div>
                    <div className="absolute inset-0 w-16 h-16 sm:w-20 sm:h-20 bg-purple-300 rounded-full animate-ping opacity-20" />
                  </div>
                  <p className="text-gray-600 font-semibold text-lg sm:text-xl mb-3">{t.input.aiThinking}</p>
                  <div className="flex items-center gap-2 text-gray-400">
                    <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                    <span className="text-xs sm:text-sm">{t.input.aiThinkingSub}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">{t.input.title}</h2>
            <p className="text-sm sm:text-base text-gray-600 mb-6 sm:mb-8">
              {t.input.subtitle}
            </p>

            {imagePreview && (
              <div className="mb-6 flex flex-col sm:flex-row sm:items-start gap-3">
                <div className="relative inline-block">
                  <img
                    src={imagePreview}
                    alt={t.input.preview}
                    className="max-h-48 sm:max-h-64 rounded-xl border-2 border-gray-200 object-contain w-full sm:w-auto"
                  />
                  <button
                    onClick={handleRemoveImage}
                    disabled={isLoading || isRecognizing}
                    className="absolute -top-2 -right-2 w-7 h-7 sm:w-8 sm:h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md active:bg-red-600"
                  >
                    <X className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  </button>
                </div>
                <button
                  onClick={handleRecognize}
                  disabled={isRecognizing || isLoading}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center gap-2 self-start active:bg-blue-600"
                >
                  {isRecognizing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Image className="w-4 h-4" />
                  )}
                  {isRecognizing ? t.input.recognizing : t.input.recognizeImage}
                </button>
              </div>
            )}

            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors active:bg-gray-200"
                >
                  <Upload className="w-4 h-4" />
                  <span>{t.input.uploadImage}</span>
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  disabled={isLoading}
                  className="hidden"
                />
              </div>

              <textarea
                value={problem}
                onChange={(e) => setProblem(e.target.value)}
                placeholder={t.input.placeholder}
                disabled={isLoading}
                className="w-full h-32 sm:h-40 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-none text-gray-700 text-base sm:text-lg"
              />
              <div className="text-right mt-2 text-xs sm:text-sm text-gray-500">
                {problem.length} {t.input.charCount}
              </div>
            </div>

            {error && (
              <div className="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-lg text-sm sm:text-base">
                {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="w-full py-3 sm:py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-base sm:text-lg font-semibold rounded-xl shadow-md hover:shadow-lg active:scale-98 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Send className="w-5 h-5" />
              {t.input.startDeduction}
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default ProblemInput
