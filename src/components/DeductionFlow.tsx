import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
  useNodesInitialized,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '@/store/useStore'
import dagre from 'dagre'

const nodeWidth = 200
const nodeHeight = 120

const nodeColors: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  condition: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af', icon: '📋' },
  inference: { bg: '#f0fdf4', border: '#22c55e', text: '#166534', icon: '✓' },
  conclusion: { bg: '#dcfce7', border: '#16a34a', text: '#14532d', icon: '🎯' },
  question: { bg: '#fef2f2', border: '#f43f5e', text: '#9f1239', icon: '❓' },
  exploration: { bg: '#fff7ed', border: '#f97316', text: '#9a3412', icon: '?' },
  dead_end: { bg: '#fef2f2', border: '#ef4444', text: '#991b1b', icon: '⚠️' },
}

function getLayoutedElements(nodes: Node[], edges: Edge[], direction = 'LR') {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: direction, ranksep: 120, nodesep: 60 })

  nodes.forEach((node) => {
    g.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    }
  })

  return layoutedNodes
}

const DeductionFlow = () => {
  const nodes = useStore((state) => state.deduction.nodes)
  const edges = useStore((state) => state.deduction.edges)

  const rfNodes: Node[] = useMemo(
    () => {
      const baseNodes: Node[] = nodes.map((node) => {
        const colors = nodeColors[node.type] || nodeColors.condition
        return {
          id: node.id,
          type: 'default',
          position: { x: 0, y: 0 },
          data: {
            label: (
              <div className="text-center">
                <div className="text-lg mb-1">{colors.icon}</div>
                <div className="font-semibold text-sm">{node.label}</div>
                <div className="text-xs mt-2 whitespace-pre-wrap leading-relaxed">
                  {node.data.content}
                </div>
              </div>
            ),
          },
          style: {
            background: colors.bg,
            border: `2px solid ${colors.border}`,
            borderRadius: '12px',
            padding: '12px 16px',
            minWidth: '160px',
            maxWidth: '220px',
            boxShadow: node.type === 'dead_end' ? '0 4px 12px rgba(239, 68, 68, 0.3)' : '0 4px 6px rgba(0,0,0,0.1)',
            color: colors.text,
          },
        }
      })

      const rfEdges: Edge[] = edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        animated: edge.animated,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: {
          stroke: edge.style || '#94a3b8',
          strokeWidth: 2,
          strokeDasharray: edge.dashed ? '8 4' : 'none',
        },
      }))

      return getLayoutedElements(baseNodes, rfEdges)
    },
    [nodes, edges]
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
        style: {
          stroke: edge.style || '#94a3b8',
          strokeWidth: 2,
          strokeDasharray: edge.dashed ? '8 4' : 'none',
        },
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
