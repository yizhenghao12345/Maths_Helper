import os
import json
import time
import httpx

import db


def mask_api_key(key: str) -> str:
    if not key or len(key) <= 8:
        return "***" if key else ""
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


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
                        "B. Count how many times the dog turns around",
                        "C. Add the dog's speed to Xiao Ming's speed only",
                        "D. Guess the answer directly",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Good. The key is the meeting time. Once time is known, the dog's total distance is easy to get.",
                    "error_feedback": "Try focusing on what remains unchanged during the whole process: the dog runs the entire time until the two people meet.",
                    "explanation": "This type of problem is usually solved by finding meeting time first.",
                },
                {
                    "question": "How do we find the meeting time of the two people?",
                    "options": [
                        "A. Use total distance divided by their combined speed",
                        "B. Use the dog's speed divided by the distance",
                        "C. Subtract the two walking speeds first and ignore the distance",
                        "D. Count the dog's turning points",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Exactly. Since they walk toward each other, their speeds add up.",
                    "error_feedback": "Think about the distance between them shrinking every minute. Which speed describes that shrinking?",
                    "explanation": "For moving toward each other, the relative speed is the sum of their speeds.",
                },
                {
                    "question": "After finding the meeting time, what should we do next to get the dog's total distance?",
                    "options": [
                        "A. Multiply the dog's speed by the meeting time",
                        "B. Add the dog's speed to both walking speeds",
                        "C. Divide the dog's speed by the number of turns",
                        "D. Use the distance between the houses again directly",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Right. The dog's distance is just speed multiplied by the total running time.",
                    "error_feedback": "The dog keeps running the whole time until the two people meet. Which formula directly uses that fact?",
                    "explanation": "Once the total running time is known, distance = speed x time.",
                },
            ]
        else:
            motion_questions = [
                {
                    "question": "这道题要算小狗一共跑了多少米，最关键应该先求什么？",
                    "options": [
                        "A. 先求两人相遇用了多少时间，再用小狗速度乘时间",
                        "B. 先数小狗一共来回跑了多少次",
                        "C. 只把小狗速度和小明速度相加",
                        "D. 直接猜一个结果",
                    ],
                    "correct_index": 0,
                    "success_feedback": "很好，关键就是先求相遇时间。时间一确定，小狗总路程就能直接求出来。",
                    "error_feedback": "再想想，整段过程中不变的是什么？小狗一直跑到两人相遇为止，所以关键是总时间。",
                    "explanation": "这类相遇问题通常先求相遇时间，再求小狗跑的总路程。",
                },
                {
                    "question": "两人同时相向而行，相遇时间应该怎样求？",
                    "options": [
                        "A. 用总路程除以两人的速度和",
                        "B. 用小狗速度除以总路程",
                        "C. 只用两人的速度差来计算",
                        "D. 先算小狗跑了多少趟",
                    ],
                    "correct_index": 0,
                    "success_feedback": "正确。相向而行时，距离缩短的速度就是两人的速度和。",
                    "error_feedback": "想一想：每分钟两人之间的距离一共减少多少米？",
                    "explanation": "相向而行要用速度和，也就是相遇问题里的相对速度。",
                },
                {
                    "question": "求出相遇时间后，下一步怎样得到小狗跑的总路程？",
                    "options": [
                        "A. 用小狗速度乘相遇时间",
                        "B. 把小狗速度和两人的速度全部相加",
                        "C. 用小狗速度除以掉头次数",
                        "D. 再直接把 1200 米乘一次",
                    ],
                    "correct_index": 0,
                    "success_feedback": "对了。小狗从出发到相遇这段时间一直在跑，总路程就是速度乘时间。",
                    "error_feedback": "抓住核心：小狗并不需要一趟一趟分开算，只要知道它跑了多久。",
                    "explanation": "知道总时间后，直接用路程公式即可求出结果。",
                },
            ]

        index = current_step if 0 <= current_step < len(motion_questions) else len(motion_questions) - 1
        return motion_questions[index]

    if problem_type == "equation":
        if english:
            equation_questions = [
                {
                    "question": "Looking at this equation, what should the first step be?",
                    "options": [
                        "A. Calculate randomly right away",
                        "B. Rearrange terms so the unknown is on one side",
                        "C. Ignore the equality and estimate",
                        "D. Give up",
                    ],
                    "correct_index": 1,
                    "success_feedback": "Good start. Rearranging the equation is the key first move.",
                    "error_feedback": "Think again. Solving an equation usually starts by organizing the two sides.",
                    "explanation": "Collect the terms with the unknown together.",
                },
                {
                    "question": "After rearranging, what should happen next?",
                    "options": [
                        "A. Combine like terms to simplify the equation",
                        "B. Copy the problem again",
                        "C. Jump straight to the answer",
                        "D. Switch to another problem",
                    ],
                    "correct_index": 0,
                    "success_feedback": "Correct. Simplifying makes the relationship clearer.",
                    "error_feedback": "Not yet. The equation still needs to be simplified.",
                    "explanation": "Combine like terms and simplify the expression.",
                },
                {
                    "question": "After simplifying, how do we isolate the unknown?",
                    "options": [
                        "A. Guess a number",
                        "B. Divide both sides by the coefficient",
                        "C. Stop here",
                        "D. Write any answer",
                    ],
                    "correct_index": 1,
                    "success_feedback": "Exactly. That isolates the unknown and gives the answer.",
                    "error_feedback": "Take another look. The final goal is to isolate the unknown.",
                    "explanation": "Solve for the unknown value.",
                },
            ]
            index = current_step if 0 <= current_step < len(equation_questions) else len(equation_questions) - 1
            return equation_questions[index]
        equation_questions = [
            {
                "question": "观察这个方程，你认为第一步应该做什么？",
                "options": [
                    "A. 直接计算结果",
                    "B. 移项，把含未知数的项移到一边",
                    "C. 忽略等式，随便算",
                    "D. 放弃不做",
                ],
                "correct_index": 1,
                "success_feedback": "很好。移项是解方程的重要第一步。",
                "error_feedback": "再想想。解方程时通常要先整理等式。",
                "explanation": "将含有未知数的项集中处理。",
            },
            {
                "question": "移项后，下一步应该做什么？",
                "options": [
                    "A. 合并同类项，化简等式",
                    "B. 重新抄一遍题目",
                    "C. 直接写出答案",
                    "D. 换个题目做",
                ],
                "correct_index": 0,
                "success_feedback": "正确。化简能让等式关系更清晰。",
                "error_feedback": "别着急，还需要进一步整理。",
                "explanation": "合并同类项并化简表达式。",
            },
            {
                "question": "化简后，如何求出未知数？",
                "options": [
                    "A. 猜一个数字",
                    "B. 两边同时除以系数",
                    "C. 不用求了",
                    "D. 随便写答案",
                ],
                "correct_index": 1,
                "success_feedback": "太棒了。这样就能得到最终答案。",
                "error_feedback": "再思考一下。目标是把未知数单独留下。",
                "explanation": "求解未知数的值。",
            },
        ]
        index = current_step if 0 <= current_step < len(equation_questions) else len(equation_questions) - 1
        return equation_questions[index]

    if problem_type == "geometry":
        if english:
            geometry_questions = [
                {
                    "question": "What geometric figure or relationship appears in this problem?",
                    "options": [
                        "A. Guess without reading carefully",
                        "B. Identify the figure and its properties",
                        "C. Ignore the figure and calculate directly",
                        "D. Skip this step",
                    ],
                    "correct_index": 1,
                    "success_feedback": "Good. Recognizing the figure is the right starting point.",
                    "error_feedback": "Try again. Geometry problems usually begin with identifying the figure.",
                    "explanation": "Identify the shape and its important properties.",
                },
                {
                    "question": "After identifying the figure, what should you choose next?",
                    "options": [
                        "A. Pick any formula",
                        "B. Choose a method or formula based on the goal",
                        "C. Estimate without a formula",
                        "D. Give up",
                    ],
                    "correct_index": 1,
                    "success_feedback": "Correct. Matching the method to the goal is essential.",
                    "error_feedback": "Slow down. The method should match what the problem asks for.",
                    "explanation": "Choose the most suitable formula or approach.",
                },
                {
                    "question": "When substituting values, what should you pay attention to?",
                    "options": [
                        "A. Nothing in particular",
                        "B. Units and calculation accuracy",
                        "C. Rough guessing only",
                        "D. Skip the calculation",
                    ],
                    "correct_index": 1,
                    "success_feedback": "Exactly. Careful substitution prevents avoidable mistakes.",
                    "error_feedback": "Think again. Details like units and precision matter here.",
                    "explanation": "Substitute values carefully and compute accurately.",
                },
            ]
            index = current_step if 0 <= current_step < len(geometry_questions) else len(geometry_questions) - 1
            return geometry_questions[index]
        geometry_questions = [
            {
                "question": "这道题涉及什么几何图形或关系？",
                "options": [
                    "A. 随意猜测",
                    "B. 识别图形和性质",
                    "C. 不管图形直接算",
                    "D. 跳过这步",
                ],
                "correct_index": 1,
                "success_feedback": "很好。认清图形是关键起点。",
                "error_feedback": "想想看。几何题通常先要识别图形和性质。",
                "explanation": "识别几何图形及其重要性质。",
            },
            {
                "question": "确定图形后，下一步应该选什么方法？",
                "options": [
                    "A. 随便选公式",
                    "B. 根据所求选择公式或方法",
                    "C. 不用公式直接目测",
                    "D. 放弃",
                ],
                "correct_index": 1,
                "success_feedback": "正确。方法要和题目目标匹配。",
                "error_feedback": "别急。先想想题目要求你求什么。",
                "explanation": "选择合适的解题公式或方法。",
            },
            {
                "question": "代入数值计算时需要注意什么？",
                "options": [
                    "A. 不用注意",
                    "B. 注意单位和计算精度",
                    "C. 大概估算就行",
                    "D. 不计算了",
                ],
                "correct_index": 1,
                "success_feedback": "非常棒。细心处理细节很重要。",
                "error_feedback": "再想想。单位和计算准确性会影响结果。",
                "explanation": "认真代入数值并准确计算。",
            },
        ]
        index = current_step if 0 <= current_step < len(geometry_questions) else len(geometry_questions) - 1
        return geometry_questions[index]

    if english:
        return {
            "question": f"Step {current_step + 1}: what should we focus on next?",
            "options": [
                "A. Analyze the known conditions and identify key information",
                "B. Build an equation or relationship from the information",
                "C. Review relevant formulas or theorems",
                "D. I am not sure and need a hint",
            ],
            "correct_index": 0,
            "success_feedback": "Good choice. Keep building the reasoning step by step.",
            "error_feedback": "Take another look at the goal and the given information.",
            "explanation": "This step is about identifying the most useful information first.",
        }

    return {
        "question": f"第{current_step + 1}步：你觉得接下来应该怎么做？",
        "options": [
            "A. 分析已知条件，找出关键信息",
            "B. 尝试建立方程或关系式",
            "C. 回顾相关公式和定理",
            "D. 不确定，需要提示",
        ],
        "correct_index": 0,
        "success_feedback": "很好！继续深入思考。",
        "error_feedback": "再想想看，先回到题目目标和已知条件。",
        "explanation": "这一步的关键在于先找准可用信息。",
    }


def _normalize_socratic_question(result: dict, language: str, current_step: int) -> dict:
    fallback = _default_socratic_question("", language, current_step)
    options = result.get("options")
    normalized_options = []
    if isinstance(options, list):
        normalized_options = [str(option).strip() for option in options if str(option).strip()]

    if len(normalized_options) < 4:
        normalized_options = fallback["options"]

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
        try:
            messages = [{"role": "user", "content": "Hi"}]
            if provider == "baidu":
                url = f"{base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
                params = {"access_token": api_key}
                payload = {
                    "messages": messages,
                    "max_output_tokens": 5,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, params=params, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    preview = data.get("result", "")[:100]
            else:
                url = f"{base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 5,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    preview = data["choices"][0]["message"]["content"][:100]
            return {"success": True, "message": "连接成功", "response_preview": preview}
        except Exception as e:
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

        request_summary = json.dumps(messages, ensure_ascii=False)[:200]
        start_time = time.time()
        success = True
        error_message = None
        result = ""
        selected_model = self._select_model(profile)

        try:
            if self.provider == "openai":
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
            response_summary = result[:200] if result else ""
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

        if english:
            system_prompt = """You are a professional math tutor AI who guides students with the Socratic method.

Your job:
1. Generate one guidance question for the student's current step.
2. The question must help the student decide the next move instead of revealing the answer directly.
3. Provide 4 options (A/B/C/D). Exactly one option should be the best next step. The others should reflect common mistakes, premature calculation, or giving up.
4. Prepare encouraging feedback for the correct choice and a gentle hint for an incorrect choice.
5. Respond in English.

Return strict JSON only:
{
  "question": "Guiding question",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_index": 0,
  "success_feedback": "Encouraging feedback for the correct choice",
  "error_feedback": "Gentle hint for an incorrect choice",
  "explanation": "Short explanation for this step"
}

Requirements:
- Make the question specific to the current step.
- Keep options pedagogically meaningful.
- Do not include any text outside the JSON."""
            user_prompt = f"""Math problem: {problem}
Current progress: step {current_step + 1} of about {total_steps}
{parsed_info}{current_node_text}
Conversation history:
{history_text}

Generate the Socratic question for this step."""
        else:
            system_prompt = """你是一个专业的数学教育AI助手，擅长使用苏格拉底式教学法引导学生思考。

你的任务是：
1. 根据学生的当前进度和回答历史，生成一个引导性的问题。
2. 问题应该帮助学生思考下一步该做什么，而不是直接给出答案。
3. 提供4个选项（A/B/C/D），其中一个是当前最合理的思路，其他选项体现常见误区、过早计算或放弃态度。
4. 对正确选项准备鼓励性反馈，对错误选项准备温和提示。
5. 用中文回答。

返回严格的JSON格式：
{
  "question": "引导性问题",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_index": 0,
  "success_feedback": "选择正确时的鼓励性反馈",
  "error_feedback": "选择错误时的温和提示",
  "explanation": "这一步的简短说明"
}

注意：
- 问题要具体到当前步骤，不要太笼统。
- 错误选项要反映学生常见的错误思维。
- 反馈要有启发性，帮助学生理解为什么对或错。
- 只返回JSON，不要其他文字。"""
            user_prompt = f"""数学题目：{problem}
当前进度：第{current_step + 1}步（共约{total_steps}步）
{parsed_info}{current_node_text}
历史对话：
{history_text}

请为这一步生成苏格拉底式提问。"""

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
