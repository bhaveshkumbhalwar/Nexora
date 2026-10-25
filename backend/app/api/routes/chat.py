import asyncio
import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import conversation_service as cs
from app.services.llm_service import (
    LLMConfigurationError,
    LLMServiceError,
    chat_completion,
    stream_chat_completion,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    started = time.perf_counter()
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    t0 = time.perf_counter()
    if req.conversation_id is None:
        conv = cs.create_conversation(db, title=cs.auto_title(message))
    else:
        conv = cs.get_conversation(db, req.conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    logger.info("chat db load/create %.1f ms", (time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    user_msg = cs.add_message(db, conv.id, "user", message)
    context = cs.build_context(db, conv.id)
    logger.info("chat db persist/context %.1f ms", (time.perf_counter() - t0) * 1000)

    try:
        answer = chat_completion(context)
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    t0 = time.perf_counter()
    assistant_msg = cs.add_message(db, conv.id, "assistant", answer)
    if conv.title == "New chat":
        conv.title = cs.auto_title(message)
        db.commit()
    logger.info("chat db save assistant %.1f ms", (time.perf_counter() - t0) * 1000)

    logger.info(
        "chat total %.1f ms conversation_id=%s",
        (time.perf_counter() - started) * 1000,
        conv.id,
    )
    return ChatResponse(
        conversation_id=conv.id,
        user_message_id=user_msg.id,
        assistant_message_id=assistant_msg.id,
        content=answer,
        title=conv.title,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, request: Request, db: Session = Depends(get_db)):
    started = time.perf_counter()
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    t0 = time.perf_counter()
    if req.conversation_id is None:
        conv = await run_in_threadpool(cs.create_conversation, db, cs.auto_title(message))
    else:
        conv = await run_in_threadpool(cs.get_conversation, db, req.conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    logger.info("stream db load/create %.1f ms", (time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    user_msg = await run_in_threadpool(cs.add_message, db, conv.id, "user", message)
    context = await run_in_threadpool(cs.build_context, db, conv.id)
    logger.info("stream db persist/context %.1f ms", (time.perf_counter() - t0) * 1000)

    async def event_generator():
        nonlocal started
        accumulated = ""
        assistant_msg_id = None
        gemini_started = time.perf_counter()
        first_chunk = True
        cancelled = False
        try:
            yield _sse(
                {
                    "type": "meta",
                    "conversation_id": conv.id,
                    "user_message_id": user_msg.id,
                    "title": conv.title,
                }
            )

            async for chunk in stream_chat_completion(context):
                if await request.is_disconnected():
                    cancelled = True
                    break
                if first_chunk:
                    logger.info(
                        "stream gemini first chunk %.1f ms", (time.perf_counter() - gemini_started) * 1000
                    )
                    first_chunk = False
                accumulated += chunk
                yield _sse({"type": "chunk", "content": chunk})

            if cancelled:
                logger.info("stream cancelled conversation_id=%s", conv.id)
                return

            t0 = time.perf_counter()
            assistant_msg = await run_in_threadpool(
                cs.add_message, db, conv.id, "assistant", accumulated.strip() or "(no response)"
            )
            assistant_msg_id = assistant_msg.id
            if conv.title == "New chat":
                conv.title = cs.auto_title(message)
                await run_in_threadpool(db.commit)
            logger.info("stream db save assistant %.1f ms", (time.perf_counter() - t0) * 1000)

            yield _sse(
                {
                    "type": "done",
                    "assistant_message_id": assistant_msg_id,
                    "title": conv.title,
                }
            )
        except asyncio.CancelledError:
            logger.info("stream cancelled conversation_id=%s", conv.id)
            raise
        except (LLMConfigurationError, LLMServiceError) as exc:
            logger.warning("stream llm error: %s", exc)
            yield _sse({"type": "error", "detail": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logger.exception("stream unexpected error")
            yield _sse({"type": "error", "detail": "Unexpected error while generating response."})
        finally:
            # Persist partial output if the client disconnected mid-stream.
            if cancelled and accumulated.strip():
                try:
                    await run_in_threadpool(cs.add_message, db, conv.id, "assistant", accumulated.strip())
                except Exception:  # noqa: BLE001
                    logger.exception("failed to persist partial stream output")
            logger.info(
                "stream total %.1f ms conversation_id=%s",
                (time.perf_counter() - started) * 1000,
                conv.id,
            )

    return StreamingResponse(event_generator(), media_type="text/event-stream")
