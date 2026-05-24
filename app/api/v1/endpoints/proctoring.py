import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.websocket_manager import ws_manager
from app.models.interview import ProctoringLog, ProctoringEventType

logger = logging.getLogger(__name__)
router = APIRouter()


VALID_EVENT_TYPES = {e.value for e in ProctoringEventType}


class ProctoringEventRequest(BaseModel):
    session_id: int
    event_type: str
    severity: str = "medium"  # low, medium, high — sent by frontend


@router.post("/event")
async def log_proctoring_event(
    request: ProctoringEventRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives proctoring violation events detected by face-api.js in the browser.
    Logs them to PostgreSQL and sends a real-time warning to the candidate via WebSocket.

    Event types sent by frontend:
    - NO_FACE         → face-api.js detected no face in frame
    - MULTI_FACE      → face-api.js detected more than one face
    - LOOKING_AWAY    → head pose estimation shows candidate not facing screen
    - TAB_SWITCH      → document.visibilityState changed
    - FULLSCREEN_EXIT → fullscreenchange event fired
    """
    if request.event_type not in VALID_EVENT_TYPES:
        logger.warning(f"Unknown proctoring event type received: {request.event_type}")
        return {"status": "ignored", "reason": "unknown event type"}

    # Save event to PostgreSQL
    log = ProctoringLog(
        session_id=request.session_id,
        event_type=ProctoringEventType(request.event_type),
        severity=request.severity,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()

    # Send real-time warning to candidate through their active WebSocket
    await ws_manager.send_json(
        str(request.session_id),
        {
            "type": "proctoring_warning",
            "event": request.event_type,
            "severity": request.severity,
            "message": _get_warning_message(request.event_type),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    logger.warning(
        f"Proctoring event: session={request.session_id} "
        f"type={request.event_type} severity={request.severity}"
    )

    return {"status": "logged"}


def _get_warning_message(event_type: str) -> str:
    messages = {
        "NO_FACE": "Warning: Your face is not visible. Please face the camera.",
        "MULTI_FACE": "Warning: Multiple faces detected. Only the candidate should be visible.",
        "LOOKING_AWAY": "Warning: Please keep your eyes on the screen.",
        "TAB_SWITCH": "Warning: Tab switching is not allowed during the interview.",
        "FULLSCREEN_EXIT": "Warning: Please remain in fullscreen mode during the interview.",
    }
    return messages.get(event_type, "Warning: Proctoring violation detected.")