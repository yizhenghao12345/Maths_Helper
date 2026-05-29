from models import MindNode, MindEdge, Position, NodeData
import uuid
from ai_service import ai_service


async def parse_problem(problem: str) -> tuple[list[MindNode], list[MindEdge]]:
    nodes = []
    edges = []

    nodes.append(
        MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label="题目",
            type="condition",
            position=Position(x=400, y=200),
            data=NodeData(content=f"题目: {problem}", status="active"),
        )
    )

    return nodes, edges


def _detect_problem_type(problem: str) -> str:
    equation_keywords = ["方程", "解方程", "x=", "求x", "等于", "=", "+", "-"]
    geometry_keywords = ["三角形", "圆", "正方形", "长方形", "面积", "周长", "角度", "平行四边形"]

    for keyword in equation_keywords:
        if keyword in problem:
            return "equation"

    for keyword in geometry_keywords:
        if keyword in problem:
            return "geometry"

    return "general"
