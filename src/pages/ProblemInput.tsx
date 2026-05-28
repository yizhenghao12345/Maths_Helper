import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Send, Upload, Image, X, Loader2 } from 'lucide-react'
import { submitProblem, recognizeImage } from '@/api'
import { useStore } from '@/store/useStore'

const ProblemInput = () => {
  const navigate = useNavigate()
  const [problem, setProblem] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [isRecognizing, setIsRecognizing] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const setSessionId = useStore((state) => state.setSessionId)
  const setNodesAndEdges = useStore((state) => state.setNodesAndEdges)
  const setQuestion = useStore((state) => state.setQuestion)

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('请选择图片文件')
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
      const result = await recognizeImage(imageFile)
      if (result.text) {
        setProblem((prev) => (prev ? prev + '\n' + result.text : result.text))
      } else {
        setError('未识别到文字内容')
      }
    } catch (err) {
      setError('图片识别失败,请重试')
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
      setError('请输入题目内容')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await submitProblem(problem)
      setSessionId(response.sessionId)
      setNodesAndEdges(response.initialNodes, response.initialEdges)
      setQuestion('观察这道题,你认为第一步应该做什么?', [
        'A. 仔细分析已知条件',
        'B. 直接尝试计算',
        'C. 跳过分析',
        'D. 不做思考',
      ])
      navigate('/deduction')
    } catch (err) {
      setError('提交失败,请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50">
      <header className="px-8 py-4">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回首页</span>
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-8 py-12">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-2">输入题目</h2>
          <p className="text-gray-600 mb-8">
            输入你要解决的数学题目,系统将为你生成思维推导图
          </p>

          {imagePreview && (
            <div className="mb-6 relative">
              <div className="relative inline-block">
                <img
                  src={imagePreview}
                  alt="预览"
                  className="max-h-64 rounded-xl border-2 border-gray-200 object-contain"
                />
                <button
                  onClick={handleRemoveImage}
                  className="absolute -top-2 -right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={handleRecognize}
                disabled={isRecognizing}
                className="ml-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isRecognizing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Image className="w-4 h-4" />
                )}
                {isRecognizing ? '识别中...' : '识别图片文字'}
              </button>
            </div>
          )}

          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <Upload className="w-4 h-4" />
                <span>上传图片</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="hidden"
              />
            </div>

            <textarea
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              placeholder="例如: 解方程 2x + 5 = 13, 求x的值"
              className="w-full h-40 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-none text-gray-700 text-lg"
            />
            <div className="text-right mt-2 text-sm text-gray-500">
              {problem.length} 字
            </div>
          </div>

          {error && (
            <div className="mb-4 px-4 py-3 bg-red-50 text-red-600 rounded-lg">
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full py-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white text-lg font-semibold rounded-xl shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Send className="w-5 h-5" />
            {isLoading ? '解析中...' : '开始推演'}
          </button>
        </div>
      </main>
    </div>
  )
}

export default ProblemInput
