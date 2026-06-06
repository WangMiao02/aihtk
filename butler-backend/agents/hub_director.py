"""
Multi-Agent Harness — Hub Director
文档映射：实现细节架构图.md LAYER 3

职责：
1. 读 working-memory（当前意图 + 已激活子Agent + 待确认项）
2. 根据意图决定派发策略（单意图直路由 / 复合意图并联 + barrier）
3. 等待子 Agent 上报（超时 8s 熔断降级，不阻塞整体）
4. 聚合结果 → 写 working-memory → 转交 Soul Adapter
5. 写 Hub 级事件日志
"""

import asyncio
from typing import Callable, Awaitable

from skills.registry         import SkillRegistry
from skills.c_skills         import C_HANDLERS
from skills.b_skills         import B_HANDLERS
from harness.skill_executor  import SkillExecutor, SkillResult
from soul.adapter            import SoulAdapter
from agents.sub_agents       import TripAgent, PetAgent, FinanceAgent, BHotelAgent

SendFn = Callable[[dict], Awaitable[None]]

# 存放当前会话的"待确认"上下文（简化：内存中）
_PENDING_CONTEXT: dict[str, dict] = {}


class HubDirector:

    def __init__(self, demo: str, executor: SkillExecutor, registry: SkillRegistry):
        self.demo      = demo
        self.executor  = executor
        self.registry  = registry
        self.soul_ada  = SoulAdapter()
        self.handlers  = {**C_HANDLERS, **B_HANDLERS}

        # 子 Agent 实例
        self.trip_agent    = TripAgent(executor, registry, self.handlers)
        self.pet_agent     = PetAgent(executor, registry, self.handlers)
        self.finance_agent = FinanceAgent(executor, registry, self.handlers)
        self.hotel_agent   = BHotelAgent(executor, registry, self.handlers)

    # ── 意图分发入口 ────────────────────────────────────────────────────
    async def dispatch(self, text: str, soul: str, send: SendFn,
                       sm, store, recorder):
        # Layer 0 意图路由
        intent_key = self.registry.resolve_intent(text, scope=self.demo)

        # LLM fallback: 未命中规则时用 mock LLM 判断
        if not intent_key:
            from llm.client import LLMClient
            llm = LLMClient()
            intent_key = await llm.route_intent(text, self.demo)

        if not intent_key:
            await send({"event": "agent_text",
                        "text": self.soul_ada.format(soul, "no_intent", {})})
            sm.transition("idle")
            return

        # Layer 1 按需加载并发送 skill_trace
        skill_meta = self.registry.get_skill_by_handler(intent_key)
        await send({"event": "skill_trace",
                    "skill": skill_meta["name"] if skill_meta else intent_key,
                    "action": "加载主文件(~2000tok)·执行",
                    "status": "running"})

        # 根据 intent 路由到对应子 Agent（体现多 Agent 并联）
        if self.demo == "C":
            await self._dispatch_c(intent_key, text, soul, send, sm, store, recorder)
        else:
            await self._dispatch_b(intent_key, text, soul, send, sm, store, recorder)

    # ── C 端路由 ────────────────────────────────────────────────────────
    async def _dispatch_c(self, intent_key: str, text: str, soul: str,
                          send: SendFn, sm, store, recorder):
        if intent_key == "trip_reserver":
            # 出行意图：并联触发 出行Agent + 宠物Agent（行程≥2天）
            await send({"event": "thinking", "lines": [
                "④ 意图命中: trip-reserver",
                "⑤ 加载主文件 (~2000tok)…",
                "⑥ 检测到养宠用户：并联触发 出行Agent + 宠物Agent",
            ], "duration": 1200})

            # 并联执行（体现 Multi-Agent Harness barrier 模式）
            trip_task = asyncio.create_task(
                self.trip_agent.run({"text": text}, send, "silent"))
            pet_task  = asyncio.create_task(
                self.pet_agent.check_boarding_needed({"days": 3}, send, "silent"))

            trip_result, pet_result = await asyncio.gather(
                asyncio.wait_for(trip_task, timeout=8),
                asyncio.wait_for(pet_task,  timeout=8),
                return_exceptions=True
            )

            # 输出卡片
            if isinstance(trip_result, SkillResult) and trip_result.status == "success":
                await send({"event": "skill_trace", "skill": "trip-reserver",
                            "action": "车次查询完成", "status": "done"})
                await send({"event": "skill_card", "card": "TripBooking",
                            "payload": trip_result.data})
                await asyncio.sleep(0.3)

            # Soul Adapter 格式化主回复
            reply = self.soul_ada.format(soul, "trip_found", {
                "trip": trip_result.data if isinstance(trip_result, SkillResult) else {},
                "pet":  pet_result.data  if isinstance(pet_result,  SkillResult) else {},
            })
            await send({"event": "agent_text", "text": reply})
            await send({"event": "options", "items": [
                {"key": "confirm_trip_pet_hotel", "label": "都订上"},
                {"key": "only_trip",              "label": "先只订票"},
            ]})

            # 写持久化 + RL
            sm.transition("awaiting_confirm")
            sm.active_skill = "trip-reserver"
            store.update_hot_state(self.demo, sm.to_dict())
            store.append_event(self.demo, "trip_intent_detected", {"text": text})
            _PENDING_CONTEXT[self.demo] = {
                "intent": "trip_reserver",
                "trip_data": trip_result.data if isinstance(trip_result, SkillResult) else {},
            }
            recorder.record(self.demo, sm.to_dict(),
                            "trip_reserver+pet_boarding", "awaiting_confirm",
                            reward=None)
            await send({"event": "phase_change", "from": "executing", "to": "awaiting_confirm"})

        elif intent_key == "food_recommend":
            result = await self.executor.execute(
                "food-recommend", self.handlers["food_recommend"], {})
            await send({"event": "skill_trace", "skill": "food-recommend",
                        "action": "推荐完成", "status": "done"})
            await send({"event": "skill_card", "card": "LunchRecommend",
                        "payload": result.data})
            reply = self.soul_ada.format(soul, "food_found", result.data)
            await send({"event": "agent_text", "text": reply})
            sm.transition("settled")
            store.update_hot_state(self.demo, sm.to_dict())
            recorder.record(self.demo, sm.to_dict(), intent_key, "settled", reward=0.75)
            await send({"event": "phase_change", "from": "executing", "to": "settled"})

        else:
            # 通用单 Skill 执行
            handler = self.handlers.get(intent_key)
            if not handler:
                await send({"event": "agent_text",
                            "text": self.soul_ada.format(soul, "no_intent", {})})
                return
            result = await self.executor.execute(intent_key, handler, {})
            skill_meta = self.registry.get_skill_by_handler(intent_key)
            card_name  = _INTENT_TO_CARD.get(intent_key, "AgentCard")
            await send({"event": "skill_trace",
                        "skill": skill_meta["name"] if skill_meta else intent_key,
                        "action": "执行完成", "status": "done"})
            await send({"event": "skill_card", "card": card_name, "payload": result.data})
            reply = self.soul_ada.format(soul, "generic_done", result.data)
            await send({"event": "agent_text", "text": reply})
            sm.transition("settled")
            store.update_hot_state(self.demo, sm.to_dict())
            recorder.record(self.demo, sm.to_dict(), intent_key, "settled",
                            reward=result.confidence * 0.8)
            await send({"event": "phase_change", "from": "executing", "to": "settled"})

    # ── B 端路由 ────────────────────────────────────────────────────────
    async def _dispatch_b(self, intent_key: str, text: str, soul: str,
                          send: SendFn, sm, store, recorder):
        if intent_key == "review_manager":
            # 差评：并联触发 review_manager + maintenance + room_switch
            await send({"event": "thinking", "lines": [
                "④ 意图命中: review_manager",
                "⑤ 差评事件：并联触发 回复/维修/下架 三路 Skill",
                "⑥ Hub Director 广播事件到三个子 Agent",
            ], "duration": 1400})

            tasks = [
                asyncio.create_task(self.hotel_agent.handle_review(send)),
                asyncio.create_task(self.hotel_agent.handle_maintenance(send)),
                asyncio.create_task(self.hotel_agent.handle_room_switch({"action": "下架"}, send)),
            ]
            results = await asyncio.gather(*[
                asyncio.wait_for(t, timeout=8) for t in tasks
            ], return_exceptions=True)

            reply = self.soul_ada.format(soul, "review_handled", {})
            await send({"event": "agent_text", "text": reply})
            await send({"event": "options", "items": [
                {"key": "confirm_review_all", "label": "全部确认执行"},
                {"key": "only_reply",         "label": "只发回复"},
            ]})
            sm.transition("awaiting_confirm")
            store.update_hot_state(self.demo, sm.to_dict())
            _PENDING_CONTEXT[self.demo] = {"intent": "review_manager"}
            recorder.record(self.demo, sm.to_dict(), "review_manager", "awaiting_confirm")
            await send({"event": "phase_change", "from": "executing", "to": "awaiting_confirm"})

        elif intent_key == "promotion_advisor":
            result = await self.executor.execute(
                "promotion-advisor", self.handlers["promotion_advisor"], {})
            await send({"event": "skill_trace", "skill": "promotion-advisor",
                        "action": "调价分析完成", "status": "done"})
            await send({"event": "skill_card", "card": "PromoAdvisorCard",
                        "payload": result.data})
            reply = self.soul_ada.format(soul, "promo_advice", result.data)
            await send({"event": "agent_text", "text": reply})
            await send({"event": "options", "items": [
                {"key": "adopt_promo", "label": "采纳·立即调价"},
                {"key": "skip_promo",  "label": "暂时不调"},
            ]})
            sm.transition("awaiting_confirm")
            store.update_hot_state(self.demo, sm.to_dict())
            _PENDING_CONTEXT[self.demo] = {"intent": "promotion_advisor", "data": result.data}
            recorder.record(self.demo, sm.to_dict(), "promotion_advisor", "awaiting_confirm")
            await send({"event": "phase_change", "from": "executing", "to": "awaiting_confirm"})

        else:
            handler = self.handlers.get(intent_key)
            if not handler:
                await send({"event": "agent_text",
                            "text": self.soul_ada.format(soul, "no_intent", {})})
                return
            result = await self.executor.execute(intent_key, handler, {})
            card   = _INTENT_TO_CARD.get(intent_key, "AgentCard")
            await send({"event": "skill_card", "card": card, "payload": result.data})
            await send({"event": "agent_text",
                        "text": self.soul_ada.format(soul, "generic_done", result.data)})
            sm.transition("settled")
            store.update_hot_state(self.demo, sm.to_dict())
            recorder.record(self.demo, sm.to_dict(), intent_key, "settled",
                            reward=result.confidence * 0.8)
            await send({"event": "phase_change", "from": "executing", "to": "settled"})

    # ── 用户确认处理 ─────────────────────────────────────────────────────
    async def handle_confirm(self, key: str, soul: str, send: SendFn,
                             sm, store, recorder):
        ctx = _PENDING_CONTEXT.get(self.demo, {})
        intent = ctx.get("intent", "")

        if key == "confirm_trip_pet_hotel":
            await self._confirm_trip_full(soul, send, sm, store, recorder)
        elif key == "only_trip":
            await self._confirm_trip_only(soul, send, sm, store, recorder)
        elif key == "adopt_promo":
            await self._confirm_promo(soul, send, sm, store, recorder)
        elif key == "confirm_review_all":
            await self._confirm_review(soul, send, sm, store, recorder)
        elif key == "view_promo":
            await self._dispatch_b("promotion_advisor", "", soul, send, sm, store, recorder)
        elif key in ("skip_report", "skip_promo", "only_reply"):
            reply = self.soul_ada.format(soul, "skip_ok", {})
            await send({"event": "agent_text", "text": reply})
            sm.transition("idle")
            store.update_hot_state(self.demo, sm.to_dict())
            await send({"event": "phase_change", "from": "executing", "to": "idle"})
        else:
            sm.transition("idle")

    # ── 确认：订全部（出行+宠物+酒店）────────────────────────────────────
    async def _confirm_trip_full(self, soul, send, sm, store, recorder):
        await send({"event": "thinking", "lines": [
            "用户确认 → 触发下游 Skill 链",
            "pet-boarding + hotel-reserver + ride-hailing 并联执行",
            "budget-manager 静默记账",
        ], "duration": 1500})

        # 并联执行三路下游
        boarding = asyncio.create_task(
            self.executor.execute("pet-boarding", self.handlers["pet_boarding"], {}))
        hotel    = asyncio.create_task(
            self.executor.execute("hotel-reserver", self.handlers["hotel_reserver"], {}))
        ride     = asyncio.create_task(
            self.executor.execute("ride-hailing", self.handlers["ride_hailing"],
                                  {"context": "departure"}))

        r_boarding, r_hotel, r_ride = await asyncio.gather(boarding, hotel, ride)

        await send({"event": "skill_trace", "skill": "pet-boarding",
                    "action": "散养位预订", "status": "done"})
        await send({"event": "skill_card", "card": "PetBoarding",
                    "payload": r_boarding.data})
        await asyncio.sleep(0.3)

        await send({"event": "skill_trace", "skill": "hotel-reserver",
                    "action": "全季虹桥预订", "status": "done"})
        await send({"event": "skill_card", "card": "HotelBooking",
                    "payload": r_hotel.data})
        await asyncio.sleep(0.3)

        await send({"event": "skill_trace", "skill": "ride-hailing",
                    "action": "6:10 叫车已预约", "status": "done"})
        await send({"event": "skill_card", "card": "RideBooking",
                    "payload": r_ride.data})
        await asyncio.sleep(0.2)

        # 静默记账
        await self.executor.execute("budget-manager", self.handlers["budget_manager"], {})
        await send({"event": "skill_trace", "skill": "budget-manager",
                    "action": "静默记账 ¥1,846", "status": "done"})

        reply = self.soul_ada.format(soul, "all_booked", {})
        await send({"event": "agent_text", "text": reply})
        await send({"event": "snapshot_update", "data": {
            "date": "6月4日 周三", "room": "全季虹桥·标准大床",
            "total": "¥1,846",     "car":  "6:10 叫车已约",
        }})
        await send({"event": "timeline_add", "title": "出行链路完成",
                    "desc": "5个Skill·3分钟全搞定", "dot": "green"})
        await send({"event": "rl_recorded", "reward": 0.92, "chain_depth": 5})

        sm.transition("settled")
        store.update_hot_state(self.demo, sm.to_dict())
        store.append_event(self.demo, "trip_full_booked",
                           {"skills": ["trip","pet","hotel","ride","budget"]})
        recorder.record(self.demo, sm.to_dict(), "confirm_trip_full", "settled", reward=0.92)
        await send({"event": "phase_change", "from": "executing", "to": "settled"})

    async def _confirm_trip_only(self, soul, send, sm, store, recorder):
        reply = self.soul_ada.format(soul, "trip_only_ok", {})
        await send({"event": "agent_text", "text": reply})
        sm.transition("settled")
        store.update_hot_state(self.demo, sm.to_dict())
        recorder.record(self.demo, sm.to_dict(), "confirm_trip_only", "settled", reward=0.6)
        await send({"event": "phase_change", "from": "executing", "to": "settled"})

    async def _confirm_promo(self, soul, send, sm, store, recorder):
        await send({"event": "skill_trace", "skill": "promotion-advisor",
                    "action": "88折生效·全渠道同步", "status": "done"})
        result = await self.executor.execute(
            "room-switch", self.handlers["room_switch"],
            {"action": "满房提示"})
        await send({"event": "skill_card", "card": "FullHouseSwitchCard",
                    "payload": result.data})
        reply = self.soul_ada.format(soul, "promo_adopted", {})
        await send({"event": "agent_text", "text": reply})
        await send({"event": "snapshot_update", "data": {
            "occupancy": "87%", "revenue": "¥2,840",
            "discount":  "88折", "operationStatus": "88折已生效 ✓",
        }})
        await send({"event": "timeline_add", "title": "调价已生效",
                    "desc": "88折·全渠道同步", "dot": "green"})
        sm.transition("settled")
        store.update_hot_state(self.demo, sm.to_dict())
        recorder.record(self.demo, sm.to_dict(), "adopt_promo", "settled", reward=0.85)
        await send({"event": "phase_change", "from": "executing", "to": "settled"})

    async def _confirm_review(self, soul, send, sm, store, recorder):
        await send({"event": "agent_text",
                    "text": self.soul_ada.format(soul, "review_confirmed", {})})
        await send({"event": "timeline_add", "title": "差评处理完成",
                    "desc": "回复+维修+下架 并联执行", "dot": "green"})
        sm.transition("settled")
        store.update_hot_state(self.demo, sm.to_dict())
        recorder.record(self.demo, sm.to_dict(), "confirm_review", "settled", reward=0.88)
        await send({"event": "phase_change", "from": "executing", "to": "settled"})


# intent → 前端卡片名映射
_INTENT_TO_CARD: dict[str, str] = {
    "trip_reserver":       "TripBooking",
    "hotel_reserver":      "HotelBooking",
    "ride_hailing":        "RideBooking",
    "pet_boarding":        "PetBoarding",
    "pet_shop":            "PetShop",
    "budget_manager":      "DayBudget",
    "expense_reimbursement": "ExpenseClassify",
    "food_recommend":      "LunchRecommend",
    "hair_salon":          "HairSalon",
    "massage_booking":     "MassageBooking",
    "morning_report":      "DailyReportCard",
    "promotion_advisor":   "PromoAdvisorCard",
    "review_manager":      "ReviewReplyCard",
    "maintenance_reminder":"MaintenanceCard",
    "room_switch":         "RoomRelistCard",
    "campaign_advisor":    "CampaignCard",
}
