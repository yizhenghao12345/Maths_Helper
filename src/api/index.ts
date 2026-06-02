import type { SubmitProblemResponse, QuestionResponse } from '@/types'

// OCR 返回的三合一结果
export interface OcrResult {
  text: string
  // AI OCR 路径时同步返回，Tesseract 降级时为 null
  parsed_problem: Record<string, unknown> | null
  first_question: Record<string, unknown> | null
}

export async function submitProblem(
  problem: string,
  problemType?: string,
  language = 'zh-CN',
  // OCR 预解析结果（可选），有则跳过后端 AI 解析 + 首题生成
  parsed_problem?: Record<string, unknown> | null,
  first_question?: Record<string, unknown> | null,
): Promise<SubmitProblemResponse> {
  const response = await fetch('/api/problem/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem, problemType, language, parsed_problem, first_question }),
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => '')
    console.error('submitProblem failed:', response.status, errorText)
    throw new Error(`提交题目失败: ${response.status} ${errorText}`)
  }

  return response.json()
}

export async function answerQuestion(
  sessionId: string,
  userAnswer: string,
  currentNodeId: string,
  currentQuestion?: string | null,
  currentOptions?: string[] | null,
  language = 'zh-CN'
): Promise<QuestionResponse> {
  const response = await fetch('/api/question/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, userAnswer, currentNodeId, currentQuestion, currentOptions, language }),
  })

  if (!response.ok) {
    throw new Error('提交答案失败')
  }

  return response.json()
}

export async function recognizeImage(file: File, language = 'zh-CN'): Promise<OcrResult> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('language', language)

  const response = await fetch('/api/ocr/recognize', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('图片识别失败')
  }

  return response.json()
}
