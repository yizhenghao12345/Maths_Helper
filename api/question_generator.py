from typing import Optional
from models import MindNode, MindEdge, QuestionResponse, Position, NodeData
import uuid
from ai_service import ai_service

MAX_CONSECUTIVE_ERRORS = 2


def _adopt_background_parsed_problem(session):
    if getattr(session, "parsed_problem", None) is not None:
        return

    task = getattr(session, "parsed_problem_task", None)
    if task is None or not task.done():
        return

    try:
        session.parsed_problem = task.result()
    except Exception:
        session.parsed_problem = None
    finally:
        session.parsed_problem_task = None


def _get_total_steps(session) -> int:
    """根据 parsed_problem 的 suggested_steps 动态决定总步数，默认 3。"""
    parsed = getattr(session, "parsed_problem", None)
    if isinstance(parsed, dict):
        steps = parsed.get("suggested_steps", [])
        if isinstance(steps, list) and len(steps) >= 2:
            return max(2, min(len(steps), 6))
    return 3


async def generate_question(
    session,
    user_answer: str,
    current_node_id: str,
    current_question_text: Optional[str] = None,
    current_options: Optional[list[str]] = None,
) -> QuestionResponse:
    if not hasattr(session, "consecutive_errors"):
        session.consecutive_errors = 0
    if not hasattr(session, "question_history"):
        session.question_history = []
    if not hasattr(session, "exploration_nodes"):
        session.exploration_nodes = []
    if not hasattr(session, "language"):
        session.language = "zh-CN"
    if not hasattr(session, "current_question_data"):
        session.current_question_data = None
    if not hasattr(session, "parsed_problem_task"):
        session.parsed_problem_task = None

    _adopt_background_parsed_problem(session)

    if ai_service.enabled:
        try:
            return await _generate_ai_question(
                session,
                user_answer,
                current_node_id,
                current_question_text,
                current_options,
                _get_total_steps(session),
            )
        except Exception as e:
            print(f"AI服务调用失败，使用默认逻辑: {e}")
            return _generate_default_question(session, user_answer)

    return _generate_default_question(session, user_answer)


