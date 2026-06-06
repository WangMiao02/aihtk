"""
Single Agent Harness — Runtime Loop
文档映射：single-agent-harness-summary-autodrive.md §3.1

每轮循环：
  ① 读热状态  →  ② 状态机判断 phase  →  ③ 渐进式加载 Skill 索引（~200tok）
  →  ④ 意图路由  →  ⑤ 按需加载 Skill 主文件  →  ⑥ 调 LLM  →  ⑦ 触发 Skill Executor
  →  ⑧ 写回五层持久化  →  ⑨ RL 轨迹写入

渐进式加载三层：
  Layer 0 索引层：~200tok/skill，用于意图路由
  Layer 1 主文件层：~2000tok，命中后按需加载
  Layer 2 references：~1000tok，复杂分支时加载
"""

import asyncio
from typing import Callable, Awaitable

from harness.state_machine  import StateMachine, Phase
from harness.skill_executor import SkillExecutor, SkillResult
from agents.hub_director    import HubDirector
from skills.registry        import SkillRegistry
from soul.adapter           import SoulAdapter
from llm.client             import LLMClient
from persistence.store      import PersistenceStore
from rl.trajectory          import TrajectoryRecorder

SendFn = Callable[[dict], Awaitable[None]]


class AgentRuntimeLoop:

    def __init__(self, demo: str, soul: str,
                 store: PersistenceStore, recorder: TrajectoryRecorder):
        self.demo     = demo   # "C" | "B"
        self.soul     = soul
        self.store    = store
        self.recorder = recorder
        self.sm       = StateMachine()
        self.executor = SkillExecutor()
        self.registry = SkillRegistry()
        self.hub      = HubDirector(demo=demo, executor=self.executor, registry=self.registry)
        self.llm      = LLMClient()
        self.soul_ada = SoulAdapter()

    # ── 心跳入口（连接建立时 or 定时触发）────────────────────────────
    async def run_heartbeat(self, send: SendFn):
        """
        Heartbeat 主动推送：
        - 不需要用户开口
        - phase: idle → briefing
        """
        if self.sm.pending_approval:
            # 死规则：有待确认项时不重复打扰
            return

        self.sm.transition(Phase.BRIEFING)
        self.store.update_hot_state(self.demo, self.sm.to_dict())

        await send({"event": "phase_change", "from": "idle", "to": "briefing"})

        if self.demo == "C":
            await self._c_heartbeat(send)
        else:
            await self._b_heartbeat(send)

    # ── 用户消息入口 ──────────────────────────────────────────────────
    async def handle_message(self, msg: dict, send: SendFn):
        event = msg.get("event")

        if event == "option_select":
            await self._handle_option(msg.get("key", ""), send)
        elif event == "user_message":
            await self._handle_intent(msg.get("text", ""), send)

    # ── 意图处理（完整 runtime 循环）────────────────────────────────
    async def _handle_intent(self, text: str, send: SendFn):
        if not self.sm.can_execute():
            return

        self.sm.transition(Phase.EXECUTING)
        state_snapshot = self.sm.to_dict()
        self.store.update_hot_state(self.demo, state_snapshot)
        await send({"event": "phase_change", "from": self.sm.phase, "to": "executing"})

        # Layer 0：渐进式加载索引层
        await send({"event": "thinking", "lines": [
            "① 读取热状态…",
            "② 加载 Skill 索引层（~200tok，34个Skill）",
            "③ 意图路由中…",
        ], "duration": 1400})

        # 通过 Hub Director 分发到子 Agent 并联执行
        await self.hub.dispatch(text=text, soul=self.soul, send=send,
                                sm=self.sm, store=self.store, recorder=self.recorder)

    # ── 选项确认处理 ──────────────────────────────────────────────────
    async def _handle_option(self, key: str, send: SendFn):
        if not self.sm.is_waiting():
            return

        self.sm.transition(Phase.EXECUTING)
        self.store.update_hot_state(self.demo, self.sm.to_dict())
        await send({"event": "phase_change", "from": "awaiting_confirm", "to": "executing"})

        await self.hub.handle_confirm(key=key, soul=self.soul, send=send,
                                      sm=self.sm, store=self.store, recorder=self.recorder)

    # ── C 端心跳推送（早间播报）──────────────────────────────────────
    async def _c_heartbeat(self, send: SendFn):
        await asyncio.sleep(0.4)
        await send({"event": "skill_trace",
                    "skill": "heartbeat", "action": "加载早报模板", "status": "running"})
        await asyncio.sleep(0.6)
        await send({"event": "skill_trace",
                    "skill": "morning-briefing", "action": "推送晨间快讯", "status": "done"})
        await asyncio.sleep(0.3)
        soul_text = self.soul_ada.format(
            soul=self.soul,
            template="heartbeat_morning_c",
            data={}
        )
        await send({"event": "agent_text", "text": soul_text})
        self.sm.transition(Phase.IDLE)
        self.store.update_hot_state(self.demo, self.sm.to_dict())
        self.store.append_event(self.demo, "heartbeat_morning", {"soul": self.soul})

    # ── B 端心跳推送（晨间日报）──────────────────────────────────────
    async def _b_heartbeat(self, send: SendFn):
        await asyncio.sleep(0.4)
        await send({"event": "skill_trace",
                    "skill": "heartbeat", "action": "加载日报数据", "status": "running"})
        await asyncio.sleep(0.8)
        await send({"event": "skill_trace",
                    "skill": "morning-report", "action": "生成晨间日报", "status": "done"})
        await asyncio.sleep(0.3)

        from skills.b_skills import B_MORNING_REPORT_DATA
        await send({"event": "skill_card", "card": "DailyReportCard",
                    "payload": B_MORNING_REPORT_DATA})
        await asyncio.sleep(0.4)
        soul_text = self.soul_ada.format(
            soul=self.soul,
            template="heartbeat_morning_b",
            data=B_MORNING_REPORT_DATA
        )
        await send({"event": "agent_text", "text": soul_text})
        await send({"event": "options", "items": [
            {"key": "view_promo",   "label": "查看调价建议"},
            {"key": "skip_report",  "label": "好的知道了"},
        ]})
        self.sm.transition(Phase.AWAITING_CONFIRM)
        self.store.update_hot_state(self.demo, self.sm.to_dict())
        self.store.append_event(self.demo, "morning_report_sent", B_MORNING_REPORT_DATA)
