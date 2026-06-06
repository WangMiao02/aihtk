"""
Soul Adapter — 输出层
文档映射：实现细节架构图.md LAYER 3 Soul Adapter

职责：
- 不含业务逻辑，只改表达方式
- 同一业务结果 → 根据 soul 输出完全不同语气
- Soul 与 Skill 彻底解耦：换 Soul 不改任何 Skill 代码
"""

from soul.configs import SOUL_TEMPLATES


class SoulAdapter:

    def format(self, soul: str, template: str, data: dict) -> str:
        """
        按 soul + template 格式化输出文本
        data 可用于填充模板变量（如 {occupancy}）
        """
        soul_cfg = SOUL_TEMPLATES.get(soul, SOUL_TEMPLATES["pet_owner"])
        text = soul_cfg.get(template, "好的，已处理。")

        # 简单变量替换
        try:
            text = text.format(**data)
        except (KeyError, ValueError):
            pass  # 模板变量不完整时保留原文

        return text
