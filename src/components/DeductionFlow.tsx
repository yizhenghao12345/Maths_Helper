import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
  useNodesInitialized,
  useReactFlow,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useStore } from '@/store/useStore'
import dagre from 'dagre'

const minNodeWidth = 180
const maxNodeWidth = 280
const minNodeHeight = 120
const nodeHorizontalPadding = 32
const nodeVerticalPadding = 24
const titleLineHeight = 20
const contentLineHeight = 18
const iconHeight = 28
const textGap = 8

const nodeColors: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  condition: { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af', icon: '📋' },
  inference: { bg: '#f0fdf4', border: '#22c55e', text: '#166534', icon: '✓' },
  conclusion: { bg: '#dcfce7', border: '#16a34a', text: '#14532d', icon: '🎯' },
  question: { bg: '#fef2f2', border: '#f43f5e', text: '#9f1239', icon: '❓' },
  exploration: { bg: '#fff7ed', border: '#f97316', text: '#9a3412', icon: '?' },
  dead_end: { bg: '#fef2f2', border: '#ef4444', text: '#991b1b', icon: '⚠️' },
}

type NodeSizeMap = Record<string, { width: number; height: number }>

// #region debug-point A:report-helper
const DEBUG_SERVER_URL = 'http://127.0.0.1:7777/event'
const DEBUG_SESSION_ID = 'mindmap-node-clipping'
const DEBUG_RUN_ID = 'post-fix'
const reportDebugEvent = (hypothesisId: string, location: string, msg: string, data: Record<string, unknown>) => {
  fetch(DEBUG_SERVER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: DEBUG_SESSION_ID,
      runId: DEBUG_RUN_ID,
      hypothesisId,
      location,
      msg: `[DEBUG] ${msg}`,
      data,
      ts: Date.now(),
    }),
  }).catch(() => {})
}
// #endregion

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

function estimateWrappedLines(text: string, charsPerLine: number) {
  return text
    .split('\n')
    .reduce((total, line) => total + Math.max(1, Math.ceil(line.length / Math.max(charsPerLine, 1))), 0)
}

function estimateNodeSize(label: string, content: string) {
  const longestLine = Math.max(
    ...[label, content]
      .flatMap((text) => text.split('\n'))
      .map((line) => line.trim().length),
    0
  )
  const width = clamp(longestLine * 7 + nodeHorizontalPadding, minNodeWidth, maxNodeWidth)
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

const FlowViewportSync = ({
  fitViewKey,
  onMeasure,
  containerRef,
}: {
  fitViewKey: string
  onMeasure: (sizes: NodeSizeMap) => void
  containerRef: React.RefObject<HTMLDivElement>
}) => {
  const { fitView, getNodes } = useReactFlow()
  const nodesInitialized = useNodesInitialized()

  useEffect(() => {
    if (!nodesInitialized) {
      return
    }

    requestAnimationFrame(() => {
      const actualSizes = getNodes().reduce<NodeSizeMap>((acc, node) => {
        if (node.width && node.height) {
          acc[node.id] = {
            width: Math.ceil(node.width),
            height: Math.ceil(node.height),
          }
        }
        return acc
      }, {})

      if (Object.keys(actualSizes).length > 0) {
        // #region debug-point B:measured-node-sizes
        const containerRect = containerRef.current?.getBoundingClientRect()
        reportDebugEvent('B', 'DeductionFlow.tsx:150', 'measured node sizes captured', {
          containerWidth: containerRect?.width ?? null,
          containerHeight: containerRect?.height ?? null,
          nodeCount: Object.keys(actualSizes).length,
          sizes: actualSizes,
        })
        // #endregion
        onMeasure(actualSizes)
      }
    })
  }, [nodesInitialized, getNodes, onMeasure, fitViewKey, containerRef])

  useEffect(() => {
    if (!fitViewKey) {
      return
    }

    const containerRect = containerRef.current?.getBoundingClientRect()
    const retries = [0, 80, 220, 500]
    const timers = retries.map((delay, attempt) =>
      window.setTimeout(() => {
        requestAnimationFrame(() => {
          const flowNodes = getNodes().map((node) => ({
            id: node.id,
            x: node.position.x,
            y: node.position.y,
            width: node.width ?? null,
            height: node.height ?? null,
          }))

          // #region debug-point C:before-fitview
          reportDebugEvent('C', 'DeductionFlow.tsx:177', 'fitView retry scheduled', {
            attempt,
            delay,
            nodesInitialized,
            containerWidth: containerRect?.width ?? null,
            containerHeight: containerRect?.height ?? null,
            fitViewKey,
            nodes: flowNodes,
          })
          // #endregion

          if (flowNodes.length > 0) {
            fitView({ padding: 0.32, duration: attempt === 0 ? 0 : 220 })
          }
        })
      }, delay)
    )

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer))
    }
  }, [nodesInitialized, fitViewKey, fitView, getNodes, containerRef])

  return null
}

const DeductionFlow = () => {
  const nodes = useStore((state) => state.deduction.nodes)
  const edges = useStore((state) => state.deduction.edges)
  const [measuredNodeSizes, setMeasuredNodeSizes] = useState<NodeSizeMap>({})
  const containerRef = useRef<HTMLDivElement>(null)

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

  const handleMeasure = useCallback((actualSizes: NodeSizeMap) => {
    setMeasuredNodeSizes((prev) => {
      const prevKeys = Object.keys(prev)
      const nextKeys = Object.keys(actualSizes)
      const isSame =
        prevKeys.length === nextKeys.length &&
        nextKeys.every((key) => {
          const prevSize = prev[key]
          const nextSize = actualSizes[key]
          return prevSize && prevSize.width === nextSize.width && prevSize.height === nextSize.height
        })

      return isSame ? prev : actualSizes
    })
  }, [])

  const fitViewKey = useMemo(
    () =>
      rfNodes
        .map((node) => {
          const size = measuredNodeSizes[node.id] ?? getNodeBox(node)
          return `${node.id}:${Math.round(node.position.x)}:${Math.round(node.position.y)}:${size.width}:${size.height}`
        })
        .join('|'),
    [rfNodes, measuredNodeSizes]
  )

  useEffect(() => {
    // #region debug-point A:layout-summary
    const containerRect = containerRef.current?.getBoundingClientRect()
    reportDebugEvent('A', 'DeductionFlow.tsx:315', 'layout summary updated', {
      containerWidth: containerRect?.width ?? null,
      containerHeight: containerRect?.height ?? null,
      nodeCount: rfNodes.length,
      edgeCount: rfEdges.length,
      nodes: rfNodes.map((node) => {
        const size = measuredNodeSizes[node.id] ?? getNodeBox(node)
        return {
          id: node.id,
          x: node.position.x,
          y: node.position.y,
          width: size.width,
          height: size.height,
        }
      }),
    })
    // #endregion
  }, [rfNodes, rfEdges.length, measuredNodeSizes])

  return (
    <div ref={containerRef} className="flex-1 min-w-0 min-h-0 overflow-hidden">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodeClick={onNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <FlowViewportSync fitViewKey={fitViewKey} onMeasure={handleMeasure} containerRef={containerRef} />
        <Background color="#e2e8f0" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  )
}

export default DeductionFlow
