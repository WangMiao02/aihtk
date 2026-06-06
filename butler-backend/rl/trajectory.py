"""
RL 轨迹收集器
文档映射：实现细节架构图.md LAYER 6 / agent-rl-concepts §4.4

每条轨迹：state_t → action_t → observation_t → reward_t → state_t+1

奖励函数（多指标联合，防 reward hacking）：
  R = w1·确认率 + w2·链路深度 - w3·步骤耗时 - w4·用户拒绝 - w5·LLM重试

轨迹持久化到 trajectories.jsonl（append-only）
"""

import json, os
from datetime import datetime, timezone
from config import DATA_DIR

_TRAJ_FILE = os.path.join(DATA_DIR, "trajectories.jsonl")

# 奖励权重
W1_CONFIRM_RATE   = 0.35
W2_CHAIN_DEPTH    = 0.25
W3_LATENCY_PENALTY= 0.15   # 超过 3s 开始扣分
W4_REJECT_PENALTY = 0.20
W5_RETRY_PENALTY  = 0.05


class TrajectoryRecorder:

    def record(
        self,
        demo:         str,
        state:        dict,
        action:       str,
        observation:  str,
        reward:       float | None = None,
        chain_depth:  int   = 1,
        latency_ms:   int   = 0,
        user_rejected:bool  = False,
        llm_retries:  int   = 0,
    ) -> dict:
        """记录一条轨迹并计算 reward"""

        if reward is None:
            reward = self._compute_reward(
                chain_depth, latency_ms, user_rejected, llm_retries)

        traj = {
            "ts":           datetime.now(timezone.utc).isoformat(),
            "demo":         demo,
            "state_t":      state,
            "action_t":     action,
            "observation_t":observation,
            "reward_t":     round(reward, 4),
            "meta": {
                "chain_depth":   chain_depth,
                "latency_ms":    latency_ms,
                "user_rejected": user_rejected,
                "llm_retries":   llm_retries,
            }
        }
        with open(_TRAJ_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(traj, ensure_ascii=False) + "\n")
        return traj

    def _compute_reward(
        self,
        chain_depth:   int,
        latency_ms:    int,
        user_rejected: bool,
        llm_retries:   int,
    ) -> float:
        """
        R = w1·confirm_rate + w2·depth_bonus - w3·latency_pen - w4·reject_pen - w5·retry_pen
        """
        confirm_rate  = 0.0 if user_rejected else 1.0
        depth_bonus   = min(chain_depth / 5.0, 1.0)     # 最多5个Skill满分
        latency_pen   = max(0.0, (latency_ms - 3000) / 10000)
        reject_pen    = 1.0 if user_rejected else 0.0
        retry_pen     = min(llm_retries * 0.3, 1.0)

        r = (W1_CONFIRM_RATE * confirm_rate
             + W2_CHAIN_DEPTH * depth_bonus
             - W3_LATENCY_PENALTY * latency_pen
             - W4_REJECT_PENALTY * reject_pen
             - W5_RETRY_PENALTY  * retry_pen)

        return max(0.0, min(1.0, r))

    def read_all(self) -> list:
        if not os.path.exists(_TRAJ_FILE):
            return []
        trajs = []
        with open(_TRAJ_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    trajs.append(json.loads(line))
                except Exception:
                    pass
        return trajs

    def summary(self) -> dict:
        trajs = self.read_all()
        if not trajs:
            return {"total": 0, "avg_reward": 0}
        rewards = [t["reward_t"] for t in trajs]
        return {
            "total":         len(trajs),
            "avg_reward":    round(sum(rewards) / len(rewards), 4),
            "max_reward":    max(rewards),
            "min_reward":    min(rewards),
        }
