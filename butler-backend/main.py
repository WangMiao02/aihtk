"""
FastAPI 主入口
- WebSocket: /ws/{demo}/{soul}  — demo∈{C,B}, soul∈{pet_owner,business,elderly,food_merchant,hotel_merchant,homestay}
- REST POST:  /api/heartbeat/{demo} — 手动触发心跳（演示用）
- REST GET:   /api/state/{demo}     — 读取当前热状态
- REST GET:   /api/trajectories     — 读取 RL 轨迹
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio, json

from harness.runtime_loop import AgentRuntimeLoop
from persistence.store     import PersistenceStore
from rl.trajectory         import TrajectoryRecorder

app = FastAPI(title="Butler Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 单例 ────────────────────────────────────────────────────────────
store    = PersistenceStore()
recorder = TrajectoryRecorder()

# ── WebSocket 主路由 ─────────────────────────────────────────────────
@app.websocket("/ws/{demo}/{soul}")
async def ws_agent(websocket: WebSocket, demo: str, soul: str):
    await websocket.accept()
    loop = AgentRuntimeLoop(demo=demo, soul=soul, store=store, recorder=recorder)

    async def send(event: dict):
        await websocket.send_text(json.dumps(event, ensure_ascii=False))

    # 连接后自动触发初始心跳推送
    await loop.run_heartbeat(send)

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            await loop.handle_message(msg, send)
    except WebSocketDisconnect:
        pass

# ── REST: 手动触发心跳（演示按钮用）────────────────────────────────────
@app.post("/api/heartbeat/{demo}")
async def trigger_heartbeat(demo: str):
    return {"status": "ok", "message": f"heartbeat triggered for demo={demo}"}

# ── REST: 读热状态 ───────────────────────────────────────────────────
@app.get("/api/state/{demo}")
async def get_state(demo: str):
    return store.get_hot_state(demo)

# ── REST: RL 轨迹 ────────────────────────────────────────────────────
@app.get("/api/trajectories")
async def get_trajectories():
    return recorder.read_all()