async def _generate_ai_question(
    session,
    user_answer: str,
    current_node_id: str,
    current_question_text: Optional[str] = None,
    current_options: Optional[list[str]] = None,
    total_steps: int = 3,
) -> QuestionResponse:
    language = _get_language(session)
    texts = _get_texts(language)
    current_question = _get_current_question_data(session)
    if current_question is None:
        current_question = await ai_service.generate_socratic_question(
            problem=session.problem,
            history=getattr(session, "question_history", []),
            current_step=session.current_step,
            total_steps=total_steps,
            parsed_problem=getattr(session, "parsed_problem", None),
            language=language,
            current_node_context=_get_current_node_context(session, current_node_id),
            session_id=session.session_id,
        )
        session.current_question_data = current_question

    options = current_question.get("options", ["A", "B", "C", "D"])
    correct_index = current_question.get("correct_index", 0)
    correct_letter = chr(65 + correct_index) if 0 <= correct_index < len(options) else "A"
    selected_option_text = _get_selected_option_text(options, user_answer)

    if user_answer == correct_letter:
        session.consecutive_errors = 0
        session.current_step += 1
        next_step = session.current_step
        success_feedback = current_question.get("success_feedback", texts["default_success_feedback"])
        explanation = current_question.get("explanation", texts["default_explanation"])

        _append_history(
            session,
            question=current_question.get("question", ""),
            answer=user_answer,
            selected_option=selected_option_text,
            feedback=success_feedback,
            is_correct=True,
        )

        new_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=texts["step_label"].format(step=next_step),
            type="inference",
            position=_calculate_position(session, is_correct=True),
            data=NodeData(
                content=texts["correct_node_content"].format(
                    option=selected_option_text,
                    explanation=explanation,
                ),
                status="active",
            ),
        )

        response = QuestionResponse(
            isCorrect=True,
            feedback=success_feedback,
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
                    label=texts["correct_edge_label"],
                    style="#22c55e",
                )
            ]

        if response.isCompleted:
            session.is_completed = True
            session.current_question_data = None
            response.finalSolution = await ai_service.generate_final_solution(
                session.problem,
                session.question_history,
                language=language,
                session_id=session.session_id,
            )
            return response

        next_question = await ai_service.generate_socratic_question(
            problem=session.problem,
            history=session.question_history,
            current_step=session.current_step,
            total_steps=total_steps,
            parsed_problem=getattr(session, "parsed_problem", None),
            language=language,
            current_node_context=_get_node_context_text(new_node),
            session_id=session.session_id,
        )
        session.current_question_data = next_question
        response.nextQuestion = next_question.get("question")
        response.options = next_question.get("options")
        return response

    session.consecutive_errors += 1
    exploration_feedback = current_question.get("error_feedback", texts["default_error_feedback"])
    exploration_node = MindNode(
        id=f"node_{uuid.uuid4().hex[:8]}",
        label=texts["exploration_label"],
        type="exploration",
        position=_calculate_position(session, is_correct=False),
        data=NodeData(
            content=texts["exploration_node_content"].format(
                option=selected_option_text,
                explanation=current_question.get("explanation", texts["default_explanation"]),
            ),
            status="exploration",
        ),
    )

    if session.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
        feedback = exploration_feedback
        _append_history(
            session,
            question=current_question.get("question", ""),
            answer=user_answer,
            selected_option=selected_option_text,
            feedback=feedback,
            is_correct=False,
        )

        dead_end_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=texts["dead_end_label"],
            type="dead_end",
            position=_calculate_position(session, is_correct=False, offset=50),
            data=NodeData(
                content=texts["dead_end_content"].format(feedback=exploration_feedback),
                status="warning",
            ),
        )

        session.consecutive_errors = 0
        next_question = await ai_service.generate_socratic_question(
            problem=session.problem,
            history=session.question_history,
            current_step=session.current_step,
            total_steps=total_steps,
            parsed_problem=getattr(session, "parsed_problem", None),
            language=language,
            current_node_context=_get_node_context_text(dead_end_node),
            session_id=session.session_id,
        )
        session.current_question_data = next_question

        response = QuestionResponse(
            isCorrect=False,
            feedback=feedback,
            needsRetreat=True,
            retreatMessage=texts["retreat_message"],
            nextQuestion=next_question.get("question"),
            options=next_question.get("options"),
            nextNodes=[exploration_node, dead_end_node],
        )
        last_node_id = _get_last_active_node_id(session)
        if last_node_id:
            response.nextEdges = [
                MindEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    source=last_node_id,
                    target=exploration_node.id,
                    label=texts["try_edge_label"],
                    style="#f97316",
                    dashed=True,
                ),
                MindEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    source=exploration_node.id,
                    target=dead_end_node.id,
                    label=texts["blocked_edge_label"],
                    style="#ef4444",
                    dashed=True,
                ),
            ]
        return response

    feedback = texts["exploration_feedback"].format(
        option=selected_option_text,
        hint=exploration_feedback,
    )
    _append_history(
        session,
        question=current_question.get("question", ""),
        answer=user_answer,
        selected_option=selected_option_text,
        feedback=feedback,
        is_correct=False,
    )

    next_question = await ai_service.generate_socratic_question(
        problem=session.problem,
        history=session.question_history,
        current_step=session.current_step,
        total_steps=total_steps,
        parsed_problem=getattr(session, "parsed_problem", None),
        language=language,
        current_node_context=_get_node_context_text(exploration_node),
        session_id=session.session_id,
    )
    session.current_question_data = next_question
    response = QuestionResponse(
        isCorrect=False,
        feedback=feedback,
        nextQuestion=next_question.get("question"),
        options=next_question.get("options"),
        nextNodes=[exploration_node],
    )
    last_node_id = _get_last_active_node_id(session)
    if last_node_id:
        response.nextEdges = [
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source=last_node_id,
                target=exploration_node.id,
                label=texts["explore_edge_label"],
                style="#f97316",
                dashed=True,
            )
        ]
    return response


