from models import MindNode, MindEdge, QuestionResponse, Position, NodeData
import uuid
from ai_service import ai_service

MAX_CONSECUTIVE_ERRORS = 2


async def generate_question(session, user_answer: str, current_node_id: str) -> QuestionResponse:

    if not hasattr(session, 'consecutive_errors'):
        session.consecutive_errors = 0
    if not hasattr(session, 'question_history'):
        session.question_history = []
    if not hasattr(session, 'exploration_nodes'):
        session.exploration_nodes = []

    if ai_service.enabled:
        try:
            return await _generate_ai_question(session, user_answer, current_node_id)
        except Exception as e:
            print(f"AI服务调用失败，使用默认逻辑: {e}")
            return _generate_default_question(session, user_answer)
    else:
        return _generate_default_question(session, user_answer)


async def _generate_ai_question(
    session,
    user_answer: str,
    current_node_id: str,
) -> QuestionResponse:
    history = getattr(session, 'question_history', [])
    total_steps = 3

    question_data = await ai_service.generate_socratic_question(
        problem=session.problem,
        history=history,
        current_step=session.current_step,
        total_steps=total_steps,
        parsed_problem=getattr(session, 'parsed_problem', None),
        session_id=session.session_id,
    )

    correct_index = question_data.get("correct_index", 0)
    options = question_data.get("options", ["A", "B", "C", "D"])
    correct_letter = chr(65 + correct_index) if 0 <= correct_index < 4 else "A"

    is_correct = user_answer == correct_letter

    if is_correct:
        session.consecutive_errors = 0
        session.current_step += 1
        next_step = session.current_step

        selected_option_text = options[correct_index] if correct_index < len(options) else ""

        session.question_history.append({
            "question": question_data["question"],
            "answer": user_answer,
            "selected_option": selected_option_text,
            "feedback": question_data["success_feedback"],
            "is_correct": True,
        })

        new_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=f"步骤{next_step}",
            type="inference",
            position=_calculate_position(session, is_correct=True),
            data=NodeData(
                content=f"✓ {selected_option_text}: {question_data['explanation']}",
                status="active",
            ),
        )

        response = QuestionResponse(
            isCorrect=True,
            feedback=question_data["success_feedback"],
            nextQuestion=None,
            options=None,
            isCompleted=next_step >= total_steps,
            nextNodes=[new_node],
        )

        last_node_id = _get_last_active_node_id(session)
        if last_node_id:
            response.nextEdges = [
                MindEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    source=last_node_id,
                    target=new_node.id,
                    label="正确",
                    style="#22c55e",
                )
            ]

        if next_step >= total_steps:
            solution = await ai_service.generate_final_solution(
                session.problem, session.question_history, session_id=session.session_id
            )
            response.isCompleted = True
            response.finalSolution = solution

        return response
    else:
        session.consecutive_errors += 1

        selected_index = ord(user_answer) - 65 if user_answer else 0
        selected_option_text = options[selected_index] if 0 <= selected_index < len(options) else user_answer

        exploration_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label="探索",
            type="exploration",
            position=_calculate_position(session, is_correct=False),
            data=NodeData(
                content=f"? {selected_option_text}: {question_data.get('explanation', '探索这条思路')}",
                status="exploration",
            ),
        )

        if session.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:

            dead_end_node = MindNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                label="⚠ 需要调整方向",
                type="dead_end",
                position=_calculate_position(session, is_correct=False, offset=50),
                data=NodeData(
                    content=f"这条路似乎走不通哦~\n\n{question_data['error_feedback']}\n\n让我们换个角度重新思考:",
                    status="warning",
                ),
            )

            session.consecutive_errors = 0

            response = QuestionResponse(
                isCorrect=False,
                feedback=question_data["error_feedback"],
                needsRetreat=True,
                retreatMessage=f"看起来这个方向遇到了困难。没关系，探索错误也是学习的一部分！让我们回到正轨：",
                nextQuestion=question_data["question"],
                options=options,
                nextNodes=[exploration_node, dead_end_node],
            )

            last_node_id = _get_last_active_node_id(session)
            if last_node_id:
                response.nextEdges = [
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=last_node_id,
                        target=exploration_node.id,
                        label="尝试",
                        style="#f97316",
                        dashed=True,
                    ),
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=exploration_node.id,
                        target=dead_end_node.id,
                        label="受阻",
                        style="#ef4444",
                        dashed=True,
                    ),
                ]

            return response
        else:

            hint = f"你选择了「{selected_option_text}」。\n\n{question_data['error_feedback']}\n\n继续沿着这个思路看看会怎样？"

            response = QuestionResponse(
                isCorrect=False,
                feedback=hint,
                nextQuestion=question_data["question"],
                options=options,
                nextNodes=[exploration_node],
            )

            last_node_id = _get_last_active_node_id(session)
            if last_node_id:
                response.nextEdges = [
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=last_node_id,
                        target=exploration_node.id,
                        label="探索",
                        style="#f97316",
                        dashed=True,
                    )
                ]

            return response


