# 全天候私人管家 · 项目说明

基于 OpenClaw Skill 机制的本地生活 AI 管家系统。  
AI 不再是指令执行者，而是能主动感知用户生活节奏、跨场景链式协作的全天候管家。

---

## 快速启动

### 前置要求

- Python 3.10+
- Node.js 18+
- pnpm 或 npm

### 第一步：启动后端

```powershell
cd d:\aihackton\butler-backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

后端启动成功后输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 第二步：启动前端

```powershell
cd d:\aihackton\agent-demo-v4-refactor
npm install       # 或 pnpm install
npm run dev       # 或 pnpm dev
```

前端默认运行在 `http://localhost:5173`

### 第三步（可选）：启动本地模型

```powershell
cd d:\aihackton\qwenclaw-main
# 参考 llama_server_start.md
# llama-server --model Qwen3.5-27B.Q4_K_M.gguf --host 0.0.0.0 --port 38000 ...
```

> 模型不启动时后端自动 fallback 到关键词路由，演示不受影响。

---

## 项目结构总览

```
d:\aihackton\
├── butler-backend/           # FastAPI 后端（Agent Harness 系统）
├── agent-demo-v4-refactor/   # React 前端（对话 UI + Skill 卡片）
├── qwenclaw-main/            # Qwen3.5-27B 本地模型（GGUF）
├── openclaw-main/            # OpenClaw 源码（Agent 运行时）
├── openclaw_runtime_full_snapshot/  # OpenClaw 运行时配置快照
├── heartbeat-learning-agent-workspace/  # Heartbeat 学习 Agent 工作区
├── 实现细节架构图.md          # 完整系统架构图（7层）
└── zhangzhangreadme.MD       # 本文件
```

---

## 后端详解 `butler-backend/`

### 架构层次（对应三份文档范式）

```
main.py                         ← FastAPI 入口，WebSocket 路由
├── harness/                    ← Single Agent Harness（文档1+2）
│   ├── state_machine.py        ← 状态机（5个 phase·硬约束流转）
│   ├── skill_executor.py       ← Skill 执行壳（六要素契约·5级错误）
│   └── runtime_loop.py         ← runtime 循环（渐进式加载三层）
├── agents/                     ← Multi-Agent Harness（文档2）
│   ├── hub_director.py         ← Hub Director（并联·熔断·事件广播）
│   └── sub_agents.py           ← 4个子 Agent（出行/宠物/财务/B端）
├── skills/                     ← Skill 层
│   ├── registry.py             ← 16个 Skill 索引（~200tok/skill）
│   ├── c_skills.py             ← C端10个 Skill mock 实现
│   └── b_skills.py             ← B端6个 Skill mock 实现
├── soul/                       ← Soul 人格层
│   ├── configs.py              ← 6套 Soul 模板（C端3套+B端3套）
│   └── adapter.py              ← Soul 适配器（与 Skill 彻底解耦）
├── llm/
│   └── client.py               ← LLM 客户端（优先本地模型·fallback规则）
├── persistence/
│   └── store.py                ← 五层持久化（JSON 文件）
├── rl/
│   └── trajectory.py           ← RL 轨迹收集（多指标奖励函数）
├── data/                       ← 运行时数据目录（自动创建）
│   ├── hot_state_C.json        ← 热状态层（C端）
│   ├── hot_state_B.json        ← 热状态层（B端）
│   ├── event_log.jsonl         ← 历史事件层（append-only）
│   ├── trajectories.jsonl      ← RL 轨迹（append-only）
│   ├── stable_config.json      ← 长期稳定层（用户偏好·策略规则）
│   └── artifacts/              ← 产物层（报销单·日报）
├── config.py                   ← 全局配置（LLM地址·端口·超时）
├── requirements.txt            ← Python 依赖
└── start.ps1                   ← Windows 启动脚本
```

---

### 关键文件说明

#### `harness/state_machine.py` — 状态机

5个 phase，硬约束流转，不过 LLM：

```
idle → briefing         heartbeat 主动推送
idle → executing        用户意图到达
executing → awaiting_confirm   Skill 执行完毕，等用户确认
awaiting_confirm → executing   用户确认，触发下游 Skill
settled → idle          本轮完成
```

`pending_approval` 为 `True` 时死规则抑制重复通知，不调 LLM。

---

#### `harness/skill_executor.py` — Skill 执行壳

每个 Skill 执行时走六要素：

