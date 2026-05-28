export interface Position {
  x: number
  y: number
}

export interface NodeData {
  content: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

export interface MindNode {
  id: string
  label: string
  type: 'condition' | 'inference' | 'conclusion' | 'question'
  position: Position
  data: NodeData
}

export interface MindEdge {
  id: string
  source: string
  target: string
  label?: string
  animated?: boolean
}

export interface SubmitProblemResponse {
  sessionId: string
  initialNodes: MindNode[]
  initialEdges: MindEdge[]
}

export interface QuestionResponse {
  isCorrect: boolean
  feedback?: string
  nextNodes?: MindNode[]
  nextEdges?: MindEdge[]
  nextQuestion?: string
  options?: string[]
  isCompleted: boolean
  finalSolution?: string
}

export interface DeductionState {
  sessionId: string | null
  nodes: MindNode[]
  edges: MindEdge[]
  currentQuestion: string | null
  currentOptions: string[] | null
  feedback: string | null
  isCompleted: boolean
  finalSolution: string | null
  deductionStep: number
}
