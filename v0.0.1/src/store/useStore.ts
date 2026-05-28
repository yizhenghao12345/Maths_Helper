import { create } from 'zustand'
import type { DeductionState, MindNode, MindEdge } from '@/types'

interface AppState {
  deduction: DeductionState
  setSessionId: (id: string) => void
  setNodesAndEdges: (nodes: MindNode[], edges: MindEdge[]) => void
  setQuestion: (question: string, options: string[]) => void
  setFeedback: (feedback: string | null) => void
  setCompleted: (completed: boolean, solution?: string) => void
  appendNodesAndEdges: (nodes: MindNode[], edges: MindEdge[]) => void
  incrementStep: () => void
  resetDeduction: () => void
}

const initialDeductionState: DeductionState = {
  sessionId: null,
  nodes: [],
  edges: [],
  currentQuestion: null,
  currentOptions: null,
  feedback: null,
  isCompleted: false,
  finalSolution: null,
  deductionStep: 0,
}

export const useStore = create<AppState>((set) => ({
  deduction: initialDeductionState,

  setSessionId: (id: string) =>
    set((state) => ({
      deduction: { ...state.deduction, sessionId: id },
    })),

  setNodesAndEdges: (nodes: MindNode[], edges: MindEdge[]) =>
    set((state) => ({
      deduction: { ...state.deduction, nodes, edges },
    })),

  setQuestion: (question: string, options: string[]) =>
    set((state) => ({
      deduction: {
        ...state.deduction,
        currentQuestion: question,
        currentOptions: options,
      },
    })),

  setFeedback: (feedback: string | null) =>
    set((state) => ({
      deduction: { ...state.deduction, feedback },
    })),

  setCompleted: (completed: boolean, solution?: string) =>
    set((state) => ({
      deduction: {
        ...state.deduction,
        isCompleted: completed,
        finalSolution: solution || null,
      },
    })),

  appendNodesAndEdges: (nodes: MindNode[], edges: MindEdge[]) =>
    set((state) => ({
      deduction: {
        ...state.deduction,
        nodes: [...state.deduction.nodes, ...nodes],
        edges: [...state.deduction.edges, ...edges],
      },
    })),

  incrementStep: () =>
    set((state) => ({
      deduction: {
        ...state.deduction,
        deductionStep: state.deduction.deductionStep + 1,
      },
    })),

  resetDeduction: () =>
    set({
      deduction: initialDeductionState,
    }),
}))
