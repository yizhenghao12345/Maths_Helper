export interface ConsoleSession {
  id: string
  problem: string
  parsed_problem: Record<string, unknown> | null
  current_step: number
  nodes: string
  edges: string
  is_completed: boolean
  consecutive_errors: number
  created_at: string
  last_active: string
  question_count?: number
  correct_rate?: number
}

export interface ConsoleSessionDetail extends ConsoleSession {
  questions: QuestionRecord[]
}

export interface QuestionRecord {
  id: number
  session_id: string
  question: string
  answer: string
  selected_option: string
  feedback: string
  is_correct: boolean
  step: number
  created_at: string
}

export interface AILog {
  id: number
  session_id: string | null
  provider: string
  model: string
  method: string
  used_parsed_problem?: boolean
  parsed_problem_title?: string | null
  request_summary: string
  response_summary: string
  duration_ms: number
  success: boolean
  error_message: string | null
  created_at: string
}

export interface ConsoleStats {
  total_sessions: number
  completed_sessions: number
  total_questions: number
  correct_rate: number
  problem_type_distribution: Record<string, number>
  avg_steps: number
  recent_sessions: number
  exploration_rate: number
}

export interface ConsoleHealth {
  status: string
  version: string
  ai_enabled: boolean
  ai_provider: string | null
  ai_model: string | null
  ai_fast_model?: string | null
  ai_slow_model?: string | null
  ocr_enabled?: boolean
  ocr_provider?: string | null
  ocr_model?: string | null
  ocr_base_url?: string | null
  db_size: number
  session_count: number
}

export interface AIConfigUpdate {
  provider?: string
  model?: string
  fast_model?: string
  slow_model?: string
  api_key?: string
  base_url?: string
  ocr_provider?: string
  ocr_model?: string
  ocr_api_key?: string
  ocr_base_url?: string
}

export interface ProviderPreset {
  name: string
  base_url: string
  models: string[]
}

export type ProviderPresets = Record<string, ProviderPreset>

export interface AIFullConfig {
  provider: string
  model: string
  fast_model?: string
  slow_model?: string
  api_key_masked: string
  base_url: string
  enabled: boolean
  ocr: {
    provider: string
    model: string
    api_key_masked: string
    base_url: string
    enabled: boolean
  }
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  response_preview?: string
}