| 层 | 内容 |
|---|---|
| 意图层 | 必填字段前置校验（fail-fast） |
| 接口层 | 结构化 SkillResult 输出 |
| 执行层 | timeout 10s · retry 2次 · idempotency |
| 证据层 | 摘要先返回，trace_id 按需拉取明细 |
| 治理层 | side_effect 分级声明 |
| 学习层 | 控制写入哪一层持久化 |

错误 5 分级（上层状态机可路由）：
- `INVALID_INPUT` → 不重试
- `TRANSIENT_ERROR` → 可重试
- `DEPENDENCY_DOWN` → 降级等待
- `PERMISSION_DENIED` → 人工处理
- `POLICY_BLOCKED` → 等待审批

---

#### `harness/runtime_loop.py` — Agent runtime 循环

每次被 heartbeat 或用户消息唤醒后执行一轮：

```
① 读热状态  →  ② 状态机判断 phase
→  ③ 渐进式加载 Skill 索引（~200tok）
→  ④ 意图路由
→  ⑤ 按需加载 Skill 主文件（~2000tok）
→  ⑥ 调 LLM（Qwen3.5-27B or fallback）
→  ⑦ 触发 Skill Executor
→  ⑧ 写回五层持久化
→  ⑨ RL 轨迹写入
```

---

#### `agents/hub_director.py` — Multi-Agent Hub

负责意图分发和多 Agent 并联调度：

- **单意图** → 直路由到目标子 Agent
- **复合意图**（出行+宠物）→ 并联触发 + barrier 聚合，总耗时 = max(各Agent)
- **被动事件**（差评/heartbeat）→ 事件广播，订阅的 Agent 自动接收
- **熔断降级**：单 Agent 超 8s 不阻塞整体，标记 pending 下轮补齐

---

#### `agents/sub_agents.py` — 子 Agent

| 子 Agent | 职责 | 覆盖 Skill |
|---|---|---|
| `TripAgent` | 出行预订 | trip-reserver |
| `PetAgent` | 宠物服务 | pet-boarding · pet-shop |
| `FinanceAgent` | 财务管理 | budget-manager · expense-reimbursement |
| `BHotelAgent` | B端民宿 | review · maintenance · room-switch · campaign |

每个子 Agent 有自己的状态机（`idle→running→done`）。

---

#### `skills/registry.py` — Skill 索引注册表

16个 Skill 的索引（渐进式加载 Layer 0，约 200tok/skill）：

**C端（10个）**

| Skill | 中文 | 触发词 |
|---|---|---|
| trip-reserver | 出行订票 | 订票/查票/出差/去XX |
| hotel-reserver | 订酒店 | 酒店/住哪/订房 |
| ride-hailing | 一键打车 | 叫车/打车/滴滴 |
| pet-boarding | 宠物寄养 | 寄养/猫/豆豆/宠物 |
| pet-shop | 宠物用品 | 寄养前自动触发 |
| budget-manager | 预算管家 | 静默记账（无感） |
| expense-reimbursement | 报销 | 报销/出差费用 |
| food-recommend | 外卖推荐 | 吃什么/午餐/外卖 |
| hair-salon | 美发预约 | 理发/剪头/发型 |
| massage-booking | 按摩预约 | 按摩/推拿/放松 |

**B端（6个）**

| Skill | 中文 | 触发 |
|---|---|---|
| morning-report | 晨间日报 | 每日 heartbeat |
| promotion-advisor | 调价建议 | 竞品监控联动 |
| review-manager | 差评处理 | 差评事件 |
| maintenance-reminder | 维修工单 | 差评联动 |
| room-switch | 房态管理 | 差评/满房/维修联动 |
| campaign-advisor | 活动顾问 | 平台活动推送 |

---

#### `soul/configs.py` — 6套 Soul 配置

| Soul Key | 适用人群 | 风格 |
|---|---|---|
| `pet_owner` | 养宠人士 | 温暖俏皮·记宠物名·主动关联 |
| `business` | 商旅人士 | 结论先行·高密度·不寒暄 |
| `elderly` | 银发人群 | 大白话·最多2选项·付款二确认 |
| `food_merchant` | 外卖商家 | 数据驱动·行动导向·预警前置 |
| `hotel_merchant` | 标准酒店 | 专业术语·建议有据·长线视角 |
| `homestay` | 民宿商家 | 感性+理性·内容创作·审美共鸣 |

