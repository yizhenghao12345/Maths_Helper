from models import MindNode, MindEdge, QuestionResponse, Position, NodeData
import uuid


def generate_question(session, user_answer: str, current_node_id: str) -> QuestionResponse:
    current_step = session.current_step

    questions = _get_questions_for_problem(session.problem)

    if current_step >= len(questions):
        return QuestionResponse(
            isCorrect=True,
            isCompleted=True,
            finalSolution=_generate_final_solution(session.problem),
        )

    question_data = questions[current_step]
    is_correct = user_answer == question_data["correct"]

    if is_correct:
        session.current_step += 1
        next_step = session.current_step

        response = QuestionResponse(
            isCorrect=True,
            feedback=question_data["success_feedback"],
            nextQuestion=questions[next_step]["question"] if next_step < len(questions) else None,
            options=questions[next_step]["options"] if next_step < len(questions) else None,
            isCompleted=next_step >= len(questions),
        )

        if next_step < len(questions):
            new_node = MindNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                label=f"步骤{next_step + 1}",
                type="inference",
                position=Position(x=300 + next_step * 250, y=100),
                data=NodeData(content=questions[next_step]["explanation"], status="active"),
            )
            response.nextNodes = [new_node]

            last_node_id = session.nodes[-1].id if session.nodes else ""
            if last_node_id:
                response.nextEdges = [
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=last_node_id,
                        target=new_node.id,
                        label="推导",
                    )
                ]

        if next_step >= len(questions):
            response.isCompleted = True
            response.finalSolution = _generate_final_solution(session.problem)

        return response
    else:
        return QuestionResponse(
            isCorrect=False,
            feedback=question_data["error_feedback"],
            nextQuestion=question_data["question"],
            options=question_data["options"],
        )


