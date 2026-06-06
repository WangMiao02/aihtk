"""
Single Agent Harness — 状态机
文档映射：single-agent-harness-summary-autodrive.md §3.2

Phase 流转规则（硬约束，不过 LLM）：
  idle → briefing          heartbeat 推送
  idle → executing         用户意图到达
  briefing → executing     用户响应心跳
  briefing → idle          超时/无响应
  executing → awaiting_confirm  Skill 执行完毕，需用户确认
  executing → settled      无需确认直接完成（静默 Skill）
  awaiting_confirm → executing  用户确认，触发下游 Skill
  awaiting_confirm → idle  用户取消
  settled → idle           本轮完成，重置
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class Phase(str, Enum):
    IDLE             = "idle"
    BRIEFING         = "briefing"
    EXECUTING        = "executing"
    AWAITING_CONFIRM = "awaiting_confirm"
    SETTLED          = "settled"


_VALID_TRANSITIONS: dict[Phase, list[Phase]] = {
    Phase.IDLE:             [Phase.BRIEFING, Phase.EXECUTING],
    Phase.BRIEFING:         [Phase.EXECUTING, Phase.IDLE],
    Phase.EXECUTING:        [Phase.AWAITING_CONFIRM, Phase.SETTLED, Phase.IDLE],
    Phase.AWAITING_CONFIRM: [Phase.EXECUTING, Phase.IDLE, Phase.SETTLED],
    Phase.SETTLED:          [Phase.IDLE],
}


@dataclass
class StateMachine:
    phase:            Phase          = Phase.IDLE
    active_skill:     Optional[str]  = None
    pending_approval: bool           = False   # 死规则：为 True 时不重复通知
    retry_count:      int            = 0
    pending_option:   Optional[str]  = None    # 等待用户选择的 key

    def transition(self, to: Phase) -> bool:
        """尝试流转，返回是否成功。失败说明违反状态机约束。"""
        if to in _VALID_TRANSITIONS[self.phase]:
            prev = self.phase
            self.phase = to
            if to == Phase.AWAITING_CONFIRM:
                self.pending_approval = True
            if to in (Phase.IDLE, Phase.SETTLED):
                self.pending_approval = False
                self.active_skill     = None
                self.retry_count      = 0
            return True
        return False

    def can_execute(self) -> bool:
        return self.phase in (Phase.IDLE, Phase.BRIEFING, Phase.EXECUTING)

    def is_waiting(self) -> bool:
        return self.phase == Phase.AWAITING_CONFIRM

    def to_dict(self) -> dict:
        return {
            "phase":            self.phase,
            "active_skill":     self.active_skill,
            "pending_approval": self.pending_approval,
            "retry_count":      self.retry_count,
        }
