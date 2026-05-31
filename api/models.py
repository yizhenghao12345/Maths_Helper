from pydantic import BaseModel
from typing import Optional


class Position(BaseModel):
    x: float
    y: float


class NodeData(BaseModel):
    content: str
    status: str = "pending"


class MindNode(BaseModel):
    id: str
    label: str
    type: str
    position: Position
    data: NodeData


class MindEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False
    style: Optional[str] = None
    dashed: bool = False


class SubmitProblemRequest(BaseModel):
    problem: str
    problemType: Optional[str] = None
    language: Optional[str] = "zh-CN"


class SubmitProblemResponse(BaseModel):
    sessionId: str
    initialNodes: list[MindNode]
    initialEdges: list[MindEdge]
    firstQuestion: Optional[str] = None
    firstOptions: Optional[list[str]] = None


class QuestionRequest(BaseModel):
    sessionId: str
    userAnswer: str
    currentNodeId: str
    language: Optional[str] = None


class QuestionResponse(BaseModel):
    isCorrect: bool
    feedback: Optional[str] = None
    nextNodes: Optional[list[MindNode]] = None
    nextEdges: Optional[list[MindEdge]] = None
    nextQuestion: Optional[str] = None
    options: Optional[list[str]] = None
    isCompleted: bool = False
    finalSolution: Optional[str] = None
    needsRetreat: bool = False
    retreatMessage: Optional[str] = None
