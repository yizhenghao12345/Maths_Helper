import os
import json
import time
import httpx

import db


def mask_api_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "***" if key else ""
    return f"{key[:4]}...{key[-4:]}"


def _content_to_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _extract_chat_preview(data: dict) -> tuple[str, str]:
    raw_preview = json.dumps(data, ensure_ascii=False)[:1000]
    choices = data.get("choices") or []
    if choices:
        choice = choices[0] or {}
        message = choice.get("message") or {}
        preview = (
            _content_to_text(message.get("content"))
            or _content_to_text(message.get("reasoning_content"))
            or _content_to_text(choice.get("text"))
        ).strip()
        return preview[:200], raw_preview
    preview = (
        _content_to_text(data.get("output_text"))
        or _content_to_text(data.get("result"))
        or _content_to_text(data.get("text"))
    ).strip()
    return preview[:200], raw_preview


PROVIDER_PRESETS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-long"],
    },
    "baidu": {
        "name": "百度文心 (Baidu)",
        "base_url": "https://aip.baidubce.com",
        "models": ["ernie-bot-4", "ernie-bot-turbo", "ernie-bot"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-v4-flash", "deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
    },
    "minimax": {
        "name": "MiniMax",
        "base_url": "https://api.minimaxi.com/v1",
        "models": ["MiniMax-M3", "MiniMax-M2.7-highspeed", "MiniMax-M2.5"],
    },
    "zhipu": {
        "name": "智谱AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-plus", "glm-4", "glm-4-flash", "glm-3-turbo"],
    },
    "custom": {
        "name": "自定义 (Custom)",
        "base_url": "",
        "models": [],
    },
}


def _is_english(language: str) -> bool:
    return language == "en-US"


# 提问类型池：按步骤轮换，避免每步都问"下一步做什么"。
QUESTION_TYPES_ZH = [
    ("判断方向", "问学生当前应优先关注哪个方向或信息，让其在几个合理策略中权衡取舍。"),
    ("识别错误", "给出几个看似可行的思路，让学生找出其中存在问题或会走入死路的那一个。"),
    ("预测结果", "假设采用某种操作，问学生这样做之后会得到什么、或会遇到什么障碍。"),
    ("补全推理", "给出一条已经进行到一半的推理链，让学生补上其中缺失的关键一步。"),
    ("比较方案", "给出两到三种不同的处理方式，让学生判断哪种更合适或哪些本质等价。"),
]

QUESTION_TYPES_EN = [
    ("choose direction", "Ask which information or strategy to prioritize now, weighing several reasonable options."),
    ("spot the flaw", "Present a few plausible-looking ideas and ask the student to find the one that is flawed or leads to a dead end."),
    ("predict outcome", "Assume a particular operation is taken and ask what result or obstacle it leads to."),
    ("complete reasoning", "Give a half-finished reasoning chain and ask the student to fill in the missing key step."),
    ("compare approaches", "Offer two or three different approaches and ask which is more suitable or which are essentially equivalent."),
]


def _pick_question_type(current_step: int, english: bool) -> tuple[str, str]:
    """第一步固定用'判断方向'，之后按步骤轮换提问类型。"""
    pool = QUESTION_TYPES_EN if english else QUESTION_TYPES_ZH
    if current_step <= 0:
        return pool[0]
    return pool[current_step % len(pool)]


def _join_items(items: list[str], fallback: str) -> str:
    values = [item for item in items if item]
    return ", ".join(values) if values else fallback


def _detect_fallback_problem_type(problem: str, parsed_problem: dict = None) -> str:
    text = problem or ""
    goal = ""
    title = ""
    concepts = ""
    if isinstance(parsed_problem, dict):
        goal = str(parsed_problem.get("goal", "") or "")
        title = str(parsed_problem.get("title", "") or "")
        concepts = " ".join(str(item) for item in parsed_problem.get("key_concepts", []) if item)

    full_text = f"{text} {goal} {title} {concepts}"
    motion_keywords = [
        "相向",
        "相遇",
        "速度",
        "每分钟",
        "路程",
        "时间",
        "来回奔跑",
        "小狗",
    ]
    equation_keywords = ["方程", "解方程", "x=", "求x", "等于", "="]
    geometry_keywords = ["三角形", "圆", "正方形", "长方形", "面积", "周长", "角度"]

    if any(keyword in full_text for keyword in motion_keywords):
        return "motion"
    if any(keyword in full_text for keyword in equation_keywords):
        return "equation"
    if any(keyword in full_text for keyword in geometry_keywords):
        return "geometry"
    return "general"


