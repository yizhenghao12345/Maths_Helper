# 技术架构文档

## 1. 架构设计

```mermaid
graph TB
    subgraph 前端层
        A[React应用] --> B[ReactFlow节点图]
        A --> C[提问交互组件]
        A --> D[路由管理]
    end
    
    subgraph 后端层
        E[Python FastAPI] --> F[题目解析服务]
        E --> G[思维节点生成服务]
        E --> H[AI对话服务]
    end
    
    subgraph 数据层
        I[临时会话存储]
    end
    
    A -->|HTTP API| E
    H -->|调用| J[大模型API]
    F --> I
    G --> I
```

## 2. 技术说明
- **前端**: React@18 + TypeScript + TailwindCSS + Vite
- **可视化**: ReactFlow@11 用于动态节点图展示
- **状态管理**: Zustand 用于前端状态管理
- **后端**: Python FastAPI 提供RESTful API
- **AI集成**: 通过API调用大语言模型能力
- **路由**: React Router DOM 用于前端路由

## 3. 路由定义
| 路由 | 用途 |
|------|------|
| / | 主页，产品介绍和快速开始 |
| /input | 题目输入页面 |
| /deduction | 思维推演页面，包含节点图和提问面板 |

## 4. API定义

```typescript
// 题目提交接口
interface SubmitProblemRequest {
  problem: string;
  problemType?: string;
}

interface SubmitProblemResponse {
  sessionId: string;
  initialNodes: MindNode[];
  initialEdges: MindEdge[];
}

// 思维节点数据结构
interface MindNode {
  id: string;
  label: string;
  type: 'condition' | 'inference' | 'conclusion' | 'question';
  position: { x: number; y: number };
  data: {
    content: string;
    status: 'pending' | 'active' | 'completed' | 'error';
  };
}

interface MindEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

// 提问交互接口
interface QuestionRequest {
  sessionId: string;
  userAnswer: string;
  currentNodeId: string;
}

interface QuestionResponse {
  isCorrect: boolean;
  feedback?: string;
  nextNodes?: MindNode[];
  nextEdges?: MindEdge[];
  nextQuestion?: string;
  options?: string[];
}
```

## 5. 服务架构图

```mermaid
graph LR
    A[Controller层] --> B[Service层]
    B --> C[Repository层]
    C --> D[内存存储]
    
    A1[ProblemController] --> B1[ProblemParseService]
    A2[DeductionController] --> B2[MindNodeGenerateService]
    A2 --> B3[AIQuestionService]
    
    B1 --> C1
    B2 --> C1
    B3 --> C2
    C2 --> E[外部AI API]
```

## 6. 数据模型

### 6.1 数据模型定义

```mermaid
erDiagram
    SESSION ||--o{ MIND_NODE : contains
    SESSION ||--o{ MIND_EDGE : contains
    SESSION ||--o{ QUESTION : has
    
    SESSION {
        string id PK
        string problem
        datetime created_at
        string status
    }
    
    MIND_NODE {
        string id PK
        string session_id FK
        string label
        string type
        json position
        json data
        string status
    }
    
    MIND_EDGE {
        string id PK
        string session_id FK
        string source_node_id
        string target_node_id
        string label
    }
    
    QUESTION {
        string id PK
        string session_id FK
        string content
        json options
        string correct_answer
        string feedback
    }
```

### 6.2 数据定义
- 会话数据存储在内存中，支持多用户并发
- 每个会话包含独立的节点图和问题序列
- 会话超时自动清理（默认30分钟）
