from models import MindNode, MindEdge, Position, NodeData
import uuid


def parse_problem(problem: str) -> tuple[list[MindNode], list[MindEdge]]:
    nodes = []
    edges = []

    nodes.append(
        MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label="已知条件",
            type="condition",
            position=Position(x=50, y=200),
            data=NodeData(content=f"题目: {problem}", status="active"),
        )
    )

    example_problem = _detect_problem_type(problem)

    if example_problem == "equation":
        step1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step1_id,
                label="步骤1: 分析等式",
                type="inference",
                position=Position(x=300, y=100),
                data=NodeData(
                    content="观察等式两边,找出未知数的位置", status="pending"
                ),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=nodes[0].id, target=step1_id, label="分析"
            )
        )

        step2_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step2_id,
                label="步骤2: 移项化简",
                type="inference",
                position=Position(x=550, y=100),
                data=NodeData(content="将含有未知数的项移到等式一边", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step1_id, target=step2_id, label="推导"
            )
        )

        step3_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step3_id,
                label="步骤3: 求解未知数",
                type="conclusion",
                position=Position(x=800, y=100),
                data=NodeData(content="计算出未知数的值", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step2_id, target=step3_id, label="求解"
            )
        )

        q1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=q1_id,
                label="思考: 第一步做什么?",
                type="question",
                position=Position(x=300, y=350),
                data=NodeData(
                    content="问题: 观察这个方程,你认为第一步应该做什么?",
                    status="pending",
                ),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source=nodes[0].id,
                target=q1_id,
                label="引导",
                animated=True,
            )
        )

    elif example_problem == "geometry":
        step1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step1_id,
                label="步骤1: 识别图形",
                type="inference",
                position=Position(x=300, y=100),
                data=NodeData(content="识别题目中涉及的几何图形及其性质", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=nodes[0].id, target=step1_id, label="分析"
            )
        )

        step2_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step2_id,
                label="步骤2: 应用公式",
                type="inference",
                position=Position(x=550, y=100),
                data=NodeData(content="选择合适的几何公式进行计算", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step1_id, target=step2_id, label="推导"
            )
        )

        step3_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step3_id,
                label="步骤3: 计算结果",
                type="conclusion",
                position=Position(x=800, y=100),
                data=NodeData(content="代入数值,计算出最终结果", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step2_id, target=step3_id, label="求解"
            )
        )

        q1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=q1_id,
                label="思考: 是什么图形?",
                type="question",
                position=Position(x=300, y=350),
                data=NodeData(
                    content="问题: 这道题涉及什么几何图形?它有什么特殊性质?",
                    status="pending",
                ),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source=nodes[0].id,
                target=q1_id,
                label="引导",
                animated=True,
            )
        )

    else:
        step1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step1_id,
                label="步骤1: 理解题意",
                type="inference",
                position=Position(x=300, y=100),
                data=NodeData(content="仔细阅读题目,理解所求内容", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=nodes[0].id, target=step1_id, label="分析"
            )
        )

        step2_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step2_id,
                label="步骤2: 制定策略",
                type="inference",
                position=Position(x=550, y=100),
                data=NodeData(content="思考解题思路,选择合适的方法", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step1_id, target=step2_id, label="推导"
            )
        )

        step3_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=step3_id,
                label="步骤3: 执行求解",
                type="conclusion",
                position=Position(x=800, y=100),
                data=NodeData(content="按照思路进行计算和推理", status="pending"),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}", source=step2_id, target=step3_id, label="求解"
            )
        )

        q1_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(
            MindNode(
                id=q1_id,
                label="思考: 题目要求什么?",
                type="question",
                position=Position(x=300, y=350),
                data=NodeData(
                    content="问题: 仔细阅读题目,你认为题目最终要求的是什么?",
                    status="pending",
                ),
            )
        )
        edges.append(
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source=nodes[0].id,
                target=q1_id,
                label="引导",
                animated=True,
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
