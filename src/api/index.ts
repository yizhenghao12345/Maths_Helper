import type { SubmitProblemResponse, QuestionResponse } from '@/types'

/** OCR 识别返回格式（只含文字） */
export interface OcrResult {
  text: string
}

/** /health 接口返回格式（部分字段） */
export interface HealthInfo {
  status: string
  ai_enabled: boolean
  ai_model: string | null
  ocr_model: string | null
}

export async function fetchHealth(): Promise<HealthInfo> {
  const response = await fetch('/api/health')
  if (!response.ok) throw new Error('获取服务信息失败')
  return response.json()
}

export async function submitProblem(
  problem: string,
  problemType?: string,
  language = 'zh-CN',
): Promise<SubmitProblemResponse> {
  const response = await fetch('/api/problem/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem, problemType, language }),
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
