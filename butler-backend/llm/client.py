"""
LLM Client — 优先调本地模型，失败时 fallback 到预制回复
本地模型：Qwen3.5-27B · llama-server · port 38000 · OpenAI compat
"""

import asyncio, httpx
from config import LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT

# 意图路由 fallback 表（模型不可用时使用）
_FALLBACK_INTENT: dict[str, str] = {
    "订票":   "trip_reserver",
    "出差":   "trip_reserver",
    "上海":   "trip_reserver",
    "高铁":   "trip_reserver",
    "酒店":   "hotel_reserver",
    "叫车":   "ride_hailing",
    "寄养":   "pet_boarding",
    "吃":     "food_recommend",
    "按摩":   "massage_booking",
    "调价":   "promotion_advisor",
    "差评":   "review_manager",
}


class LLMClient:

    async def route_intent(self, text: str, scope: str = "C") -> str | None:
        """
        尝试调本地 LLM 做意图路由。
        失败时 fallback 到关键词规则。
        """
        try:
            result = await asyncio.wait_for(
                self._call_llm_intent(text, scope), timeout=LLM_TIMEOUT
            )
            return result
        except Exception:
            return self._fallback_intent(text)

    async def _call_llm_intent(self, text: str, scope: str) -> str | None:
        system = (
            "你是本地生活管家的意图路由器。根据用户输入，判断应该调用哪个Skill。\n"
            "只输出Skill的handler_key，不要其他内容。\n"
            f"可用Skill（scope={scope}）：trip_reserver, hotel_reserver, ride_hailing, "
            "pet_boarding, food_recommend, hair_salon, massage_booking, budget_manager, "
            "expense_reimbursement, morning_report, promotion_advisor, review_manager, "
            "maintenance_reminder, room_switch, campaign_advisor\n"
            "如果都不匹配，输出: none"
        )
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system",  "content": system},
                {"role": "user",    "content": text},
            ],
            "max_tokens": 20,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(
                f"{LLM_BASE_URL}/v1/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            return None if content == "none" else content

    def _fallback_intent(self, text: str) -> str | None:
        for kw, key in _FALLBACK_INTENT.items():
            if kw in text:
                return key
        return None
