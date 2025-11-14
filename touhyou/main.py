from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import sqlite3
import json

app = FastAPI()
clients = []

# --- DB 初期化 ---
def init_db():
    conn = sqlite3.connect("vote.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            votes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 全クライアントへ配信
async def broadcast(data):
    for ws in clients:
        await ws.send_text(json.dumps(data))

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.append(ws)

    try:
        while True:
            await ws.receive_text()  # クライアントの入力を待つ（使わなくてもOK）
    except:
        clients.remove(ws)

# 議題一覧
@app.get("/topics")
def get_topics():
    conn = sqlite3.connect("vote.db")
    c = conn.cursor()
    c.execute("SELECT id, title, votes FROM topics")
    topics = c.fetchall()
    conn.close()
    return topics

# 投票
@app.post("/vote/{topic_id}")
async def vote(topic_id: int):
    conn = sqlite3.connect("vote.db")
    c = conn.cursor()
    c.execute("UPDATE topics SET votes = votes + 1 WHERE id=?", (topic_id,))
    conn.commit()
    c.execute("SELECT id, title, votes FROM topics WHERE id=?", (topic_id,))
    topic = c.fetchone()
    conn.close()

    # 全クライアントへ配信
    await broadcast({
        "type": "update",
        "topic": topic
    })

    return {"status": "ok"}
