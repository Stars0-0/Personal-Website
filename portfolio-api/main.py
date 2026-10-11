"""Portfolio API: a private inbox, a moderated guestbook and a visit counter.

Local run:  ALLOWED_ORIGINS=http://localhost:8765 ADMIN_TOKEN=dev uvicorn main:app --reload
"""
import os
import secrets
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field as V, field_validator
from sqlalchemy import func, update
from sqlmodel import Field, Session, SQLModel, create_engine, select

URL = os.getenv("DATABASE_URL", "sqlite:///portfolio.db")
for old in ("postgres://", "postgresql://"):  # some hosts hand out the old scheme; always use the psycopg 3 driver
    if URL.startswith(old):
        URL = "postgresql+psycopg://" + URL[len(old):]
engine = create_engine(
    URL,
    pool_pre_ping=True,  # a scale-to-zero database drops idle connections
    connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {},
)
ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "https://stars0-0.github.io").split(",")]

# ponytail: one global bucket in process memory, no per-IP limit. Behind Render's proxy I could not verify a
# trustworthy client IP, and a spoofable per-IP limit is worse than none. Add per-IP or Redis once the real
# header layout is confirmed on the deployed service. Moderation keeps spam off the public page either way.
LIMIT, WINDOW = 30, 3600  # posts per hour, all visitors combined
POSTS: deque = deque()


def now():
    return datetime.now(timezone.utc)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    body: str
    created: datetime = Field(default_factory=now)


class Entry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    body: str
    approved: bool = False
    created: datetime = Field(default_factory=now)


class Counter(SQLModel, table=True):
    name: str = Field(primary_key=True)
    n: int = 0


class In(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("*")
    @classmethod
    def no_nul(cls, v):
        if "\x00" in v:  # Postgres rejects NUL bytes in text columns, which would be a 500
            raise ValueError("NUL character not allowed")
        return v


class MessageIn(In):
    name: str = V("", max_length=60)
    email: str = V("", max_length=120, pattern=r"^([^@\s]+@[^@\s]+\.[^@\s]+)?$")
    body: str = V(min_length=1, max_length=2000)


class EntryIn(In):
    name: str = V(min_length=1, max_length=40)
    body: str = V(min_length=1, max_length=280)

    @field_validator("name", "body")
    @classmethod
    def one_line(cls, v):  # no newlines: a name can't fake extra lines in the terminal
        return " ".join(v.split())


@asynccontextmanager
async def lifespan(_):
    SQLModel.metadata.create_all(engine)  # ponytail: no migrations; add Alembic when the schema first changes
    with Session(engine) as s:
        if not s.get(Counter, "visits"):
            s.add(Counter(name="visits"))
            s.commit()
    yield


app = FastAPI(title="Portfolio API", description="Backend for Kristan Martinez's portfolio terminal.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


def session():
    with Session(engine) as s:
        yield s


def throttle():
    t = time.monotonic()
    while POSTS and t - POSTS[0] > WINDOW:
        POSTS.popleft()
    if len(POSTS) >= LIMIT:
        raise HTTPException(429, "Too many posts right now. Try again later.")
    POSTS.append(t)


def admin(authorization: str = Header("")):
    token = os.getenv("ADMIN_TOKEN", "")
    if not token:
        raise HTTPException(404)  # admin routes don't exist until a token is configured
    if not secrets.compare_digest(authorization.encode(), f"Bearer {token}".encode()):
        raise HTTPException(401, "Bad token")


def found(s, model, pk):
    row = s.get(model, pk)
    if not row:
        raise HTTPException(404)
    return row


@app.get("/")
def root():
    return {"service": "portfolio-api", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/visit")
def visit(s: Session = Depends(session)):
    # ponytail: counts every call, no de-duplication. It's a vanity number; the page only calls it once per tab.
    s.exec(update(Counter).where(Counter.name == "visits").values(n=Counter.n + 1))
    s.commit()
    return {"visits": s.get(Counter, "visits").n}


@app.get("/api/stats")
def stats(s: Session = Depends(session)):
    guestbook = s.exec(select(func.count()).select_from(Entry).where(Entry.approved)).one()
    return {"visits": s.get(Counter, "visits").n, "guestbook": guestbook}


@app.post("/api/messages", status_code=201, dependencies=[Depends(throttle)])
def send(m: MessageIn, s: Session = Depends(session)):
    s.add(Message(**m.model_dump()))
    s.commit()
    return {"status": "sent"}


@app.get("/api/guestbook")
def guestbook(s: Session = Depends(session)):
    rows = s.exec(select(Entry).where(Entry.approved).order_by(Entry.id.desc()).limit(20)).all()
    return [{"name": r.name, "body": r.body, "date": r.created.date().isoformat()} for r in rows]


@app.post("/api/guestbook", status_code=201, dependencies=[Depends(throttle)])
def sign(e: EntryIn, s: Session = Depends(session)):
    s.add(Entry(**e.model_dump()))  # approved stays False until Kristan approves it
    s.commit()
    return {"status": "pending"}


@app.get("/api/admin/inbox", dependencies=[Depends(admin)])
def inbox(s: Session = Depends(session)):
    return {
        "messages": [m.model_dump(mode="json") for m in s.exec(select(Message).order_by(Message.id.desc()).limit(100))],
        "pending": [e.model_dump(mode="json") for e in s.exec(select(Entry).where(Entry.approved == False).order_by(Entry.id))],  # noqa: E712
    }


@app.post("/api/admin/guestbook/{eid}/approve", dependencies=[Depends(admin)])
def approve(eid: int, s: Session = Depends(session)):
    found(s, Entry, eid).approved = True
    s.commit()
    return {"status": "approved"}


@app.delete("/api/admin/guestbook/{eid}", status_code=204, dependencies=[Depends(admin)])
def remove(eid: int, s: Session = Depends(session)):
    s.delete(found(s, Entry, eid))
    s.commit()
