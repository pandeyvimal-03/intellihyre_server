import json
from typing import List, Optional, Any
from app.core.redis import get_redis

class InterviewStateManager:
    @property
    def redis(self):
        client = get_redis()
        if client is None:
            raise RuntimeError("Redis client is not initialized. Ensure connect_to_redis() was called.")
        return client

    async def initialize_session(self, session_id: int, questions: List[str]):
        state = {
            "session_id": session_id,
            "current_question_index": 0,
            "questions": questions,
            "answers": [],
            "scores": [],
            "status": "ongoing"
        }
        # Set with 24h expiration to avoid leaks
        await self.redis.set(f"interview_state:{session_id}", json.dumps(state), ex=86400)

    async def get_state(self, session_id: int) -> Optional[dict[str, Any]]:
        data = await self.redis.get(f"interview_state:{session_id}")
        return json.loads(data) if data else None

    async def update_state(self, session_id: int, state: dict[str, Any]):
        # Keep the 24h expiration on updates as well
        await self.redis.set(f"interview_state:{session_id}", json.dumps(state), ex=86400)

    async def clear_state(self, session_id: int):
        await self.redis.delete(f"interview_state:{session_id}")

interview_state_manager = InterviewStateManager()