def _generate_default_question(
    session,
    user_answer: str,
) -> QuestionResponse:
    questions = _get_questions_for_problem(session.problem)

    if not hasattr(session, 'consecutive_errors'):
        session.consecutive_errors = 0
    if not hasattr(session, 'question_history'):
        session.question_history = []

    current_step = session.current_step

    if current_step >= len(questions):
        return QuestionResponse(
            isCorrect=True,
            isCompleted=True,
            finalSolution=_generate_final_solution(session.problem),
        )

    question_data = questions[current_step]
    is_correct = user_answer == question_data["correct"]

    if is_correct:
        session.consecutive_errors = 0
        session.current_step += 1
        next_step = session.current_step

        session.question_history.append({
            "question": question_data["question"],
            "answer": user_answer,
            "is_correct": True,
        })

        new_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=f"步骤{next_step}",
            type="inference",
            position=_calculate_position(session, is_correct=True),
            data=NodeData(
                content=f"✓ {question_data['explanation']}",
                status="active",
            ),
        )

        response = QuestionResponse(
            isCorrect=True,
            feedback=question_data["success_feedback"],
            nextQuestion=questions[next_step]["question"] if next_step < len(questions) else None,
            options=questions[next_step]["options"] if next_step < len(questions) else None,
            isCompleted=next_step >= len(questions),
            nextNodes=[new_node],
        )

        last_node_id = _get_last_active_node_id(session)
        if last_node_id:
            response.nextEdges = [
                MindEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    source=last_node_id,
                    target=new_node.id,
                    label="正确",
                    style="#22c55e",
                )
            ]

        if next_step >= len(questions):
            response.isCompleted = True
            response.finalSolution = _generate_final_solution(session.problem)

        return response
    else:
        session.consecutive_errors += 1

        exploration_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label="探索",
            type="exploration",
            position=_calculate_position(session, is_correct=False),
            data=NodeData(
                content=f"? 尝试: {user_answer}",
                status="exploration",
            ),
        )

        if session.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:

            dead_end_node = MindNode(
                id=f"node_{uuid.uuid4().hex[:8]}",
                label="⚠ 调整方向",
                type="dead_end",
                position=_calculate_position(session, is_correct=False, offset=50),
                data=NodeData(
                    content=f"这条路走不通~\n\n{question_data['error_feedback']}\n\n让我们换个思路:",
                    status="warning",
                ),
            )

            session.consecutive_errors = 0

            response = QuestionResponse(
                isCorrect=False,
                feedback=question_data["error_feedback"],
                needsRetreat=True,
                retreatMessage="这个方向遇到了困难。没关系，让我们重新思考！",
                nextQuestion=question_data["question"],
                options=question_data["options"],
                nextNodes=[exploration_node, dead_end_node],
            )

            last_node_id = _get_last_active_node_id(session)
            if last_node_id:
                response.nextEdges = [
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=last_node_id,
                        target=exploration_node.id,
                        label="尝试",
                        style="#f97316",
                        dashed=True,
                    ),
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=exploration_node.id,
                        target=dead_end_node.id,
                        label="受阻",
                        style="#ef4444",
                        dashed=True,
                    ),
                ]

            return response
        else:

            response = QuestionResponse(
                isCorrect=False,
                feedback=f"你选择了 {user_answer}。{question_data['error_feedback']}\n\n继续看看？",
                nextQuestion=question_data["question"],
                options=question_data["options"],
                nextNodes=[exploration_node],
            )

            last_node_id = _get_last_active_node_id(session)
            if last_node_id:
                response.nextEdges = [
                    MindEdge(
                        id=f"edge_{uuid.uuid4().hex[:8]}",
                        source=last_node_id,
                        target=exploration_node.id,
                        label="探索",
                        style="#f97316",
                        dashed=True,
                    )
                ]

            return response


