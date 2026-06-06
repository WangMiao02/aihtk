"""
Sub-Agents — 各专项子 Agent
文档映射：实现细节架构图.md LAYER 3 子 Agent

每个子 Agent 有自己的状态机（idle→running→done）
通过契约输出向 Hub Director 上报结果
"""

import asyncio
from harness.skill_executor import SkillExecutor, SkillResult
from skills.registry        import SkillRegistry
from typing import Callable, Awaitable

SendFn = Callable[[dict], Awaitable[None]]


class TripAgent:
    """出行子 Agent：trip-reserver + hotel-reserver + ride-hailing"""

    def __init__(self, executor: SkillExecutor, registry: SkillRegistry, handlers: dict):
        self.executor = executor
        self.registry = registry
        self.handlers = handlers
        self.phase    = "idle"  # 子 Agent 自有状态机

    async def run(self, params: dict, send: SendFn, mode: str = "silent") -> SkillResult:
        self.phase = "searching"
        result = await self.executor.execute(
            "trip-reserver", self.handlers["trip_reserver"], params)
        self.phase = "done"
        return result


class PetAgent:
    """宠物子 Agent：pet-boarding + pet-shop + pet-medical"""

    def __init__(self, executor: SkillExecutor, registry: SkillRegistry, handlers: dict):
        self.executor = executor
        self.registry = registry
        self.handlers = handlers
        self.phase    = "idle"

    async def check_boarding_needed(self, params: dict, send: SendFn,
                                    mode: str = "silent") -> SkillResult:
        """行程≥2天自动触发寄养检查"""
        self.phase = "checking"
        days = params.get("days", 1)
        if days >= 2:
            result = await self.executor.execute(
                "pet-boarding", self.handlers["pet_boarding"], params)
            self.phase = "done"
            return result
        self.phase = "idle"
        return SkillResult(status="skipped", data={}, summary="行程<2天，无需寄养")

    async def buy_carrier(self, params: dict) -> SkillResult:
        """寄养前自动检测是否需要太空箱"""
        return await self.executor.execute(
            "pet-shop", self.handlers["pet_shop"], params)


class FinanceAgent:
    """财务子 Agent：budget-manager + expense-reimbursement + coupon-claim"""

    def __init__(self, executor: SkillExecutor, registry: SkillRegistry, handlers: dict):
        self.executor = executor
        self.handlers = handlers
        self.phase    = "idle"

    async def record_silent(self, params: dict) -> SkillResult:
        """静默记账——用户无感知"""
        self.phase = "recording"
        result = await self.executor.execute(
            "budget-manager", self.handlers["budget_manager"], params)
        self.phase = "done"
        return result

    async def generate_expense(self, params: dict) -> SkillResult:
        """生成报销单"""
        return await self.executor.execute(
            "expense-reimbursement", self.handlers["expense_reimbursement"], params)


class BHotelAgent:
    """B 端民宿子 Agent：review + maintenance + room_switch + campaign"""

    def __init__(self, executor: SkillExecutor, registry: SkillRegistry, handlers: dict):
        self.executor = executor
        self.handlers = handlers
        self.phase    = "idle"

    async def handle_review(self, send: SendFn) -> SkillResult:
        self.phase = "processing_review"
        result = await self.executor.execute(
            "review-manager", self.handlers["review_manager"], {})
        await send({"event": "skill_trace", "skill": "review-manager",
                    "action": "差评回复草稿生成", "status": "done"})
        await send({"event": "skill_card", "card": "ReviewReplyCard",
                    "payload": result.data})
        self.phase = "done"
        return result

    async def handle_maintenance(self, send: SendFn) -> SkillResult:
        self.phase = "creating_workorder"
        result = await self.executor.execute(
            "maintenance-reminder", self.handlers["maintenance_reminder"], {})
        await asyncio.sleep(0.3)
        await send({"event": "skill_trace", "skill": "maintenance-reminder",
                    "action": "维修工单已创建·李师傅今日14:00", "status": "done"})
        await send({"event": "skill_card", "card": "MaintenanceCard",
                    "payload": result.data})
        self.phase = "done"
        return result

    async def handle_room_switch(self, params: dict, send: SendFn) -> SkillResult:
        self.phase = "switching_room"
        result = await self.executor.execute(
            "room-switch", self.handlers["room_switch"], params)
        await asyncio.sleep(0.3)
        await send({"event": "skill_trace", "skill": "room-switch",
                    "action": f"A201 {params.get('action','下架')}·防超卖护栏", "status": "done"})
        await send({"event": "skill_card", "card": "MaintenanceSwitchCard",
                    "payload": result.data})
        self.phase = "done"
        return result

    async def handle_campaign(self, send: SendFn) -> SkillResult:
        result = await self.executor.execute(
            "campaign-advisor", self.handlers["campaign_advisor"], {})
        await send({"event": "skill_trace", "skill": "campaign-advisor",
                    "action": "避暑季活动已报名", "status": "done"})
        await send({"event": "skill_card", "card": "CampaignCard",
                    "payload": result.data})
        return result
