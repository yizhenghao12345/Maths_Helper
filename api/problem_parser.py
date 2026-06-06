from models import MindNode, MindEdge, Position, NodeData
import uuid
from ai_service import ai_service
from problem_classifier import detect_problem_type


def _get_problem_text(language: str) -> tuple[str, str]:
    if language == "en-US":
        return "Problem", f"Problem: {{problem}}"
    return "题目", f"题目: {{problem}}"


async def parse_problem(problem: str, language: str = "zh-CN") -> tuple[list[MindNode], list[MindEdge]]:
    nodes = []
    edges = []
    title, content_template = _get_problem_text(language)

    nodes.append(
        MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=title,
            type="condition",
            position=Position(x=400, y=200),
            data=NodeData(content=content_template.format(problem=problem), status="active"),
        )
    )

    return nodes, edges

def _detect_problem_type(problem: str) -> str:
    return detect_problem_type(problem)