换 Soul 只换配置文件，Skill 代码零改动。

---

#### `rl/trajectory.py` — RL 轨迹收集

每次 Skill 执行自动记录一条轨迹：

```json
{
  "state_t":   { "phase": "executing", "active_skill": "trip-reserver" },
  "action_t":  "trip_reserver+pet_boarding",
  "observation_t": "awaiting_confirm",
  "reward_t":  0.87,
  "meta": { "chain_depth": 5, "latency_ms": 1200 }
}
```

奖励函数（多指标联合，防 reward hacking）：

```
R = 0.35·确认率 + 0.25·链路深度 - 0.15·延迟惩罚 - 0.20·用户拒绝 - 0.05·LLM重试
```

轨迹写入 `data/trajectories.jsonl`，可通过 `GET /api/trajectories` 查看。

---

#### `persistence/store.py` — 五层持久化

| 层 | 文件 | 特点 |
|---|---|---|
| 热状态层 | `hot_state_{demo}.json` | 高频读写·当前 phase·active skill |
| 长期稳定层 | `stable_config.json` | 用户偏好·Soul配置·策略规则 |
| 历史事件层 | `event_log.jsonl` | append-only·时序可溯·可审计 |
| 语义召回层 | （演示阶段跳过）| 相似案例检索 |
| 产物层 | `artifacts/*.json` | 报销单·日报·诊断报告 |

---

### API 接口

| 接口 | 说明 |
|---|---|
| `WS /ws/{demo}/{soul}` | WebSocket 主连接，demo=C/B，soul=pet_owner/business/... |
| `POST /api/heartbeat/{demo}` | 手动触发心跳（演示按钮用） |
| `GET /api/state/{demo}` | 查看当前热状态 |
| `GET /api/trajectories` | 查看 RL 轨迹记录 |

---

## 前端详解 `agent-demo-v4-refactor/`

```
src/
├── hooks/
│   └── useAgentSocket.js      ← WebSocket hook（连接·事件分发·发送）
├── demos/
│   ├── CDemo.jsx              ← C端演示（WebSocket 事件驱动·全替换）
│   └── BDemo.jsx              ← B端演示（WebSocket 事件驱动·全替换）
├── components/
│   ├── SharedUI.jsx           ← 通用组件（ChatBubble·ThinkingChain·SkillTrace·AgentCard）
│   ├── CCards.jsx             ← C端卡片（订票·酒店·打车·叫车）
│   └── BCards.jsx             ← B端卡片（日报·调价·差评·维修·活动）
├── data/
│   ├── cDemoData.js           ← C端数据常量（和后端 c_skills.py 对齐）
│   └── bDemoData.js           ← B端数据常量（和后端 b_skills.py 对齐）
├── App.jsx                    ← 根组件（B/C 双 Tab·快照·时间线）
└── utils.js                   ← sleep / nowTime 工具函数
.env                           ← VITE_WS_BASE=ws://localhost:8000
```

### WebSocket 事件协议

后端 → 前端（服务端推送）：

| event | 说明 | 前端行为 |
|---|---|---|
| `phase_change` | 状态机流转 | 清除选项/更新指示器 |
| `thinking` | ThinkingChain 数据 | 渲染推理过程动画 |
| `skill_trace` | Skill 执行状态 | 更新顶部 SkillTrace 栏 |
| `agent_text` | Agent 回复文本 | 显示打字效果后渲染气泡 |
| `skill_card` | Skill 结果卡片 | 按 card 类型渲染对应组件 |
| `options` | 选项按钮列表 | 渲染确认按钮组 |
| `snapshot_update` | 右侧快照数据更新 | 更新行程/经营快照面板 |
| `timeline_add` | 新增时间线节点 | 事件时间线追加 |
| `rl_recorded` | RL 轨迹得分 | 控制台打印（可扩展为 UI 展示） |

前端 → 后端（用户操作）：

| event | 说明 |
|---|---|
| `user_message` | 用户输入文本 |
| `option_select` | 用户点击选项按钮（key） |

---

## 模型层 `qwenclaw-main/`

```
qwenclaw-main/
├── Qwen3.5-27B.Q4_K_M.gguf   ← 本地模型文件（~18GB）
├── llama_server_start.md      ← 启动命令参考
├── docker_start.md            ← Docker 启动方式
└── README.md
```

**四个微调方向（针对本地生活场景）：**