def _generate_default_question(session, user_answer: str) -> QuestionResponse:
    language = _get_language(session)
    texts = _get_texts(language)
    questions = _get_questions_for_problem(session.problem, language)
    current_step = session.current_step

    if current_step >= len(questions):
        session.is_completed = True
        return QuestionResponse(
            isCorrect=True,
            isCompleted=True,
            finalSolution=_generate_final_solution(session.problem, language),
        )

    question_data = _get_current_question_data(session) or questions[current_step]
    selected_option_text = _get_selected_option_text(question_data["options"], user_answer)
    is_correct = user_answer == question_data["correct"]

    if is_correct:
        session.consecutive_errors = 0
        session.current_step += 1
        next_step = session.current_step

        _append_history(
            session,
            question=question_data["question"],
            answer=user_answer,
            selected_option=selected_option_text,
            feedback=question_data["success_feedback"],
            is_correct=True,
        )

        new_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=texts["step_label"].format(step=next_step),
            type="inference",
            position=_calculate_position(session, is_correct=True),
            data=NodeData(
                content=texts["correct_node_content"].format(
                    option=selected_option_text,
                    explanation=question_data["explanation"],
                ),
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
                    label=texts["correct_edge_label"],
                    style="#22c55e",
                )
            ]

        if response.isCompleted:
            session.is_completed = True
            session.current_question_data = None
            response.finalSolution = _generate_final_solution(session.problem, language)
        elif next_step < len(questions):
            session.current_question_data = questions[next_step]

        return response

    session.consecutive_errors += 1
    exploration_node = MindNode(
        id=f"node_{uuid.uuid4().hex[:8]}",
        label=texts["exploration_label"],
        type="exploration",
        position=_calculate_position(session, is_correct=False),
        data=NodeData(
            content=texts["exploration_node_content"].format(
                option=selected_option_text,
                explanation=question_data["explanation"],
            ),
            status="exploration",
        ),
    )

    if session.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
        feedback = question_data["error_feedback"]
        _append_history(
            session,
            question=question_data["question"],
            answer=user_answer,
            selected_option=selected_option_text,
            feedback=feedback,
            is_correct=False,
        )

        dead_end_node = MindNode(
            id=f"node_{uuid.uuid4().hex[:8]}",
            label=texts["dead_end_label"],
            type="dead_end",
            position=_calculate_position(session, is_correct=False, offset=50),
            data=NodeData(
                content=texts["dead_end_content"].format(feedback=question_data["error_feedback"]),
                status="warning",
            ),
        )

        session.consecutive_errors = 0
        session.current_question_data = question_data
        response = QuestionResponse(
            isCorrect=False,
            feedback=feedback,
            needsRetreat=True,
            retreatMessage=texts["retreat_message"],
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
                    label=texts["try_edge_label"],
                    style="#f97316",
                    dashed=True,
                ),
                MindEdge(
                    id=f"edge_{uuid.uuid4().hex[:8]}",
                    source=exploration_node.id,
                    target=dead_end_node.id,
                    label=texts["blocked_edge_label"],
                    style="#ef4444",
                    dashed=True,
                ),
            ]

        return response

    feedback = texts["exploration_feedback"].format(
        option=selected_option_text,
        hint=question_data["error_feedback"],
    )
    _append_history(
        session,
        question=question_data["question"],
        answer=user_answer,
        selected_option=selected_option_text,
        feedback=feedback,
        is_correct=False,
    )
    response = QuestionResponse(
        isCorrect=False,
        feedback=feedback,
        nextQuestion=question_data["question"],
        options=question_data["options"],
        nextNodes=[exploration_node],
    )
    session.current_question_data = question_data

    last_node_id = _get_last_active_node_id(session)
    if last_node_id:
        response.nextEdges = [
            MindEdge(
                id=f"edge_{uuid.uuid4().hex[:8]}",
                source=last_node_id,
                target=exploration_node.id,
                label=texts["explore_edge_label"],
                style="#f97316",
                dashed=True,
            )
        ]

    return response


