"""
Skill 索引注册表 — 渐进式加载 Layer 0
每条 ~200 token，用于意图路由，不载入完整执行逻辑

格式：
  name         Skill 唯一标识
  description  触发词 + 能力边界（意图路由唯一依据）
  scope        "C" | "B" | "both"
  downstream   声明式下游（框架自动编排，无 if-else）
  handler_key  运行时映射到 handler 函数
"""

SKILL_INDEX: list[dict] = [
    # ── C 端·出行 ────────────────────────────────────────────────────
    {
        "name": "trip-reserver",
        "description": "查询并预订火车票/高铁票/机票。触发词：订票/查票/去XX/出差/回家/行程",
        "scope": "C",
        "downstream": ["hotel-reserver", "pet-boarding", "ride-hailing", "budget-manager"],
        "handler_key": "trip_reserver",
    },
    {
        "name": "hotel-reserver",
        "description": "出差/旅行酒店推荐与预订。通常由 trip-reserver 联动触发，也可独立使用",
        "scope": "C",
        "downstream": ["budget-manager"],
        "handler_key": "hotel_reserver",
    },
    {
        "name": "ride-hailing",
        "description": "叫车/打车/出行。触发词：叫车/打车/滴滴/快车/去机场/去车站",
        "scope": "C",
        "downstream": ["budget-manager"],
        "handler_key": "ride_hailing",
    },
    # ── C 端·宠物 ────────────────────────────────────────────────────
    {
        "name": "pet-boarding",
        "description": "宠物寄养预约。触发词：寄养/猫/狗/宠物/出差宠物安置。行程≥2天自动触发",
        "scope": "C",
        "downstream": ["pet-shop", "budget-manager"],
        "handler_key": "pet_boarding",
    },
    {
        "name": "pet-shop",
        "description": "宠物用品购买。寄养前自动检测是否需要太空箱/猫包等随行物品",
        "scope": "C",
        "downstream": ["budget-manager"],
        "handler_key": "pet_shop",
    },
    # ── C 端·财务 ────────────────────────────────────────────────────
    {
        "name": "budget-manager",
        "description": "无感记账/预算管理/超支预警。所有消费类 Skill 完成后静默触发，用户无感知",
        "scope": "C",
        "downstream": [],
        "handler_key": "budget_manager",
    },
    {
        "name": "expense-reimbursement",
        "description": "差旅报销：识别可报销消费、生成报销单。触发词：报销/出差费用/整理票据",
        "scope": "C",
        "downstream": [],
        "handler_key": "expense_reimbursement",
    },
    # ── C 端·餐饮 ────────────────────────────────────────────────────
    {
        "name": "food-recommend",
        "description": "外卖/堂食推荐。触发词：吃什么/午餐/晚餐/点外卖/附近餐厅",
        "scope": "C",
        "downstream": ["budget-manager"],
        "handler_key": "food_recommend",
    },
    # ── C 端·丽人 ────────────────────────────────────────────────────
    {
        "name": "hair-salon",
        "description": "美发预约。触发词：理发/剪头/染发/发型师/SALON",
        "scope": "C",
        "downstream": [],
        "handler_key": "hair_salon",
    },
    {
        "name": "massage-booking",
        "description": "按摩/推拿预约。触发词：按摩/推拿/足疗/放松/肩颈。也可由疲劳感知触发",
        "scope": "C",
        "downstream": ["budget-manager"],
        "handler_key": "massage_booking",
    },
    # ── B 端·民宿核心链路 ─────────────────────────────────────────────
    {
        "name": "morning-report",
        "description": "B端晨间日报：昨日入住率/营收/RevPAR/评分/竞品动态。每日 08:00 heartbeat 触发",
        "scope": "B",
        "downstream": ["promotion-advisor"],
        "handler_key": "morning_report",
    },
    {
        "name": "promotion-advisor",
        "description": "B端调价建议：基于竞品监控给出折扣率调整建议和收益预测",
        "scope": "B",
        "downstream": ["morning-report"],
        "handler_key": "promotion_advisor",
    },
    {
        "name": "review-manager",
        "description": "B端差评处理：差评检测/回复草稿生成/归因分析。事件触发",
        "scope": "B",
        "downstream": ["maintenance-reminder", "room-switch"],
        "handler_key": "review_manager",
    },
    {
        "name": "maintenance-reminder",
        "description": "B端维修工单：硬件/设施故障维修单创建、师傅通知、进度跟踪",
        "scope": "B",
        "downstream": ["room-switch"],
        "handler_key": "maintenance_reminder",
    },
    {
        "name": "room-switch",
        "description": "B端房态管理：房间上下架/锁房/防超卖/换房协调。由差评/满房/维修联动触发",
        "scope": "B",
        "downstream": ["morning-report"],
        "handler_key": "room_switch",
    },
    {
        "name": "campaign-advisor",
        "description": "B端活动顾问：平台活动报名建议/效果追踪/ROI 归因复盘",
        "scope": "B",
        "downstream": ["morning-report"],
        "handler_key": "campaign_advisor",
    },
]

# 快速查询表
_INDEX_BY_NAME: dict[str, dict] = {s["name"]: s for s in SKILL_INDEX}
_INDEX_BY_KEY:  dict[str, dict] = {s["handler_key"]: s for s in SKILL_INDEX}


class SkillRegistry:
    def get_index(self, scope: str = "C") -> list[dict]:
        """Layer 0：返回能力索引（仅 name + description，约 200tok/skill）"""
        return [
            {"name": s["name"], "description": s["description"]}
            for s in SKILL_INDEX
            if s["scope"] in (scope, "both")
        ]

    def get_skill(self, name: str) -> dict | None:
        return _INDEX_BY_NAME.get(name)

    def get_downstream(self, name: str) -> list[str]:
        s = _INDEX_BY_NAME.get(name, {})
        return s.get("downstream", [])

    def get_skill_by_handler(self, handler_key: str) -> dict | None:
        return _INDEX_BY_KEY.get(handler_key)

    def resolve_intent(self, text: str, scope: str = "C") -> str | None:
        """
        简单关键词路由（实际项目由 LLM 做，这里用规则作为 fallback）
        返回命中的 handler_key
        """
        t = text.lower()
        rules = [
            (["订票", "查票", "去上海", "出差", "高铁", "火车", "机票", "回家"], "trip_reserver"),
            (["酒店", "住哪", "订房"],                                          "hotel_reserver"),
            (["叫车", "打车", "滴滴", "快车"],                                  "ride_hailing"),
            (["寄养", "猫", "豆豆", "宠物"],                                    "pet_boarding"),
            (["吃什么", "午餐", "外卖", "点餐", "附近餐厅"],                    "food_recommend"),
            (["理发", "剪头", "发型"],                                          "hair_salon"),
            (["按摩", "推拿", "足疗", "放松"],                                  "massage_booking"),
            (["报销", "出差费用"],                                              "expense_reimbursement"),
            (["调价", "折扣", "竞品"],                                          "promotion_advisor"),
            (["差评", "回复", "维修"],                                          "review_manager"),
        ]
        for keywords, key in rules:
            if any(k in t for k in keywords):
                return key
        return None