def _get_questions_for_problem(problem: str) -> list[dict]:
    problem_type = _detect_problem_type(problem)

    if problem_type == "equation":
        return [
            {
                "question": "观察这个方程,你认为第一步应该做什么?",
                "options": [
                    "A. 直接计算结果",
                    "B. 移项,把含未知数的项移到一边",
                    "C. 忽略等式,随便算",
                    "D. 放弃不做",
                ],
                "correct": "B",
                "success_feedback": "很好!移项是解方程的重要第一步。接下来我们需要化简等式。",
                "error_feedback": "再想想看~ 解方程时,我们通常要把含有未知数的项集中到等式的一边,这样更容易求解。",
                "explanation": "将含有未知数的项移到等式一边,常数项移到另一边",
            },
            {
                "question": "移项后,下一步应该做什么?",
                "options": [
                    "A. 合并同类项,化简等式",
                    "B. 重新抄一遍题目",
                    "C. 直接写出答案",
                    "D. 换个题目做",
                ],
                "correct": "A",
                "success_feedback": "正确!合并同类项后,等式会变得更简洁。",
                "error_feedback": "别着急~ 移项后我们需要合并同类项,让等式变得更简单清晰。",
                "explanation": "合并同类项,化简等式两边",
            },
            {
                "question": "化简后,如何求出未知数的值?",
                "options": [
                    "A. 猜一个数字",
                    "B. 两边同时除以未知数的系数",
                    "C. 不用求了",
                    "D. 随便写一个答案",
                ],
                "correct": "B",
                "success_feedback": "太棒了!通过两边同时除以系数,就能得到未知数的值。",
                "error_feedback": "再思考一下~ 要得到未知数的值,我们需要让未知数单独在等式一边。",
                "explanation": "两边同时除以未知数的系数,得到最终答案",
            },
        ]
    elif problem_type == "geometry":
        return [
            {
                "question": "这道题涉及什么几何图形?它有什么特殊性质?",
                "options": [
                    "A. 随意猜测",
                    "B. 识别图形,回忆相关性质和公式",
                    "C. 不管图形直接算",
                    "D. 跳过这步",
                ],
                "correct": "B",
                "success_feedback": "很好!识别图形并了解其性质是解几何题的关键。",
                "error_feedback": "想想看~ 不同的几何图形有不同的性质和公式,先认清图形很重要。",
                "explanation": "识别题目中的几何图形,回忆相关的性质和计算公式",
            },
            {
                "question": "确定图形后,应该选择什么公式?",
                "options": [
                    "A. 随便选一个公式",
                    "B. 根据所求量选择合适的公式",
                    "C. 不用公式,目测",
                    "D. 放弃",
                ],
                "correct": "B",
                "success_feedback": "正确!选择合适的公式能让解题事半功倍。",
                "error_feedback": "别急~ 根据题目要求(求面积、周长等)选择对应的公式。",
                "explanation": "根据题目所求,选择合适的几何公式",
            },
            {
                "question": "代入数值计算时,需要注意什么?",
                "options": [
                    "A. 不用注意,直接写答案",
                    "B. 注意单位换算和计算精度",
                    "C. 大概估算就行",
                    "D. 不计算了",
                ],
                "correct": "B",
                "success_feedback": "非常棒!注意单位换算和计算精度是保证答案正确的关键。",
                "error_feedback": "再想想~ 计算时要注意单位是否统一,计算过程要仔细。",
                "explanation": "代入已知数值,注意单位换算,仔细计算出结果",
            },
        ]
    else:
        return [
            {
                "question": "仔细阅读题目,你认为题目最终要求的是什么?",
                "options": [
                    "A. 没看题目",
                    "B. 明确题目所求,找出已知和未知的关系",
                    "C. 随便猜一个",
                    "D. 不做了",
                ],
                "correct": "B",
                "success_feedback": "很好!明确所求是解题的第一步。",
                "error_feedback": "没关系~ 先仔细阅读题目,找出题目要求我们求什么。",
                "explanation": "理解题意,明确已知条件和所求目标",
            },
            {
                "question": "根据题目,你打算用什么方法来解决?",
                "options": [
                    "A. 不用方法,直接算",
                    "B. 分析已知条件,选择合适的解题策略",
                    "C. 问别人",
                    "D. 放弃",
                ],
                "correct": "B",
                "success_feedback": "正确!好的解题策略能让问题迎刃而解。",
                "error_feedback": "想想看~ 根据已知条件,思考可以用哪些方法来解决这个问题。",
                "explanation": "分析已知条件,制定解题策略",
            },
            {
                "question": "按照策略,如何执行具体的求解过程?",
                "options": [
                    "A. 跳过过程写答案",
                    "B. 按照思路一步步计算推理",
                    "C. 不做了",
                    "D. 随便写写",
                ],
                "correct": "B",
                "success_feedback": "太棒了!按步骤执行是得到正确答案的关键。",
                "error_feedback": "再想想~ 按照之前制定的策略,一步步进行计算和推理。",
                "explanation": "按照解题策略,逐步进行计算和推理",
            },
        ]


def _detect_problem_type(problem: str) -> str:
    equation_keywords = ["方程", "解方程", "x=", "求x", "等于", "="]
    geometry_keywords = ["三角形", "圆", "正方形", "长方形", "面积", "周长", "角度"]

    for keyword in equation_keywords:
        if keyword in problem:
            return "equation"

    for keyword in geometry_keywords:
        if keyword in problem:
            return "geometry"

    return "general"


def _generate_final_solution(problem: str) -> str:
    problem_type = _detect_problem_type(problem)

    if problem_type == "equation":
        return f"完整解题思路:\n1. 分析方程: {problem}\n2. 移项,将含未知数的项移到一边\n3. 合并同类项,化简等式\n4. 求解未知数,得到最终答案\n\n记住: 解方程的关键是保持等式平衡,每一步都要在等式两边同时进行相同的操作。"
    elif problem_type == "geometry":
        return f"完整解题思路:\n1. 识别题目中的几何图形\n2. 回忆该图形的性质和相关公式\n3. 根据所求选择合适的公式\n4. 代入已知数值进行计算\n5. 注意单位换算,得出最终结果\n\n记住: 解几何题要先认清图形,再选择合适的公式。"
    else:
        return f"完整解题思路:\n1. 理解题意: {problem}\n2. 分析已知条件和所求\n3. 制定解题策略\n4. 按步骤执行求解\n5. 检查答案是否合理\n\n记住: 解题的关键是理解题意,制定清晰的解题策略。"


class Position:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class NodeData:
    def __init__(self, content: str, status: str = "pending"):
        self.content = content
        self.status = status