def _append_history(session, question: str, answer: str, selected_option: str, feedback: str, is_correct: bool):
    session.question_history.append(
        {
            "question": question,
            "answer": answer,
            "selected_option": selected_option,
            "feedback": feedback,
            "is_correct": is_correct,
        }
    )


def _get_language(session) -> str:
    return getattr(session, "language", "zh-CN") or "zh-CN"


def _get_selected_option_text(options: list[str], answer: str) -> str:
    selected_index = ord(answer) - 65 if answer else -1
    if 0 <= selected_index < len(options):
        return options[selected_index]
    return answer


def _node_attr(node, key: str, default=None):
    if isinstance(node, dict):
        return node.get(key, default)
    return getattr(node, key, default)


def _get_current_question_data(session) -> Optional[dict]:
    data = getattr(session, "current_question_data", None)
    if not isinstance(data, dict):
        return None

    question = data.get("question")
    options = data.get("options")
    if isinstance(question, str) and question and isinstance(options, list) and options:
        return data
    return None


def _get_node_context_text(node) -> str:
    label = _node_attr(node, "label", "")
    data = _node_attr(node, "data", {}) or {}
    if isinstance(data, dict):
        content = data.get("content", "")
    else:
        content = getattr(data, "content", "")
    return f"{label}\n{content}".strip()


def _get_current_node_context(session, current_node_id: str) -> str:
    for node in getattr(session, "nodes", []):
        node_id = _node_attr(node, "id", "")
        if node_id == current_node_id:
            return _get_node_context_text(node)
    return ""


