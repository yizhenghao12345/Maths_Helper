# Debug Session: mindmap-node-clipping
- **Status**: [OPEN]
- **Issue**: 思维导图右侧节点仍被侧栏一侧裁切，未完整显示
- **Debug Server**: http://127.0.0.1:7777/event
- **Log File**: .dbg/trae-debug-log-mindmap-node-clipping.ndjson

## Reproduction Steps
1. 打开“思维推演”页面。
2. 触发右侧出现较长内容的新节点。
3. 观察右侧节点是否被侧栏一侧裁切。

## Hypotheses & Verification
| ID | Hypothesis | Likelihood | Effort | Evidence |
|----|------------|------------|--------|----------|
| A | 左侧画布实际可用宽度比 fitView 计算时更小，右侧侧栏占位未纳入缩放边界 | High | Low | 部分确认：容器宽 896，但日志中最右节点 x=700、width=280，右边界达到 980 |
| B | fitView 执行过早，节点真实宽高尚未稳定 | High | Low | 部分确认：刷新后仅看到布局摘要日志，未看到 fitView 相关日志，疑似首屏缩放未执行或执行时机丢失 |
| C | dagre 使用的节点尺寸与最终渲染尺寸不一致，导致位置偏右 | High | Med | 待确认 |
| D | React Flow 容器或 viewport 存在额外边界/缩放限制 | Med | Med | Pending |
| E | 边标签或阴影扩展了实际包围盒，但布局和缩放未覆盖 | Low | Med | Pending |

## Log Evidence
- `pre-fix` 日志显示容器 `containerWidth=896`。
- 三节点场景中最右节点 `x=700,width=280`，理论右边界约 `980`，已经超过容器宽度。
- 刷新复现场景中已记录到布局摘要，但未采集到 `fitView scheduled` 日志，说明首屏时序存在异常。

## Verification Conclusion
- 初步判断根因偏向“刷新后首屏自动缩放时序不稳定”，而不是单纯节点尺寸估算错误。
