"""
五层持久化 — JSON 文件实现
文档映射：实现细节架构图.md LAYER 5 / single-agent-harness §4

五层：
  Layer 1 热状态层     hot_state_{demo}.json     高频读写·当前 phase
  Layer 2 长期稳定层   stable_config.json         Soul配置+用户偏好+策略规则
  Layer 3 历史事件层   event_log.jsonl            append-only，时序可溯
  Layer 4 语义召回层   (向量库·演示阶段跳过)
  Layer 5 产物层       artifacts/                报销单/日报
"""

import json, os
from datetime import datetime, timezone
from config import DATA_DIR


def _path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)

def _read_json(path: str, default) -> dict | list:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def _write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class PersistenceStore:

    # ── Layer 1：热状态层 ────────────────────────────────────────────
    def get_hot_state(self, demo: str) -> dict:
        return _read_json(_path(f"hot_state_{demo}.json"), {
            "phase": "idle", "active_skill": None,
            "pending_approval": False, "retry_count": 0
        })

    def update_hot_state(self, demo: str, state: dict) -> None:
        existing = self.get_hot_state(demo)
        existing.update(state)
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_json(_path(f"hot_state_{demo}.json"), existing)

    # ── Layer 2：长期稳定层 ──────────────────────────────────────────
    def get_stable_config(self) -> dict:
        return _read_json(_path("stable_config.json"), {
            "users": {
                "kevin": {
                    "soul":    "pet_owner",
                    "pet":     "豆豆",
                    "favs":    ["全季虹桥", "MOMENT SALON", "喵星人之家"],
                }
            },
            "policies": {
                "booking_auto_confirm": False,
                "max_chain_depth": 7,
            }
        })

    def set_user_pref(self, user_id: str, key: str, value) -> None:
        cfg = self.get_stable_config()
        cfg.setdefault("users", {}).setdefault(user_id, {})[key] = value
        _write_json(_path("stable_config.json"), cfg)

    # ── Layer 3：历史事件层（append-only）────────────────────────────
    def append_event(self, demo: str, event_type: str, payload: dict) -> None:
        record = {
            "ts":         datetime.now(timezone.utc).isoformat(),
            "demo":       demo,
            "event_type": event_type,
            "payload":    payload,
        }
        with open(_path("event_log.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_recent_events(self, demo: str, n: int = 20) -> list:
        events = []
        log_path = _path("event_log.jsonl")
        if not os.path.exists(log_path):
            return events
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                    if e.get("demo") == demo:
                        events.append(e)
                except Exception:
                    pass
        return events[-n:]

    # ── Layer 5：产物层 ──────────────────────────────────────────────
    def save_artifact(self, name: str, content: dict) -> str:
        path = os.path.join(DATA_DIR, "artifacts", f"{name}.json")
        _write_json(path, {
            "created_at": datetime.now(timezone.utc).isoformat(),
            **content
        })
        return path

    def get_artifact(self, name: str) -> dict | None:
        path = os.path.join(DATA_DIR, "artifacts", f"{name}.json")
        return _read_json(path, None)
