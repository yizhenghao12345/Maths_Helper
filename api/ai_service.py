import os
import json
import time
import httpx
from typing import Optional

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
        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
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


class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.api_key = os.getenv("AI_API_KEY", "")
        self.base_url = os.getenv("AI_BASE_URL", "")
        self.model = os.getenv("AI_MODEL", "gpt-3.5-turbo")
        self.enabled = bool(self.api_key)

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
        method: str = "unknown",
        session_id: str = None,
    ) -> str:
        if not self.enabled:
            raise ValueError("AI服务未配置,请设置 AI_API_KEY 环境变量")

        request_summary = json.dumps(messages, ensure_ascii=False)[:200]
        start_time = time.time()
        success = True
        error_message = None
        result = ""

        try:
            if self.provider == "openai":
                result = await self._call_openai(messages, temperature, max_tokens)
            elif self.provider == "qwen":
                result = await self._call_qwen(messages, temperature, max_tokens)
            elif self.provider == "baidu":
                result = await self._call_baidu(messages, temperature, max_tokens)
            else:
                result = await self._call_openai(messages, temperature, max_tokens)
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
                    model=self.model,
                    method=method,
                    request_summary=request_summary,
                    response_summary=response_summary,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                )
            except Exception:
                pass

    async def _call_openai(self, messages, temperature, max_tokens) -> str:
        url = f"{self.base_url or 'https://api.openai.com/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_qwen(self, messages, temperature, max_tokens) -> str:
        url = (
            self.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ) + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model or "qwen-plus",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_baidu(self, messages, temperature, max_tokens) -> str:
        url = f"{self.base_url or 'https://aip.baidubce.com'}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        params = {"access_token": self.api_key}
        payload = {
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
            method="parse_problem",
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
        session_id: str = None,
    ) -> dict:
        history_text = "\n".join([
            f"Q{i+1}: {h['question']}\nA: {h['answer']}\n反馈: {h['feedback']}"
            for i, h in enumerate(history)
        ]) if history else "（这是第一步）"

        parsed_info = ""
        if parsed_problem:
            parsed_info = f"""
题目分析结果：
- 题目类型：{parsed_problem.get('problem_type', '未知')}
- 题目标题：{parsed_problem.get('title', '未知')}
- 已知条件：{', '.join(parsed_problem.get('known_conditions', []))}
- 求解目标：{parsed_problem.get('goal', '未知')}
- 涉及知识点：{', '.join(parsed_problem.get('key_concepts', []))}
- 建议步骤：{' → '.join(parsed_problem.get('suggested_steps', []))}
"""

        system_prompt = """你是一个专业的数学教育AI助手，擅长使用苏格拉底式教学法引导学生思考。

你的任务是：
1. 根据学生的当前进度和回答历史，生成一个引导性的问题
2. 问题应该帮助学生思考下一步该做什么，而不是直接给出答案
3. 提供4个选项（A/B/C/D），其中一个是正确思路，其他是常见错误或放弃态度
4. 对每个选项准备正确的反馈和错误时的温和提示

返回严格的JSON格式：
{
  "question": "引导性问题",
  "options": ["A. 正确思路选项", "B. 错误选项1", "C. 错误选项2", "D. 放弃选项"],
  "correct_index": 0,
  "success_feedback": "选择正确时的鼓励性反馈",
  "error_feedback": "选择错误时的温和提示",
  "explanation": "这一步的解释说明"
}

注意：
- 问题要具体到当前步骤，不要太笼统
- 错误选项要反映学生常见的错误思维
- 反馈要有启发性，帮助学生理解为什么对或错
- 只返回JSON，不要其他文字"""

        user_prompt = f"""数学题目：{problem}
当前进度：第{current_step + 1}步（共约{total_steps}步）
{parsed_info}
历史对话：
{history_text}

请为这一步生成苏格拉底式提问。"""

        response = await self.chat_completion(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            method="generate_socratic_question",
            session_id=session_id,
        )

        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                return result
        except (json.JSONDecodeError, KeyError):
            pass

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
            "error_feedback": "再想想看~ 提示一下...",
            "explanation": "这一步的关键在于...",
        }

    async def generate_final_solution(self, problem: str, history: list[dict], session_id: str = None) -> str:
        history_text = "\n".join([
            f"步骤{i+1}: {h['question']} -> 回答: {h['answer']}"
            for i, h in enumerate(history)
        ]) if history else "无历史记录"

        system_prompt = """你是一个专业的数学教育AI助手。根据学生的解题过程，给出完整的解题思路总结。

要求：
1. 用清晰的步骤展示完整解题过程
2. 结合学生在每一步的回答进行点评
3. 总结解题的关键方法和注意事项
4. 鼓励学生继续保持良好的思维习惯

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
            method="generate_final_solution",
            session_id=session_id,
        )


ai_service = AIService()