def _calculate_position(session, is_correct: bool, offset: int = 0) -> Position:
    base_step = len([n for n in session.nodes if n.type in ['inference', 'exploration', 'dead_end']])
    base_x = 400 + base_step * 250
    if is_correct:
        return Position(x=base_x, y=150)
    else:
        error_offset = session.consecutive_errors * 80 + offset
        return Position(x=base_x + error_offset, y=300 + (base_step // 2) * 200)


def _get_last_active_node_id(session) -> str:
    if session.nodes:
        for node in reversed(session.nodes):
            if node.data.status in ["active", "exploration", "warning"]:
                return node.id
    return session.nodes[0].id if session.nodes else ""


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
                "success_feedback": "很好!移项是解方程的重要第一步。",
                "error_feedback": "再想想看~ 解方程时需要整理等式。",
                "explanation": "将含有未知数的项集中处理",
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
                "success_feedback": "正确!化简让等式更清晰。",
                "error_feedback": "别着急~ 还需要进一步整理。",
                "explanation": "合并同类项,化简表达式",
            },
            {
                "question": "化简后,如何求出未知数?",
                "options": [
                    "A. 猜一个数字",
                    "B. 两边同时除以系数",
                    "C. 不用求了",
                    "D. 随便写答案",
                ],
                "correct": "B",
                "success_feedback": "太棒了!得到最终答案。",
                "error_feedback": "再思考一下~ 需要隔离出未知数。",
                "explanation": "求解未知数的值",
            },
        ]
    elif problem_type == "geometry":
        return [
            {
                "question": "这道题涉及什么几何图形?",
                "options": [
                    "A. 随意猜测",
                    "B. 识别图形和性质",
                    "C. 不管图形直接算",
                    "D. 跳过这步",
                ],
                "correct": "B",
                "success_feedback": "很好!认清图形是关键。",
                "error_feedback": "想想看~ 先要识别图形。",
                "explanation": "识别几何图形及其性质",
            },
            {
                "question": "确定图形后,选择什么方法?",
                "options": [
                    "A. 随便选公式",
                    "B. 根据所求选择公式",
                    "C. 不用公式目测",
                    "D. 放弃",
                ],
                "correct": "B",
                "success_feedback": "正确!选对公式事半功倍。",
                "error_feedback": "别急~ 要匹配题目要求。",
                "explanation": "选择合适的解题公式",
            },
            {
                "question": "代入数值时注意什么?",
                "options": [
                    "A. 不用注意",
                    "B. 注意单位和精度",
                    "C. 大概估算",
                    "D. 不计算了",
                ],
                "correct": "B",
                "success_feedback": "非常棒!细心很重要。",
                "error_feedback": "再想想~ 计算要注意细节。",
                "explanation": "代入数值并计算结果",
            },
        ]
    else:
        return [
            {
                "question": "仔细阅读题目,最终要求是什么?",
                "options": [
                    "A. 没看题目",
                    "B. 明确所求目标",
                    "C. 随便猜",
                    "D. 不做了",
                ],
                "correct": "B",
                "success_feedback": "很好!明确目标是第一步。",
                "error_feedback": "没关系~ 先理解题意。",
                "explanation": "理解题意,明确目标",
            },
            {
                "question": "根据题目,打算用什么方法?",
                "options": [
                    "A. 直接算",
                    "B. 分析条件选策略",
                    "C. 问别人",
                    "D. 放弃",
                ],
                "correct": "B",
                "success_feedback": "正确!策略很重要。",
                "error_feedback": "想想看~ 如何着手？",
                "explanation": "制定解题策略",
            },
            {
                "question": "如何执行求解过程?",
                "options": [
                    "A. 跳过过程",
                    "B. 按步骤推理",
                    "C. 不做了",
                    "D. 随便写",
                ],
                "correct": "B",
                "success_feedback": "太棒了!按步执行。",
                "error_feedback": "再想想~ 要有步骤。",
                "explanation": "逐步执行求解",
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
        return f"""完整解题回顾:\n\n题目: {problem}\n\n你的思考路径已记录在左侧图中。
\n关键步骤:
1. 识别方程类型
2. 移项整理
3. 化简求解\n\n记住: 解方程的核心是保持等式平衡，每一步都要在两边进行相同操作。
\n💡 你在探索中遇到的弯路也是宝贵的学习经验！"""
    elif problem_type == "geometry":
        return f"""完整解题回顾:\n\n题目: {problem}\n\n你的思考路径已记录在左侧图中。

关键步骤:
1. 识别几何图形
2. 回忆相关公式
3. 代入计算\n\n记住: 几何题要先认清图形特征，再选择合适的方法。

💡 探索不同思路能帮你更深刻地理解问题！"""
    else:
        return f"""完整解题回顾:\n\n题目: {problem}\n\n你的思考路径已记录在左侧图中。

关键步骤:
1. 理解题意
2. 分析条件
3. 制定策略
4. 执行求解\n\n记住: 清晰的思维路径比快速得到答案更重要。

💡 你的每一次思考尝试都是有价值的！"""
