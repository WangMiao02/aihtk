"""
C 端 Skill Mock 实现
每个 handler 模拟真实执行：有合理延迟、结构化输出、声明下游
"""

import asyncio
from harness.skill_executor import SkillResult, SideEffect

# ── 复用数据常量（和前端 cDemoData.js 保持一致）────────────────────────
C_TRIP_DATA = {
    "trainNo":   "G1",
    "departure": "07:00",
    "arrival":   "11:30",
    "from":      "北京南",
    "to":        "上海虹桥",
    "seatType":  "二等座靠窗",
    "price":     "¥553",
    "date":      "周三 6月4日",
}

C_PET_BOARDING_DATA = {
    "petName":   "豆豆",
    "storeName": "喵星人之家",
    "boardType": "散养位",
    "days":      3,
    "price":     "¥450",
}

C_HOTEL_DATA = {
    "hotelName":     "全季虹桥店",
    "pricePerNight": "¥389",
    "roomType":      "标准大床房",
    "checkIn":       "6月4日",
    "checkOut":      "6月6日",
    "nights":        2,
    "total":         "¥778",
}

C_RIDE_DATA = {
    "from":     "北京南站",
    "to":       "出发楼下",
    "time":     "06:10",
    "price":    "约¥45",
    "note":     "周三早高峰建议提前10分钟",
}

C_ARRIVAL_RIDE_DATA = {
    "from":     "上海虹桥站",
    "to":       "全季虹桥店",
    "distance": "3.2km",
    "time":     "约12分钟",
    "price":    "约¥18",
}

C_LUNCH_DATA = {
    "restaurants": [
        {"name": "渝是乎", "rating": "4.8", "price": "¥38/人", "distance": "280米", "recommended": True},
        {"name": "老盛昌", "rating": "4.7", "price": "¥22/人", "distance": "450米", "recommended": False},
    ],
    "coupon": "满25减5（已自动匹配）",
}

C_BUDGET_DAY1 = {
    "total": "¥1,846",
    "items": [
        {"label": "高铁·G1",        "amount": "¥553",  "type": "差旅"},
        {"label": "宠物寄养·3天",    "amount": "¥450",  "type": "个人"},
        {"label": "全季·2晚",        "amount": "¥778",  "type": "差旅"},
        {"label": "打车·南站",        "amount": "¥45",   "type": "差旅"},
        {"label": "午餐",            "amount": "¥20",   "type": "个人"},
    ],
    "reimbursable": "¥1,376",
}

C_EXPENSE_DATA = {
    "bizTotal":  "¥1,376",
    "items": [
        {"label": "高铁·G1",  "amount": "¥553"},
        {"label": "全季酒店", "amount": "¥778"},
        {"label": "打车",     "amount": "¥45"},
    ],
}


# ── Skill Handlers ────────────────────────────────────────────────────

async def trip_reserver(params: dict) -> SkillResult:
    await asyncio.sleep(0.8)
    return SkillResult(
        status="success",
        summary="G1次 周三 07:00 北京南→上海虹桥 ¥553",
        data=C_TRIP_DATA,
        confidence=0.96,
        recommended_next=["pet-boarding", "hotel-reserver", "ride-hailing"],
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=120,
    )

async def hotel_reserver(params: dict) -> SkillResult:
    await asyncio.sleep(0.6)
    return SkillResult(
        status="success",
        summary="全季虹桥店 ¥389/晚 × 2 = ¥778",
        data=C_HOTEL_DATA,
        confidence=0.94,
        recommended_next=["budget-manager"],
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=100,
    )

async def ride_hailing(params: dict) -> SkillResult:
    await asyncio.sleep(0.4)
    data = C_ARRIVAL_RIDE_DATA if params.get("context") == "arrival" else C_RIDE_DATA
    return SkillResult(
        status="success",
        summary="叫车预约成功",
        data=data,
        confidence=0.98,
        recommended_next=["budget-manager"],
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=60,
    )

async def pet_boarding(params: dict) -> SkillResult:
    await asyncio.sleep(0.7)
    return SkillResult(
        status="success",
        summary="喵星人之家 散养位 3天 ¥450",
        data=C_PET_BOARDING_DATA,
        confidence=0.92,
        recommended_next=["pet-shop"],
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=80,
    )

async def pet_shop(params: dict) -> SkillResult:
    await asyncio.sleep(0.4)
    return SkillResult(
        status="success",
        summary="太空箱 ¥89 闪购30分钟送到",
        data={"item": "太空猫包", "price": "¥89", "eta": "30分钟"},
        confidence=0.88,
        recommended_next=["budget-manager"],
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=40,
    )

async def budget_manager(params: dict) -> SkillResult:
    await asyncio.sleep(0.3)
    return SkillResult(
        status="success",
        summary=f"已入账，差旅可报销 {C_BUDGET_DAY1['reimbursable']}",
        data=C_BUDGET_DAY1,
        side_effect_level=SideEffect.WRITE_STATE,
        payload_size_tokens=80,
    )

async def expense_reimbursement(params: dict) -> SkillResult:
    await asyncio.sleep(0.5)
    return SkillResult(
        status="success",
        summary=f"报销单生成：差旅 {C_EXPENSE_DATA['bizTotal']}",
        data=C_EXPENSE_DATA,
        side_effect_level=SideEffect.WRITE_STATE,
        payload_size_tokens=80,
    )

async def food_recommend(params: dict) -> SkillResult:
    await asyncio.sleep(0.5)
    return SkillResult(
        status="success",
        summary="推荐渝是乎酸菜鱼 ¥38（已匹配满减券）",
        data=C_LUNCH_DATA,
        confidence=0.89,
        recommended_next=["budget-manager"],
        side_effect_level=SideEffect.READ_ONLY,
        payload_size_tokens=100,
    )

async def hair_salon(params: dict) -> SkillResult:
    await asyncio.sleep(0.5)
    return SkillResult(
        status="success",
        summary="MOMENT SALON · Tony老师 · 周三15:00 ¥128",
        data={"storeName": "MOMENT SALON", "stylist": "Tony 老师",
              "time": "周三 15:00", "service": "剪+洗", "price": "¥128"},
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=60,
    )

async def massage_booking(params: dict) -> SkillResult:
    await asyncio.sleep(0.5)
    return SkillResult(
        status="success",
        summary="清和堂 60分钟肩颈套餐 ¥198 · 18:30",
        data={"storeName": "清和堂", "service": "中式推拿60分钟",
              "time": "18:30", "price": "¥198", "distance": "步行5分钟"},
        side_effect_level=SideEffect.EXTERNAL_ACTION,
        payload_size_tokens=60,
    )


# handler 注册表（handler_key → callable）
C_HANDLERS: dict = {
    "trip_reserver":       trip_reserver,
    "hotel_reserver":      hotel_reserver,
    "ride_hailing":        ride_hailing,
    "pet_boarding":        pet_boarding,
    "pet_shop":            pet_shop,
    "budget_manager":      budget_manager,
    "expense_reimbursement": expense_reimbursement,
    "food_recommend":      food_recommend,
    "hair_salon":          hair_salon,
    "massage_booking":     massage_booking,
}
