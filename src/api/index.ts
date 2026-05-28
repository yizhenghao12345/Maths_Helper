import type { SubmitProblemResponse, QuestionResponse } from '@/types'

export async function submitProblem(
  problem: string,
  problemType?: string
): Promise<SubmitProblemResponse> {
  const response = await fetch('/api/problem/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ problem, problemType }),
  })

  if (!response.ok) {
    throw new Error('提交题目失败')
  }

  return response.json()
}

export async function answerQuestion(
  sessionId: string,
  userAnswer: string,
  currentNodeId: string
): Promise<QuestionResponse> {
  const response = await fetch('/api/question/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, userAnswer, currentNodeId }),
  })

  if (!response.ok) {
    throw new Error('提交答案失败')
  }

  return response.json()
}

export async function recognizeImage(file: File): Promise<{ text: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('/api/ocr/recognize', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('图片识别失败')
  }

  return response.json()
}
