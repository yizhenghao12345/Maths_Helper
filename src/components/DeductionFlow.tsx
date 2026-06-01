import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
import dagre from 'dagre'

const minNodeWidth = 180
const maxNodeWidth = 280
const mobileMinNodeWidth = 140
const mobileMaxNodeWidth = 220
const minNodeHeight = 120
const nodeHorizontalPadding = 32
const nodeVerticalPadding = 24
const titleLineHeight = 20
const contentLineHeight = 18
const iconHeight = 28
const textGap = 8

const isMobile = () => typeof window !== 'undefined' && window.innerWidth < 640

const getEffectiveNodeWidths = () => {
  return isMobile()
    ? { min: mobileMinNodeWidth, max: mobileMaxNodeWidth }
    : { min: minNodeWidth, max: maxNodeWidth }
}

const nodeColors: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  condition: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af', icon: '📋' },
  inference: { bg: '#f0fdf4', border: '#22c55e', text: '#166534', icon: '✓' },
  conclusion: { bg: '#dcfce7', border: '#16a34a', text: '#14532d', icon: '🎯' },
  question: { bg: '#fef2f2', border: '#f43f5e', text: '#9f1239', icon: '❓' },
  exploration: { bg: '#fff7ed', border: '#f97316', text: '#9a3412', icon: '?' },
  dead_end: { bg: '#fef2f2', border: '#ef4444', text: '#991b1b', icon: '⚠️' },
}

type NodeSizeMap = Record<string, { width: number; height: number }>

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function estimateWrappedLines(text: string, charsPerLine: number) {
  return text
    .split('\n')
    .reduce((total, line) => total + Math.max(1, Math.ceil(line.length / Math.max(charsPerLine, 1))), 0)
}

function estimateNodeSize(label: string, content: string) {
  const { min, max } = getEffectiveNodeWidths()
  const longestLine = Math.max(
    ...[label, content]
      .flatMap((text) => text.split('\n'))
      .map((line) => line.trim().length),
    0
  )
  const width = clamp(longestLine * 7 + nodeHorizontalPadding, min, max)
  const titleCharsPerLine = Math.max(8, Math.floor((width - nodeHorizontalPadding) / 8))
  const contentCharsPerLine = Math.max(12, Math.floor((width - nodeHorizontalPadding) / 7))
  const titleLines = estimateWrappedLines(label, titleCharsPerLine)
  const contentLines = estimateWrappedLines(content, contentCharsPerLine)
  const contentBlockHeight = content ? contentLines * contentLineHeight + textGap : 0
  const height =
    nodeVerticalPadding * 2 +
    iconHeight +
    titleLines * titleLineHeight +
    contentBlockHeight

  return {
    width,
    height: Math.max(minNodeHeight, height),
  }
}

function getNodeBox(node: Node, measuredNodeSizes?: NodeSizeMap) {
  const measuredSize = measuredNodeSizes?.[node.id]
  if (measuredSize) {
    return measuredSize
  }

  const width = typeof node.style?.width === 'number' ? node.style.width : minNodeWidth
  const minHeight = typeof node.style?.minHeight === 'number' ? node.style.minHeight : minNodeHeight

  return { width, height: minHeight }
}

function getLayoutedElements(nodes: Node[], edges: Edge[], measuredNodeSizes: NodeSizeMap, direction = 'LR') {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: direction, ranksep: 120, nodesep: 60 })

  nodes.forEach((node) => {
    const { width, height } = getNodeBox(node, measuredNodeSizes)
    g.setNode(node.id, { width, height })
  })

  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target)
  })

  dagre.layout(g)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = g.node(node.id)
    const { width, height } = getNodeBox(node, measuredNodeSizes)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - width / 2,
        y: nodeWithPosition.y - height / 2,
      },
    }
  })

  return layoutedNodes
}

const DeductionFlow = () => {
  const nodes = useStore((state) => state.deduction.nodes)
  const edges = useStore((state) => state.deduction.edges)
  const [measuredNodeSizes, setMeasuredNodeSizes] = useState<NodeSizeMap>({})
  const containerRef = useRef<HTMLDivElement>(null)
  const [fitViewKey, setFitViewKey] = useState(0)

  useEffect(() => {
    setMeasuredNodeSizes((prev) => {
      const nextEntries = Object.entries(prev).filter(([nodeId]) => nodes.some((node) => node.id === nodeId))
      if (nextEntries.length === Object.keys(prev).length) {
        return prev
      }

      return Object.fromEntries(nextEntries)
    })
  }, [nodes])

  const rfNodes: Node[] = useMemo(
    () => {
      const baseNodes: Node[] = nodes.map((node) => {
        const colors = nodeColors[node.type] || nodeColors.condition
        const size = measuredNodeSizes[node.id] ?? estimateNodeSize(node.label, node.data.content)
        return {
          id: node.id,
          type: 'default',
          position: { x: 0, y: 0 },
          data: {
            label: (
              <div className="flex h-full w-full flex-col items-center justify-center text-center">
                <div className="mb-1 text-lg leading-none">{colors.icon}</div>
                <div className="text-sm font-semibold leading-snug">{node.label}</div>
                <div className="mt-2 text-xs leading-relaxed whitespace-pre-wrap break-words">
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
            width: size.width,
            minHeight: size.height,
            boxShadow: node.type === 'dead_end' ? '0 4px 12px rgba(239, 68, 68, 0.3)' : '0 4px 6px rgba(0,0,0,0.1)',
            color: colors.text,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
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

      return getLayoutedElements(baseNodes, rfEdges, measuredNodeSizes)
    },
    [nodes, edges, measuredNodeSizes]
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

  useEffect(() => {
    const triggerFitView = () => setFitViewKey((k) => k + 1)
    window.addEventListener('resize', triggerFitView)
    return () => window.removeEventListener('resize', triggerFitView)
  }, [])

  useEffect(() => {
    // Re-fit view when nodes or edges change
  }, [rfNodes, rfEdges.length, measuredNodeSizes])

  return (
    <div ref={containerRef} className="flex-1 min-w-0 min-h-0 overflow-hidden w-full h-full">
      <ReactFlow
        key={fitViewKey}
        nodes={rfNodes}
        edges={rfEdges}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.15 }}
      >
        <Background color="#e2e8f0" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

export default DeductionFlow
