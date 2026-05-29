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


class SubmitProblemResponse(BaseModel):
    sessionId: str
    initialNodes: list[MindNode]
    initialEdges: list[MindEdge]


class QuestionRequest(BaseModel):
    sessionId: str
    userAnswer: str
    currentNodeId: str


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