def _calculate_position(session, is_correct: bool, offset: int = 0) -> Position:
    base_step = len([n for n in session.nodes if _node_attr(n, "type", "") in ["inference", "exploration", "dead_end"]])
    base_x = 400 + base_step * 250
    if is_correct:
        return Position(x=base_x, y=150)

    error_offset = session.consecutive_errors * 80 + offset
    return Position(x=base_x + error_offset, y=300 + (base_step // 2) * 200)


def _get_last_active_node_id(session) -> str:
    if session.nodes:
        for node in reversed(session.nodes):
            data = _node_attr(node, "data", {}) or {}
            status = data.get("status") if isinstance(data, dict) else getattr(data, "status", None)
            if status in ["active", "exploration", "warning"]:
                return _node_attr(node, "id", "")
    return _node_attr(session.nodes[0], "id", "") if session.nodes else ""


def _get_texts(language: str) -> dict[str, str]:
    if language == "en-US":
        return {
            "step_label": "Step {step}",
            "exploration_label": "Explore",
            "dead_end_label": "Need To Reframe",
            "correct_edge_label": "Correct",
            "try_edge_label": "Try",
            "explore_edge_label": "Explore",
            "blocked_edge_label": "Blocked",
            "retreat_message": "This direction is getting stuck. That is okay. Let's step back and rethink the key idea.",
            "correct_node_content": "✓ {option}: {explanation}",
            "exploration_node_content": "? {option}: {explanation}",
            "dead_end_content": "This path does not seem to work.\n\n{feedback}\n\nLet's switch perspective and try again:",
            "exploration_feedback": "You chose \"{option}\".\n\n{hint}\n\nLet's trace this idea a bit more.",
            "default_success_feedback": "Good choice. Keep going.",
            "default_error_feedback": "Take another look at the goal and the given information.",
            "default_explanation": "This step helps narrow down the next move.",
        }

    return {
        "step_label": "步骤{step}",
        "exploration_label": "探索",
        "dead_end_label": "⚠ 需要调整方向",
        "correct_edge_label": "正确",
        "try_edge_label": "尝试",
        "explore_edge_label": "探索",
        "blocked_edge_label": "受阻",
        "retreat_message": "这个方向遇到了困难。没关系，探索错误也是学习的一部分。让我们回到正轨重新思考。",
        "correct_node_content": "✓ {option}: {explanation}",
        "exploration_node_content": "? {option}: {explanation}",
        "dead_end_content": "这条路似乎走不通。\n\n{feedback}\n\n让我们换个角度重新思考：",
        "exploration_feedback": "你选择了「{option}」。\n\n{hint}\n\n继续沿着这个思路看看会怎样？",
        "default_success_feedback": "很好，继续思考。",
        "default_error_feedback": "再想想，先回到题目目标和已知条件。",
        "default_explanation": "这一步的关键在于找准下一步思路。",
    }


def _get_questions_for_problem(problem: str, language: str = "zh-CN") -> list[dict]:
    problem_type = _detect_problem_type(problem)
    if language == "en-US":
        if problem_type == "equation":
            return [
                {
                    "question": "Looking at this equation, what should the first step be?",
                    "options": [
                        "A. Calculate randomly right away",
                        "B. Rearrange terms so the unknown is on one side",
                        "C. Ignore the equality and estimate",
                        "D. Give up",
                    ],
                    "correct": "B",
                    "success_feedback": "Good start. Rearranging the equation is the key first move.",
                    "error_feedback": "Think again. Solving an equation usually starts by organizing the two sides.",
                    "explanation": "Collect the terms with the unknown together",
                },
                {
                    "question": "After rearranging, what should happen next?",
                    "options": [
                        "A. Combine like terms to simplify the equation",
                        "B. Copy the problem again",
                        "C. Jump straight to the answer",
                        "D. Switch to another problem",
                    ],
                    "correct": "A",
                    "success_feedback": "Correct. Simplifying makes the relationship clearer.",
                    "error_feedback": "Not yet. The equation still needs to be simplified.",
                    "explanation": "Combine like terms and simplify the expression",
                },
                {
                    "question": "After simplifying, how do we isolate the unknown?",
                    "options": [
                        "A. Guess a number",
                        "B. Divide both sides by the coefficient",
                        "C. Stop here",
                        "D. Write any answer",
                    ],
                    "correct": "B",
                    "success_feedback": "Exactly. That isolates the unknown and gives the answer.",
                    "error_feedback": "Take another look. The final goal is to isolate the unknown.",
                    "explanation": "Solve for the unknown value",
                },
            ]
        if problem_type == "geometry":
            return [
                {
                    "question": "What geometric figure or relationship appears in this problem?",
                    "options": [
                        "A. Guess without reading carefully",
                        "B. Identify the figure and its properties",
                        "C. Ignore the figure and calculate directly",
                        "D. Skip this step",
                    ],
                    "correct": "B",
                    "success_feedback": "Good. Recognizing the figure is the right starting point.",
                    "error_feedback": "Try again. Geometry problems usually begin with identifying the figure.",
                    "explanation": "Identify the shape and its important properties",
                },
                {
                    "question": "After identifying the figure, what should you choose next?",
                    "options": [
                        "A. Pick any formula",
                        "B. Choose a method or formula based on the goal",
                        "C. Estimate without a formula",
                        "D. Give up",
                    ],
                    "correct": "B",
                    "success_feedback": "Correct. Matching the method to the goal is essential.",
                    "error_feedback": "Slow down. The method should match what the problem asks for.",
                    "explanation": "Choose the most suitable formula or approach",
                },
                {
                    "question": "When substituting values, what should you pay attention to?",
                    "options": [
                        "A. Nothing in particular",
                        "B. Units and calculation accuracy",
                        "C. Rough guessing only",
                        "D. Skip the calculation",
                    ],
                    "correct": "B",
                    "success_feedback": "Exactly. Careful substitution prevents avoidable mistakes.",
                    "error_feedback": "Think again. Details like units and precision matter here.",
                    "explanation": "Substitute values carefully and compute accurately",
                },
            ]
        return [
            {
                "question": "After reading the problem carefully, what is the exact goal?",
                "options": [
                    "A. I did not really read it",
                    "B. Identify clearly what needs to be found",
                    "C. Guess randomly",
                    "D. Stop trying",
                ],
                "correct": "B",
                "success_feedback": "Good. Clarifying the goal is always a strong first step.",
                "error_feedback": "Start from the basics. First make sure you know what the problem asks for.",
                "explanation": "Understand the problem and clarify the target",
            },
            {
                "question": "Based on the conditions, what kind of strategy fits best?",
                "options": [
                    "A. Compute immediately",
                    "B. Analyze the conditions and choose a strategy",
                    "C. Ask someone else first",
                    "D. Give up",
                ],
                "correct": "B",
                "success_feedback": "Correct. A good strategy makes the rest of the work easier.",
                "error_feedback": "Think again. The conditions should guide your method.",
                "explanation": "Choose a strategy from the given information",
            },
            {
                "question": "How should the solving process be carried out?",
                "options": [
                    "A. Skip the process",
                    "B. Reason through it step by step",
                    "C. Stop here",
                    "D. Write anything",
                ],
                "correct": "B",
                "success_feedback": "Exactly. Step-by-step reasoning leads to a reliable answer.",
                "error_feedback": "Try again. A clear process matters as much as the answer.",
                "explanation": "Carry out the solution through orderly reasoning",
            },
        ]

    if problem_type == "equation":
        return [
            {
                "question": "观察这个方程，你认为第一步应该做什么？",
                "options": [
                    "A. 直接计算结果",
                    "B. 移项，把含未知数的项移到一边",
                    "C. 忽略等式，随便算",
                    "D. 放弃不做",
                ],
                "correct": "B",
                "success_feedback": "很好。移项是解方程的重要第一步。",
                "error_feedback": "再想想。解方程时通常要先整理等式。",
                "explanation": "将含有未知数的项集中处理",
            },
            {
                "question": "移项后，下一步应该做什么？",
                "options": [
                    "A. 合并同类项，化简等式",
                    "B. 重新抄一遍题目",
                    "C. 直接写出答案",
                    "D. 换个题目做",
                ],
                "correct": "A",
                "success_feedback": "正确。化简能让等式关系更清晰。",
                "error_feedback": "别着急，还需要进一步整理。",
                "explanation": "合并同类项并化简表达式",
            },
            {
                "question": "化简后，如何求出未知数？",
                "options": [
                    "A. 猜一个数字",
                    "B. 两边同时除以系数",
                    "C. 不用求了",
                    "D. 随便写答案",
                ],
                "correct": "B",
                "success_feedback": "太棒了。这样就能得到最终答案。",
                "error_feedback": "再思考一下。目标是把未知数单独留下。",
                "explanation": "求解未知数的值",
            },
        ]
    if problem_type == "geometry":
        return [
            {
                "question": "这道题涉及什么几何图形或关系？",
                "options": [
                    "A. 随意猜测",
                    "B. 识别图形和性质",
                    "C. 不管图形直接算",
                    "D. 跳过这步",
                ],
                "correct": "B",
                "success_feedback": "很好。认清图形是关键起点。",
                "error_feedback": "想想看。几何题通常先要识别图形和性质。",
                "explanation": "识别几何图形及其重要性质",
            },
            {
                "question": "确定图形后，下一步应该选什么方法？",
                "options": [
                    "A. 随便选公式",
                    "B. 根据所求选择公式或方法",
                    "C. 不用公式直接目测",
                    "D. 放弃",
                ],
                "correct": "B",
                "success_feedback": "正确。方法要和题目目标匹配。",
                "error_feedback": "别急。先想想题目要求你求什么。",
                "explanation": "选择合适的解题公式或方法",
            },
            {
                "question": "代入数值计算时需要注意什么？",
                "options": [
                    "A. 不用注意",
                    "B. 注意单位和计算精度",
                    "C. 大概估算就行",
                    "D. 不计算了",
                ],
                "correct": "B",
                "success_feedback": "非常棒。细心处理细节很重要。",
                "error_feedback": "再想想。单位和计算准确性会影响结果。",
                "explanation": "认真代入数值并准确计算",
            },
        ]
    return [
        {
            "question": "仔细阅读题目后，最终要求是什么？",
            "options": [
                "A. 没认真看题",
                "B. 先明确所求目标",
                "C. 随便猜一个结果",
                "D. 不做了",
            ],
            "correct": "B",
            "success_feedback": "很好。明确目标是第一步。",
            "error_feedback": "没关系，先回到题意，明确题目到底在问什么。",
            "explanation": "理解题意并明确目标",
        },
        {
            "question": "根据题目条件，接下来该用什么策略？",
            "options": [
                "A. 直接算",
                "B. 分析条件后选择策略",
                "C. 先问别人",
                "D. 放弃",
            ],
            "correct": "B",
            "success_feedback": "正确。策略选对了，后面会顺很多。",
            "error_feedback": "再想想。题目条件会提示你该怎么做。",
            "explanation": "根据条件制定解题策略",
        },
        {
            "question": "真正开始求解时，过程应该怎样展开？",
            "options": [
                "A. 跳过过程",
                "B. 按步骤推理并求解",
                "C. 不做了",
                "D. 随便写答案",
            ],
            "correct": "B",
            "success_feedback": "太棒了。清晰的步骤能让答案更可靠。",
            "error_feedback": "再想想。解题过程本身也很重要。",
            "explanation": "按步骤展开推理并完成求解",
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


def _generate_final_solution(problem: str, language: str = "zh-CN") -> str:
    problem_type = _detect_problem_type(problem)
    if language == "en-US":
        if problem_type == "equation":
            return f"""Solution Review:\n\nProblem: {problem}\n\nYour reasoning path is shown on the left.\n\nKey steps:\n1. Identify the equation structure\n2. Rearrange the terms\n3. Simplify and solve\n\nRemember: the core idea in solving equations is to keep both sides balanced by applying the same operation to each side.\n\nYour detours also contain valuable learning signals."""
        if problem_type == "geometry":
            return f"""Solution Review:\n\nProblem: {problem}\n\nYour reasoning path is shown on the left.\n\nKey steps:\n1. Identify the geometric figure\n2. Recall the relevant formula or property\n3. Substitute values and compute carefully\n\nRemember: geometry problems become easier once the figure and its properties are clear.\n\nExploring different paths helps deepen understanding."""
        return f"""Solution Review:\n\nProblem: {problem}\n\nYour reasoning path is shown on the left.\n\nKey steps:\n1. Understand the task\n2. Analyze the given conditions\n3. Choose a strategy\n4. Carry out the solution step by step\n\nRemember: a clear reasoning path matters more than rushing to an answer.\n\nEach attempt helps strengthen your mathematical thinking."""

    if problem_type == "equation":
        return f"""完整解题回顾：\n\n题目：{problem}\n\n你的思考路径已记录在左侧图中。\n\n关键步骤：\n1. 识别方程结构\n2. 移项整理\n3. 化简求解\n\n记住：解方程的核心是保持等式平衡，每一步都要在两边进行相同操作。\n\n你在探索中遇到的弯路也是宝贵的学习经验。"""
    if problem_type == "geometry":
        return f"""完整解题回顾：\n\n题目：{problem}\n\n你的思考路径已记录在左侧图中。\n\n关键步骤：\n1. 识别几何图形\n2. 回忆相关公式或性质\n3. 代入计算\n\n记住：几何题要先认清图形特征，再选择合适的方法。\n\n探索不同思路能帮你更深刻地理解问题。"""
    return f"""完整解题回顾：\n\n题目：{problem}\n\n你的思考路径已记录在左侧图中。\n\n关键步骤：\n1. 理解题意\n2. 分析条件\n3. 制定策略\n4. 执行求解\n\n记住：清晰的思维路径比快速得到答案更重要。\n\n你的每一次思考尝试都是有价值的。"""
