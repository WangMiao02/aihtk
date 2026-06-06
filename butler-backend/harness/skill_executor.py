"""
Single Skill Harness — 六要素能力契约执行壳
文档映射：single-skill-harness-summary-autodrive.md §3

六要素：意图层 / 接口层 / 执行层 / 证据层 / 治理层 / 学习层
错误语义 5 分级：INVALID_INPUT / TRANSIENT_ERROR / DEPENDENCY_DOWN / PERMISSION_DENIED / POLICY_BLOCKED
"""

import asyncio, time, uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum


class ErrorClass(str, Enum):
    INVALID_INPUT    = "INVALID_INPUT"     # 参数错误，不重试
    TRANSIENT_ERROR  = "TRANSIENT_ERROR"   # 短暂故障，可重试
    DEPENDENCY_DOWN  = "DEPENDENCY_DOWN"   # 依赖不可用，降级等待
    PERMISSION_DENIED= "PERMISSION_DENIED" # 权限不足，人工处理
    POLICY_BLOCKED   = "POLICY_BLOCKED"    # 命中策略门禁，等待审批


class SideEffect(str, Enum):
    READ_ONLY              = "read-only"
    WRITE_STATE            = "write-state"
    EXTERNAL_ACTION        = "external-action"
    HUMAN_APPROVAL_REQUIRED= "human-approval-required"


@dataclass
class SkillResult:
    """Skill 执行结果——契约化输出，上层 Harness 可路由"""
    status:               str                   # "success" | "error" | "pending"
    data:                 dict                  = field(default_factory=dict)
    summary:              str                   = ""        # 摘要（渐进式加载第一层）
    error_class:          Optional[ErrorClass]  = None
    error_message:        Optional[str]         = None
    confidence:           float                 = 1.0
    trace_id:             str                   = field(default_factory=lambda: uuid.uuid4().hex[:8])
    recommended_next:     list[str]             = field(default_factory=list)  # 建议下游
    side_effect_level:    SideEffect            = SideEffect.READ_ONLY
    payload_size_tokens:  int                   = 0         # 可观测性：本次返回体积
    latency_ms:           int                   = 0


class SkillExecutor:
    """
    统一执行壳：
    1. 参数前置校验（fail-fast）
    2. 调用 handler（mock 或真实）
    3. 超时/重试控制
    4. 错误语义分级
    5. 审计日志（写入持久化由调用方负责）
    """

    def __init__(self, timeout_s: float = 10.0, max_retry: int = 2):
        self.timeout_s = timeout_s
        self.max_retry = max_retry

    async def execute(
        self,
        skill_name: str,
        handler: Callable,
        params: dict,
        required_fields: list[str] | None = None,
    ) -> SkillResult:

        # §3.1 意图层校验：必填字段（INVALID_INPUT 不重试）
        if required_fields:
            missing = [f for f in required_fields if f not in params]
            if missing:
                return SkillResult(
                    status="error",
                    error_class=ErrorClass.INVALID_INPUT,
                    error_message=f"缺少必填字段: {missing}",
                )

        # §3.3 执行层：超时 + 重试
        for attempt in range(self.max_retry + 1):
            t0 = time.monotonic()
            try:
                result: SkillResult = await asyncio.wait_for(
                    handler(params), timeout=self.timeout_s
                )
                result.latency_ms = int((time.monotonic() - t0) * 1000)
                return result
            except asyncio.TimeoutError:
                if attempt < self.max_retry:
                    await asyncio.sleep(0.3)
                    continue
                return SkillResult(
                    status="error",
                    error_class=ErrorClass.TRANSIENT_ERROR,
                    error_message=f"{skill_name} 执行超时（{self.timeout_s}s）",
                    latency_ms=int((time.monotonic() - t0) * 1000),
                )
            except Exception as e:
                return SkillResult(
                    status="error",
                    error_class=ErrorClass.DEPENDENCY_DOWN,
                    error_message=str(e),
                    latency_ms=int((time.monotonic() - t0) * 1000),
                )
