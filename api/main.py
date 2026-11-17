import os
import time
from contextlib import asynccontextmanager

import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "notes"),
        user=os.getenv("DB_USER", "app"),
        password=os.getenv("DB_PASSWORD", "app_pw"),
        connect_timeout=3,
    )


def init_db(retries=30, delay=2):
    """Tao bang notes; thu lai vi DB co the chua san sang luc API khoi dong."""
    for i in range(retries):
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS notes ("
                    "id SERIAL PRIMARY KEY, text TEXT NOT NULL)"
                )
            print("DB san sang", flush=True)
            return
        except Exception as e:  # noqa: BLE001
            print(f"Cho DB ({i + 1}/{retries}): {e}", flush=True)
            time.sleep(delay)
    print("Khong ket noi duoc DB, API van chay (se loi o endpoint can DB)", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="microseg-api", lifespan=lifespan)


class NoteIn(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/notes")
def list_notes():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, text FROM notes ORDER BY id")
            return [{"id": r[0], "text": r[1]} for r in cur.fetchall()]
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")


@app.post("/notes")
def create_note(note: NoteIn):
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO notes (text) VALUES (%s) RETURNING id", (note.text,))
            return {"id": cur.fetchone()[0], "text": note.text}
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Not found")
            return {"deleted": note_id}
    except psycopg2.Error as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")
