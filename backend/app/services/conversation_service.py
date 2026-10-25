from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.db.models import Conversation, Message
from app.core.config import settings


def create_conversation(db: Session, title: str = "New chat") -> Conversation:
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
    return db.get(Conversation, conversation_id)


def list_conversations(db: Session) -> list[Conversation]:
    return (
        db.query(Conversation)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def rename_conversation(db: Session, conversation_id: int, title: str) -> Optional[Conversation]:
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        return None
    conv.title = title
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(db: Session, conversation_id: int) -> bool:
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        return False
    db.delete(conv)
    db.commit()
    return True


def add_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(msg)
    conv = db.get(Conversation, conversation_id)
    if conv is not None:
        conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


def build_context(db: Session, conversation_id: int) -> List[dict]:
    limit = settings.llm_context_message_limit
    if limit and limit > 0:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        msgs.reverse()
    else:
        msgs = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )
    return [{"role": m.role, "content": m.content} for m in msgs if m.role in ("user", "assistant")]


def auto_title(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= 60:
        return text or "New chat"
    return text[:57] + "..."
