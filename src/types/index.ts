export interface Position {
  x: number
  y: number
}

export interface NodeData {
  content: string
  status: 'pending' | 'active' | 'completed' | 'error' | 'exploration' | 'warning'
}

export interface MindNode {
  id: string
  label: string
  type: 'condition' | 'inference' | 'conclusion' | 'question' | 'exploration' | 'dead_end'
  position: Position
  data: NodeData
}

export interface MindEdge {
  id: string
  source: string
  target: string
  label?: string
  animated?: boolean
  style?: string
  dashed?: boolean
}

export interface SubmitProblemResponse {
  sessionId: string
  initialNodes: MindNode[]
  initialEdges: MindEdge[]
  firstQuestion?: string
  firstOptions?: string[]
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
  needsRetreat?: boolean
  retreatMessage?: string
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
