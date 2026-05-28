import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '@/store/useStore'

const nodeColors: Record<string, { bg: string; border: string; text: string }> = {
  condition: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af' },
  inference: { bg: '#fefce8', border: '#eab308', text: '#854d0e' },
  conclusion: { bg: '#f0fdf4', border: '#22c55e', text: '#166534' },
  question: { bg: '#fef2f2', border: '#f43f5e', text: '#9f1239' },
}

const DeductionFlow = () => {
  const nodes = useStore((state) => state.deduction.nodes)
  const edges = useStore((state) => state.deduction.edges)

  const rfNodes: Node[] = useMemo(
    () =>
      nodes.map((node) => ({
        id: node.id,
        type: 'default',
        position: node.position,
        data: {
          label: node.label,
          content: node.data.content,
          status: node.data.status,
        },
        style: {
          background: nodeColors[node.type]?.bg || '#fff',
          border: `2px solid ${nodeColors[node.type]?.border || '#ccc'}`,
          borderRadius: '12px',
          padding: '12px 16px',
          minWidth: '180px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          color: nodeColors[node.type]?.text || '#333',
        },
      })),
    [nodes]
  )

  const rfEdges: Edge[] = useMemo(
    () =>
      edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: edge.animated,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { stroke: '#94a3b8', strokeWidth: 2 },
      })),
    [edges]
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    console.log('Node clicked:', node.data)
  }, [])

  return (
    <div className="flex-1 h-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Background color="#e2e8f0" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export default DeductionFlow