| 任务 | 方法 | 效果 |
|---|---|---|
| 本地生活意图识别 | SFT | 模糊意图识别 +23pp（61%→84%） |
| Skill 链路规划 | CoT SFT | 链路完整触发率 +31pp（52%→83%） |
| Soul 语气迁移 | DPO | Soul 风格合规率 +41pp（44%→85%） |
| 幻觉抑制 | 负样本 SFT | 领域幻觉率 -67%（18%→6%） |

**启动命令：**

```bash
llama-server \
    --model ./Qwen3.5-27B.Q4_K_M.gguf \
    --temp 0.6 --top-p 0.95 --top-k 20 \
    --host 0.0.0.0 --port 38000 \
    --ctx-size 131072 \
    --flash-attn on --kv-unified \
    --cache-type-k q8_0 --cache-type-v q8_0
```

接口：OpenAI compat `http://localhost:38000/v1/chat/completions`

---

## 运行时配置 `openclaw_runtime_full_snapshot/`

```
openclaw_runtime_full_snapshot/
├── .openclaw-dev/
│   ├── openclaw.json          ← OpenClaw 运行时配置（agent·heartbeat·provider）
│   ├── agents/dev/sessions/   ← 历史会话记录
│   └── tasks/runs.sqlite      ← 任务执行记录
└── workspace-dev/
    ├── AGENTS.md              ← Agent 运行规则
    ├── IDENTITY.md            ← C3PO agent 身份定义
    ├── SOUL.md                ← Soul 人格描述
    ├── TOOLS.md               ← 可用工具说明
    └── USER.md                ← 用户 profile
```

---

## Heartbeat 学习 Agent `heartbeat-learning-agent-workspace/`

独立的学习路径推荐 Agent，与管家产品解耦，演示 heartbeat 范式：

```
├── HEARTBEAT.md               ← 心跳运行协议
├── IDENTITY.md                ← Agent 身份（Learning Route Heartbeat Agent）
├── MEMORY.md                  ← 持久记忆规则
├── skills/                    ← 6个学习类 Skill
│   ├── internal-doc-discovery/
│   ├── external-source-discovery/
│   ├── topic-relevance-ranking/
│   ├── learning-choice-synthesis/
│   ├── feedback-to-memory/
│   └── memory-hygiene/
├── state/
│   ├── learning-state.json    ← 学习路径当前状态
│   └── eval-metrics.json      ← 质量评估指标
└── docs/
    ├── single-agent-harness-summary-autodrive.md   ← Single Agent Harness 范式文档
    ├── single-skill-harness-summary-autodrive.md   ← Single Skill Harness 范式文档
    └── agent-rl-concepts-autodrive.md              ← Agent + RL 概念文档
```

---

## 架构文档

| 文件 | 说明 |
|---|---|
| `实现细节架构图.md` | 完整 7 层系统架构图，含执行流·层间关系·工程亮点速查 |
| `heartbeat-learning-agent-workspace/docs/` | Single Skill/Agent Harness + RL 三份核心范式文档 |
| `openclaw-main/AGENTS.md` | OpenClaw 工程规范（根目录） |
| `openclaw-main/VISION.md` | OpenClaw 产品愿景 |

---

## 演示说明

### C端：Kevin 出差场景

连接 WebSocket `ws://localhost:8000/ws/C/pet_owner`，系统自动触发晨间推送。

输入示例（任选一条）：
- `帮我订下周去上海的票` → 触发 trip→pet→hotel→ride→budget 5个 Skill 链
- `中午吃什么` → 触发 food-recommend + coupon-claim
- `帮我约个按摩` → 触发 massage-booking

### B端：林姐民宿场景

连接 WebSocket `ws://localhost:8000/ws/B/homestay`，系统自动推送晨间日报。

输入示例：
- `帮我处理差评` → 并联触发 review+maintenance+room-switch 三路 Skill
- `查看调价建议` → 触发 promotion-advisor
- `报名避暑季活动` → 触发 campaign-advisor

### 查看 RL 轨迹

每次对话结束后访问：
```
GET http://localhost:8000/api/trajectories
```

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 19 · Vite · WebSocket |
| 后端 | Python 3.12 · FastAPI · uvicorn |
| Agent 运行时 | OpenClaw（本地 Gateway） |
| 模型 | Qwen3.5-27B · Q4_K_M · llama-server |
| 持久化 | JSON 文件（热状态+事件日志+RL轨迹） |
| 通信协议 | WebSocket（双向实时推送） |