def _default_socratic_question(
    problem: str,
    language: str,
    current_step: int,
    parsed_problem: dict = None,
) -> dict:
    english = _is_english(language)
    problem_type = _detect_fallback_problem_type(problem, parsed_problem)

    if problem_type == "motion":
        if english:
            motion_questions = [
                {
                    "question": "What quantity do we really need first to find the total distance the dog runs?",
                    "options": [
                        "A. Find how long it takes for the two people to meet, then use dog's speed x time",
                        "B. Track each leg the dog runs separately and add them up",
                        "C. Use the distance between the two people as the dog's total path",
                        "D. Add all three speeds together to get the dog's effective speed",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Exactly. The meeting time is the key. Once you know how long they take to meet, the dog's total distance follows immediately.",
                    "error_feedback": "The dog runs non-stop until the two people meet — no need to track individual legs. What single quantity captures the whole running time?",
                    "explanation": "This type of problem is solved by finding meeting time first, then applying distance = speed x time for the dog.",
                },
                {
                    "question": "To find the meeting time of the two people, which formula applies?",
                    "options": [
                        "A. Time = total distance / (sum of both speeds)",
                        "B. Time = total distance / (difference of both speeds)",
                        "C. Time = total distance / (only the faster person's speed)",
                        "D. Time = dog's speed x total distance",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Exactly. Since they approach each other, their speeds combine — the gap shrinks at the rate of both speeds added together.",
                    "error_feedback": "Think about how quickly the gap between them shrinks each minute. Does it shrink at the sum or the difference of their speeds?",
                    "explanation": "For objects moving toward each other, relative speed = sum of both speeds.",
                },
                {
                    "question": "After finding the meeting time, which step correctly gives the dog's total distance?",
                    "options": [
                        "A. Dog's distance = dog's speed x meeting time",
                        "B. Dog's distance = (dog's speed + one person's speed) x meeting time",
                        "C. Dog's distance = total distance between the two starting points",
                        "D. Dog's distance = meeting time x average of all three speeds",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Correct. The dog runs at a fixed speed for the entire duration — distance = speed x time.",
                    "error_feedback": "The dog's distance depends only on its own speed and the total time it ran — not on the other people's speeds.",
                    "explanation": "Once the total running time is known, distance = speed x time gives the dog's path directly.",
                },
            ]
        else:
            motion_questions = [
                {
                    "question": "这道题要算小狗一共跑了多少米，最关键应该先求什么？",
                    "options": [
                        "A. 先求两人相遇用了多少时间，再用小狗速度乘时间",
                        "B. 分段追踪小狗每次来回的路程，最后累加",
                        "C. 用两人之间的初始距离直接当作小狗跑的总路程",
                        "D. 把三者的速度全部相加，得到小狗的有效速度",
                    ],
                    "correct_index": 0,
                    "success_feedback": "很好，关键就是先求相遇时间。时间一确定，小狗总路程就能直接求出来，不用逐段追踪。",
                    "error_feedback": "小狗从始至终不停地跑，不需要逐段计算。整段过程中，哪个量可以一次捕捉到小狗的全程时间？",
                    "explanation": "这类相遇问题先求相遇时间，然后用路程 = 速度 x 时间一步得出小狗的总路程。",
                },
                {
                    "question": "两人同时相向而行，求相遇时间应该用哪个公式？",
                    "options": [
                        "A. 时间 = 总路程 / (两人速度之和)",
                        "B. 时间 = 总路程 / (两人速度之差)",
                        "C. 时间 = 总路程 / (只用速度较快那人的速度)",
                        "D. 时间 = 小狗速度 x 总路程",
                    ],
                    "correct_index": 0,
                    "success_feedback": "正确。相向而行时，两人每分钟共同消耗的距离是两速之和，所以用速度和来除。",
                    "error_feedback": "想想看：每分钟两人之间的距离减少了多少？是两速之和还是速度差？",
                    "explanation": "相向而行的相对速度 = 两速之和，这是相遇问题的核心公式。",
                },
                {
                    "question": "求出相遇时间后，哪一步能正确得到小狗跑的总路程？",
                    "options": [
                        "A. 小狗路程 = 小狗速度 x 相遇时间",
                        "B. 小狗路程 = (小狗速度 + 其中一人速度) x 相遇时间",
                        "C. 小狗路程 = 两人的初始距离",
                        "D. 小狗路程 = 相遇时间 x 三人速度的平均值",
                    ],
                    "correct_index": 0,
                    "success_feedback": "对了。小狗以固定速度跑完全程，路程 = 速度 x 时间，一步到位。",
                    "error_feedback": "小狗的路程只取决于它自己的速度和跑的时间，与两人速度无关。",
                    "explanation": "知道总时间后，路程公式直接给出小狗的全程，无需逐段相加。",
                },
            ]

        index = current_step if 0 <= current_step < len(motion_questions) else len(motion_questions) - 1
        return motion_questions[index]

    if problem_type == "equation":
        if english:
            equation_questions = [
                {
                    "question": "Looking at this equation, what is the most effective first step?",
                    "options": [
                        "A. Move all terms with the unknown to one side and constants to the other",
                        "B. Divide both sides by the coefficient of the unknown immediately",
                        "C. Substitute a trial value to check which side is larger",
                        "D. Multiply out all brackets on both sides before doing anything else",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Correct. Rearranging terms first gives you a clean equation where combining like terms is straightforward.",
                    "error_feedback": "Dividing by the coefficient works at a later stage, but the equation isn't ready for that yet — there are still terms on both sides to organize.",
                    "explanation": "Collect terms with the unknown on one side so you can then combine and simplify.",
                },
                {
                    "question": "After moving terms to their respective sides, what comes next?",
                    "options": [
                        "A. Combine like terms on each side to get the simplest form",
                        "B. Divide both sides by the unknown's coefficient right now",
                        "C. Square both sides to eliminate the unknown from the denominator",
                        "D. Swap the left and right sides for convenience",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Good. Combining like terms reduces the equation to its simplest form, making the next step obvious.",
                    "error_feedback": "Dividing by the coefficient is close but premature — if there are still uncombined like terms, do that first so the coefficient is clear.",
                    "explanation": "Always simplify both sides fully before isolating the unknown.",
                },
                {
                    "question": "The equation is now in its simplest form. How do we isolate the unknown?",
                    "options": [
                        "A. Divide both sides by the coefficient of the unknown",
                        "B. Subtract the unknown's value from both sides",
                        "C. Take the square root of both sides",
                        "D. Move the unknown to the denominator and flip the equation",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Exactly right. Dividing both sides by the coefficient leaves the unknown alone and gives the final answer.",
                    "error_feedback": "Subtracting the unknown from both sides would eliminate it entirely. The goal is to isolate it — dividing by its coefficient does that.",
                    "explanation": "To isolate the unknown, divide both sides by its coefficient.",
                },
            ]
            index = current_step if 0 <= current_step < len(equation_questions) else len(equation_questions) - 1
            return equation_questions[index]
        equation_questions = [
            {
                "question": "观察这个方程，最有效的第一步是什么？",
                "options": [
                    "A. 移项，把含未知数的项移到一边、常数项移到另一边",
                    "B. 立即把两边都除以未知数的系数",
                    "C. 代入一个试探值，看哪边更大",
                    "D. 先把所有括号展开，再做其他步骤",
                ],
                "correct_index": 0,
                "success_feedback": "正确。先移项整理，把未知数集中到一边，为合并同类项做准备。",
                "error_feedback": "除以系数是后面的步骤，现在两边还有项没整理好，先移项才能让系数清晰可见。",
                "explanation": "将含未知数的项集中到一边，常数项移到另一边，便于后续化简。",
            },
            {
                "question": "移项完成后，下一步最该做什么？",
                "options": [
                    "A. 合并同类项，把两边分别化简到最简形式",
                    "B. 现在就把两边除以未知数的系数",
                    "C. 两边同时平方，消去分母中的未知数",
                    "D. 把等式的左右两边互换，方便计算",
                ],
                "correct_index": 0,
                "success_feedback": "很好。合并同类项把方程化到最简，下一步的系数就一目了然。",
                "error_feedback": "除以系数方向对，但还有点早——若同类项还没合并，系数不明确，除法容易出错。",
                "explanation": "先合并同类项化简两边，再隔离未知数，步骤更稳。",
            },
            {
                "question": "方程已化到最简，怎样求出未知数？",
                "options": [
                    "A. 两边同时除以未知数的系数",
                    "B. 两边同时减去未知数本身",
                    "C. 两边同时开平方",
                    "D. 把未知数移到分母并翻转等式",
                ],
                "correct_index": 0,
                "success_feedback": "完全正确。两边除以系数后，未知数就单独留在一边，答案直接得出。",
                "error_feedback": "两边减去未知数会把它消掉，而我们要的是留下它。除以系数才能把未知数单独隔离出来。",
                "explanation": "两边同除以未知数的系数，即可求出未知数的值。",
            },
        ]
        index = current_step if 0 <= current_step < len(equation_questions) else len(equation_questions) - 1
        return equation_questions[index]

    if problem_type == "geometry":
        if english:
            geometry_questions = [
                {
                    "question": "Before calculating, which information about this geometric figure is most important to pin down?",
                    "options": [
                        "A. Identify the figure type and note its key properties (e.g. parallel sides, right angles)",
                        "B. Write down all given numbers first, then decide what figure it is later",
                        "C. Use the perimeter formula immediately since area and perimeter share the same variables",
                        "D. Convert all units to the same scale before identifying the figure",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Good. Identifying the figure and its properties first ensures you choose the right formula in the next step.",
                    "error_feedback": "Knowing the figure type determines which formula applies — getting the numbers without the right formula leads to the wrong calculation.",
                    "explanation": "Identify the shape and its key properties before choosing any formula.",
                },
                {
                    "question": "You've identified the figure. How do you decide which formula to use?",
                    "options": [
                        "A. Match the formula to what the problem asks for (area, perimeter, angle, etc.)",
                        "B. Use the most general formula you remember, since it works for all shapes",
                        "C. Apply both area and perimeter formulas, then pick the answer that looks right",
                        "D. Use the formula for a similar but simpler shape as an approximation",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Correct. The goal of the problem — area, perimeter, angle — directly determines which formula to apply.",
                    "error_feedback": "There is no single formula that works for all shapes and goals. The problem's target quantity should guide your formula choice.",
                    "explanation": "Choose the formula that matches both the figure type and the quantity being asked for.",
                },
                {
                    "question": "When substituting values into the formula, what is most likely to cause an error?",
                    "options": [
                        "A. Mismatched units or substituting a measurement meant for a different dimension",
                        "B. Not converting fractions to decimals before substituting",
                        "C. Writing the formula on the left instead of the right side of the equals sign",
                        "D. Using the exact value instead of rounding to one decimal place",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Exactly. Unit mismatches and substituting the wrong measurement are the most common sources of error.",
                    "error_feedback": "Fraction-to-decimal conversion rarely causes mistakes in geometry. Watch out for unit mismatches and whether you're using the right dimension.",
                    "explanation": "Check that units are consistent and each variable gets its correct measurement before computing.",
                },
            ]
            index = current_step if 0 <= current_step < len(geometry_questions) else len(geometry_questions) - 1
            return geometry_questions[index]
        geometry_questions = [
            {
                "question": "计算前，最需要先确认这个几何图形的哪方面信息？",
                "options": [
                    "A. 先判断图形类型，记录关键性质（如平行边、直角等）",
                    "B. 先把所有已知数字列出来，之后再确定是什么图形",
                    "C. 直接套周长公式，因为面积和周长用同一批变量",
                    "D. 先把所有单位统一，之后再识别图形",
                ],
                "correct_index": 0,
                "success_feedback": "很好。先确认图形类型和性质，才能在下一步选对公式。",
                "error_feedback": "图形类型决定了用哪个公式——先凑数字却没选对公式，计算方向就会出错。",
                "explanation": "选公式之前，先弄清图形及其关键性质。",
            },
            {
                "question": "已经确认了图形，怎么决定用哪个公式？",
                "options": [
                    "A. 根据题目所求（面积、周长、角度等）来匹配公式",
                    "B. 用自己记得最清楚的那个通用公式，因为它对所有图形都适用",
                    "C. 面积和周长两个公式都算一遍，再选看起来合理的答案",
                    "D. 用类似但更简单的图形的公式近似代替",
                ],
                "correct_index": 0,
                "success_feedback": "正确。题目要求的量——面积、周长还是角度——直接决定用哪个公式。",
                "error_feedback": "没有一个公式能适用所有图形和所有目标量。题目的求解目标才是选公式的依据。",
                "explanation": "根据图形类型和所求量，选择最对应的公式。",
            },
            {
                "question": "把数值代入公式时，最容易引发错误的是哪种情况？",
                "options": [
                    "A. 单位不一致，或把用于另一维度的量代错了位置",
                    "B. 代入前没有把分数转换成小数",
                    "C. 把公式写在等号左边而不是右边",
                    "D. 使用了精确值而不是四舍五入到一位小数",
                ],
                "correct_index": 0,
                "success_feedback": "完全正确。单位不统一和量搞混（如把直径当半径代入）是几何计算最常见的错误源。",
                "error_feedback": "分数转小数很少出错。更要注意的是单位是否一致，以及是否把正确的那个量代入了公式中正确的位置。",
                "explanation": "代入前检查：单位是否统一，每个变量是否对应了正确的测量值。",
            },
        ]
        index = current_step if 0 <= current_step < len(geometry_questions) else len(geometry_questions) - 1
        return geometry_questions[index]

    if english:
        return {
            "question": f"Step {current_step + 1}: which of the following best describes the right focus right now?",
            "options": [
                "A. Pin down what is known and what is being asked before choosing any method",
                "B. Jump straight into building an equation using the numbers given",
                "C. Search for a formula that uses all the given numbers at once",
                "D. Work backwards from a guessed answer to see if it fits",
            ],
            "correct_index": 0,
            "success_feedback": "Good. Clarifying what you know and what you need is always the most reliable starting point.",
            "error_feedback": "Building equations or picking formulas too early can lead you down the wrong path if the goal isn't clear yet. Start by identifying knowns and unknowns.",
            "explanation": "Before choosing any method, make sure the known conditions and target are fully understood.",
        }

    return {
        "question": f"第{current_step + 1}步：以下哪个描述最符合当前应该关注的事情？",
        "options": [
            "A. 先弄清楚已知量和待求量，再决定用什么方法",
            "B. 直接用题目给的数字建立方程",
            "C. 找一个能把所有已知数一次用完的公式",
            "D. 从猜测的答案出发，反推看是否符合条件",
        ],
        "correct_index": 0,
        "success_feedback": "很好！先搞清楚已知和所求，是最可靠的出发点。",
        "error_feedback": "目标还没明确就急着建方程或套公式，容易走弯路。先确认已知量和待求量，再选方法。",
        "explanation": "选择方法之前，先确认已知条件和求解目标是什么。",
    }


def _normalize_socratic_question(result: dict, language: str, current_step: int) -> dict:
    fallback = _default_socratic_question("", language, current_step)
    options = result.get("options")
    normalized_options = []
    if isinstance(options, list):
        normalized_options = [str(option).strip() for option in options if str(option).strip()]

    if len(normalized_options) < 2:
        normalized_options = fallback["options"]
    elif len(normalized_options) > 5:
        normalized_options = normalized_options[:5]

    correct_index = result.get("correct_index", fallback["correct_index"])
    if not isinstance(correct_index, int) or not 0 <= correct_index < len(normalized_options):
        correct_index = fallback["correct_index"]

    question = result.get("question")
    if not isinstance(question, str) or not question.strip():
        question = fallback["question"]

    def _pick_text(key: str) -> str:
        value = result.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else fallback[key]

    return {
        "question": question.strip(),
        "options": normalized_options,
        "correct_index": correct_index,
        "success_feedback": _pick_text("success_feedback"),
        "error_feedback": _pick_text("error_feedback"),
        "explanation": _pick_text("explanation"),
    }


class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "deepseek").lower()
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("AI_MODEL", "deepseek-v4-flash")
        self.fast_model = os.getenv("AI_FAST_MODEL", self.model)
        self.slow_model = os.getenv("AI_SLOW_MODEL", self.fast_model)
        self.enabled = bool(self.api_key)

    def load_persisted_config(self):
        """控制台持久化配置优先于 .env。"""
        try:
            provider = db.get_config("ai_provider")
            model = db.get_config("ai_model")
            fast_model = db.get_config("ai_fast_model")
            slow_model = db.get_config("ai_slow_model")
            api_key = db.get_config("ai_api_key")
            base_url = db.get_config("ai_base_url")
        except Exception:
            return

        if provider:
            self.provider = provider.lower()
            os.environ["AI_PROVIDER"] = provider
        if model:
            self.model = model
            os.environ["AI_MODEL"] = model
        if fast_model:
            self.fast_model = fast_model
            os.environ["AI_FAST_MODEL"] = fast_model
        else:
            self.fast_model = self.model
        if slow_model:
            self.slow_model = slow_model
            os.environ["AI_SLOW_MODEL"] = slow_model
        else:
            self.slow_model = self.fast_model
        if api_key is not None:
            self.api_key = api_key
            os.environ["AI_API_KEY"] = api_key
        if base_url is not None:
            self.base_url = base_url
            os.environ["AI_BASE_URL"] = base_url
        self.enabled = bool(self.api_key)

    def _select_model(self, profile: str) -> str:
        if profile == "slow":
            return self.slow_model
        return self.fast_model

    async def test_connection(self, provider: str, api_key: str, base_url: str, model: str) -> dict:
        provider = (provider or "").lower().strip()
        api_key = (api_key or "").strip()
        base_url = (base_url or "").rstrip("/")
        model = (model or "").strip()
        started_at = time.time()

        if not provider or not model or not base_url:
            return {"success": False, "message": "供应商、模型和基础URL不能为空"}
        if not api_key:
            return {"success": False, "message": "API密钥不能为空"}

        try:
            test_prompt = "Calculate 1+1. Reply with only the number 2."
            messages = [{"role": "user", "content": test_prompt}]
            if provider == "baidu":
                url = f"{base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
                params = {"access_token": api_key}
                payload = {
                    "messages": messages,
                    "max_output_tokens": 32,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, params=params, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    preview, raw_preview = _extract_chat_preview(data)
            else:
                url = f"{base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0,
                    "max_tokens": 64,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    preview, raw_preview = _extract_chat_preview(data)

            success = bool(preview)
            message = "连接成功，模型返回有效测试响应" if success else "连接成功，但模型返回内容为空"
            response_summary = preview or raw_preview
            try:
                db.add_ai_log(
                    session_id=None,
                    provider=provider,
                    model=model,
                    method="test_connection",
                    used_parsed_problem=False,
                    parsed_problem_title=None,
                    request_summary=test_prompt,
                    response_summary=response_summary,
                    duration_ms=int((time.time() - started_at) * 1000),
                    success=success,
                    error_message="" if success else f"{message}; raw_response={raw_preview}",
                )
            except Exception:
                pass
            return {"success": success, "message": message, "response_preview": preview or raw_preview}
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text[:500] if e.response is not None else str(e)
            message = f"HTTP {e.response.status_code}: {error_detail}" if e.response is not None else str(e)
            try:
                db.add_ai_log(
                    session_id=None,
                    provider=provider,
                    model=model,
                    method="test_connection",
                    used_parsed_problem=False,
                    parsed_problem_title=None,
                    request_summary="Calculate 1+1. Reply with only the number 2.",
                    response_summary="",
                    duration_ms=int((time.time() - started_at) * 1000),
                    success=False,
                    error_message=message[:500],
                )
            except Exception:
                pass
            return {"success": False, "message": message}
        except Exception as e:
            try:
                db.add_ai_log(
                    session_id=None,
                    provider=provider,
                    model=model,
                    method="test_connection",
                    used_parsed_problem=False,
                    parsed_problem_title=None,
                    request_summary="Calculate 1+1. Reply with only the number 2.",
                    response_summary="",
                    duration_ms=int((time.time() - started_at) * 1000),
                    success=False,
                    error_message=str(e)[:500],
                )
            except Exception:
                pass
            return {"success": False, "message": str(e)}

    def get_full_config(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "fast_model": self.fast_model,
            "slow_model": self.slow_model,
            "api_key_masked": mask_api_key(self.api_key),
            "base_url": self.base_url,
            "enabled": self.enabled,
            "provider_presets": PROVIDER_PRESETS,
        }

    async def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        profile: str = "fast",
        method: str = "unknown",
        used_parsed_problem: bool = False,
        parsed_problem_title: str = None,
        session_id: str = None,
    ) -> str:
        if not self.enabled:
            raise ValueError("AI服务未配置,请设置 AI_API_KEY 环境变量")

        request_summary = json.dumps(messages, ensure_ascii=False)
        start_time = time.time()
        success = True
        error_message = None
        result = ""
        selected_model = self._select_model(profile)

        try:
            if self.provider == "openai":
                result = await self._call_openai(messages, temperature, max_tokens, selected_model)
            elif self.provider == "minimax":
                result = await self._call_openai(messages, temperature, max_tokens, selected_model)
            elif self.provider == "qwen":
                result = await self._call_qwen(messages, temperature, max_tokens, selected_model)
            elif self.provider == "baidu":
                result = await self._call_baidu(messages, temperature, max_tokens, selected_model)
            else:
                result = await self._call_openai(messages, temperature, max_tokens, selected_model)
            return result
        except Exception as e:
            success = False
            error_message = str(e)[:500]
            raise Exception(f"AI服务调用失败: {str(e)}")
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            response_summary = result or ""
            if not success:
                response_summary = ""
            try:
                db.add_ai_log(
                    session_id=session_id,
                    provider=self.provider,
                    model=selected_model,
                    method=f"{method}:{profile}",
                    used_parsed_problem=used_parsed_problem,
                    parsed_problem_title=parsed_problem_title,
                    request_summary=request_summary,
                    response_summary=response_summary,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                )
            except Exception:
                pass

    async def _call_openai(self, messages, temperature, max_tokens, model) -> str:
        url = f"{self.base_url or 'https://api.openai.com/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_qwen(self, messages, temperature, max_tokens, model) -> str:
        url = (
            self.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ) + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or "qwen-plus",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_baidu(self, messages, temperature, max_tokens, model) -> str:
        url = f"{self.base_url or 'https://aip.baidubce.com'}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        params = {"access_token": self.api_key}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("result", "")

    async def parse_problem(self, problem: str, session_id: str = None) -> dict:
        system_prompt = """你是一个专业的数学教育AI助手。你的任务是分析学生提交的数学题目，并返回结构化的JSON数据。

请分析以下数学题目，返回JSON格式数据：
{
  "problem_type": "equation|geometry|general|algebra|function",
  "title": "题目简短标题",
  "known_conditions": ["已知条件1", "已知条件2"],
  "goal": "求解目标",
  "key_concepts": ["涉及的知识点1", "知识点2"],
  "suggested_steps": ["建议的解题步骤1", "步骤2", "步骤3"]
}

只返回JSON，不要其他文字。"""

        user_prompt = f"请分析这道数学题：\n{problem}"

        response = await self.chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            profile="slow",
            method="parse_problem",
            used_parsed_problem=False,
            session_id=session_id,
        )

        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
            else:
                return {
                    "problem_type": "general",
                    "title": problem[:20],
                    "known_conditions": [problem],
                    "goal": "求解",
                    "key_concepts": [],
                    "suggested_steps": ["理解题意", "分析条件", "求解"],
                }
        except json.JSONDecodeError:
            return {
                "problem_type": "general",
                "title": problem[:20],
                "known_conditions": [problem],
                "goal": "求解",
                "key_concepts": [],
                "suggested_steps": ["理解题意", "分析条件", "求解"],
            }

    async def generate_socratic_question(
        self,
        problem: str,
        history: list[dict],
        current_step: int,
        total_steps: int,
        parsed_problem: dict = None,
        language: str = "zh-CN",
        current_node_context: str = "",
        session_id: str = None,
    ) -> dict:
        english = _is_english(language)
        history_text = "\n".join(
            [
                (
                    f"Q{i+1}: {h.get('question', '')}\n"
                    f"A: {h.get('answer', '')}\n"
                    f"Selected option: {h.get('selected_option', '')}\n"
                    f"Feedback: {h.get('feedback', '')}"
                )
                if english
                else (
                    f"Q{i+1}: {h.get('question', '')}\n"
                    f"A: {h.get('answer', '')}\n"
                    f"选择: {h.get('selected_option', '')}\n"
                    f"反馈: {h.get('feedback', '')}"
                )
                for i, h in enumerate(history)
            ]
        ) if history else ("(This is the first step)" if english else "（这是第一步）")

        parsed_info = ""
        if parsed_problem:
            if english:
                parsed_info = f"""
Problem analysis:
- Problem type: {parsed_problem.get('problem_type', 'unknown')}
- Title: {parsed_problem.get('title', 'unknown')}
- Known conditions: {_join_items(parsed_problem.get('known_conditions', []), 'none')}
- Goal: {parsed_problem.get('goal', 'unknown')}
- Key concepts: {_join_items(parsed_problem.get('key_concepts', []), 'none')}
- Suggested steps: {' -> '.join(parsed_problem.get('suggested_steps', [])) or 'none'}
"""
            else:
                parsed_info = f"""
题目分析结果：
- 题目类型：{parsed_problem.get('problem_type', '未知')}
- 题目标题：{parsed_problem.get('title', '未知')}
- 已知条件：{_join_items(parsed_problem.get('known_conditions', []), '无')}
- 求解目标：{parsed_problem.get('goal', '未知')}
- 涉及知识点：{_join_items(parsed_problem.get('key_concepts', []), '无')}
- 建议步骤：{' -> '.join(parsed_problem.get('suggested_steps', [])) or '无'}
"""

        current_node_text = ""
        if current_node_context:
            current_node_text = (
                f"\nCurrent node context:\n{current_node_context}\n"
                if english
                else f"\n当前节点上下文：\n{current_node_context}\n"
            )

        q_type_name, q_type_desc = _pick_question_type(current_step, english)

        if english:
            system_prompt = """You are a professional math tutor AI who guides students with the Socratic method.

Your job:
1. Generate one guidance question for the student's current step.
2. The question must help the student think — never reveal the answer directly.
3. Provide 2-4 options (A/B/C/D). ALL options must be plausible, well-reasoned thinking directions.
4. Option requirements:
   - Every option must be a thoughtful, logical approach a student might realistically choose
   - One option is the optimal path; the others are viable but suboptimal, roundabout, or incomplete
   - Distractors should reflect genuine student misconceptions — wrong formula, overlooked condition, incorrect operation order, premature calculation
   - NEVER include "give up", "guess randomly", "skip", "I don't know" or any defeatist option
   - NEVER include absurd or irrelevant options
   - Each option must describe a specific thought or action, not a vague attitude
5. Prepare encouraging feedback for the correct choice and a gentle hint for incorrect choices (explain why that path is less optimal, not just "wrong").
6. Respond in English.

Return strict JSON only:
{
  "question": "Guiding question",
  "options": ["A. ...", "B. ...", "C. ..."],
  "correct_index": 0,
  "success_feedback": "Encouraging feedback for the correct choice",
  "error_feedback": "Gentle hint for an incorrect choice",
  "explanation": "Short explanation for this step"
}

Requirements:
- Make the question specific to the current step, not generic.
- Every option should make the student pause and think before choosing.
- Feedback should be insightful, helping students understand trade-offs between options.
- Do not include any text outside the JSON."""
            user_prompt = f"""Math problem: {problem}
Current progress: step {current_step + 1} of about {total_steps}
Question type: {q_type_name} — {q_type_desc}
{parsed_info}{current_node_text}
Conversation history:
{history_text}

Generate the Socratic question for this step. The question type is "{q_type_name}" — design the question and options accordingly."""
        else:
            system_prompt = """你是一个专业的数学教育AI助手，擅长使用苏格拉底式教学法引导学生思考。

你的任务是：
1. 根据学生的当前进度和回答历史，生成一个引导性的问题。
2. 问题应该帮助学生思考，而不是直接给出答案。
3. 提供2-4个选项（A/B/C/D），所有选项都必须是合理的、有逻辑的思考方向。
4. 选项要求：
   - 每个选项都必须是认真思考后可能得出的合理思路
   - 一个是最优路径，其余是可行但次优、绕远或有局限的路径
   - 干扰项应反映真实的学生常见思维——如选错公式、忽略条件、计算顺序错误、过早代入
   - 禁止出现"放弃"、"随便猜"、"跳过"、"不做了"等消极选项
   - 禁止出现与题目无关的荒谬选项
   - 每个选项要描述具体的思考或操作，而非笼统态度
5. 对正确选项准备鼓励性反馈，对错误选项解释为什么这条思路不如最优的（不要只说"错了"）。
6. 用中文回答。

返回严格的JSON格式：
{
  "question": "引导性问题",
  "options": ["A. ...", "B. ...", "C. ..."],
  "correct_index": 0,
  "success_feedback": "选择正确时的鼓励性反馈",
  "error_feedback": "选择错误时的温和提示",
  "explanation": "这一步的简短说明"
}

注意：
- 问题要具体到当前步骤，不要太笼统。
- 每个选项都应让学生需要认真思考才能区分优劣。
- 反馈要有启发性，帮助学生理解各选项的利弊。
- 只返回JSON，不要其他文字。"""
            user_prompt = f"""数学题目：{problem}
当前进度：第{current_step + 1}步（共约{total_steps}步）
提问类型：{q_type_name}——{q_type_desc}
{parsed_info}{current_node_text}
历史对话：
{history_text}

请为这一步生成苏格拉底式提问。注意：提问类型是「{q_type_name}」，请按照这个类型来设计问题和选项。"""

        response = await self.chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            profile="fast",
            method="generate_socratic_question",
            used_parsed_problem=bool(parsed_problem),
            parsed_problem_title=(
                str(parsed_problem.get("title", "")).strip()
                if isinstance(parsed_problem, dict)
                else None
            ),
            session_id=session_id,
        )

        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                if isinstance(result, dict):
                    return _normalize_socratic_question(result, language, current_step)
        except (json.JSONDecodeError, KeyError):
            pass
        return _default_socratic_question(problem, language, current_step, parsed_problem)

    async def generate_final_solution(
        self,
        problem: str,
        history: list[dict],
        language: str = "zh-CN",
        session_id: str = None,
    ) -> str:
        english = _is_english(language)
        history_text = "\n".join(
            [
                (
                    f"Step {i+1}: {h.get('question', '')} -> "
                    f"Answer: {h.get('answer', '')} -> "
                    f"Feedback: {h.get('feedback', '')}"
                )
                if english
                else (
                    f"步骤{i+1}: {h.get('question', '')} -> "
                    f"回答: {h.get('answer', '')} -> "
                    f"反馈: {h.get('feedback', '')}"
                )
                for i, h in enumerate(history)
            ]
        ) if history else ("No history recorded" if english else "无历史记录")

        if english:
            system_prompt = """You are a professional math tutor AI. Summarize the student's full reasoning path.

Requirements:
1. Present the full solution in clear steps.
2. Comment briefly on the student's choices along the way.
3. Summarize the key method and common pitfalls.
4. End with encouraging study advice.

Respond in friendly, clear English."""
            user_prompt = f"""Math problem: {problem}

Student reasoning history:
{history_text}

Provide a complete solution summary and learning advice."""
        else:
            system_prompt = """你是一个专业的数学教育AI助手。根据学生的解题过程，给出完整的解题思路总结。

要求：
1. 用清晰的步骤展示完整解题过程。
2. 结合学生在每一步的回答进行点评。
3. 总结解题的关键方法和注意事项。
4. 鼓励学生继续保持良好的思维习惯。

用中文回答，语言亲切易懂。"""
            user_prompt = f"""数学题目：{problem}

学生的推演过程：
{history_text}

请给出完整的解题思路总结和学习建议。"""

        return await self.chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
            profile="fast",
            method="generate_final_solution",
            used_parsed_problem=False,
            session_id=session_id,
        )


ai_service = AIService()
