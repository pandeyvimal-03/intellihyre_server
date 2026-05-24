import json
import logging
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import async_session
from app.core.websocket_manager import ws_manager
from app.models.interview import (
    Interview,
    InterviewStatus,
    InterviewSession as DBInterviewSession,
    ProctoringLog,
    ProctoringEventType,
    EvaluationReport, 
    RecommendationType, 
    QALog 
)
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.modules.interview_state import interview_state_manager
from app.modules import ai_engine

logger = logging.getLogger(__name__)
router = APIRouter()


import asyncio

@router.websocket("/ws/interview/{token}")
async def interview_websocket(websocket: WebSocket, token: str):
    logger.info(f"Incoming WebSocket connection attempt for token: {token}")
    try:
        # ── 1. Validate token ──────────────────────────────────────────────
        async with async_session() as db:
            logger.info("Database session opened successfully.")
            result = await db.execute(
                select(Interview).where(Interview.token == token)
            )
            interview = result.scalar_one_or_none()
            logger.info(f"Interview found: {interview is not None}")

            if not interview or interview.status not in [InterviewStatus.PENDING, InterviewStatus.ONGOING]:
                logger.warning(f"Invalid interview or status: {interview.status if interview else 'None'}")
                await websocket.close(code=4001)
                return

            # Get Job and Application details for AI context
            res_app = await db.execute(
                select(Application).where(Application.id == interview.application_id)
            )
            application = res_app.scalar_one_or_none()
            if not application:
                 logger.error(f"Application not found for interview: {interview.id}")
                 await websocket.close(code=4004)
                 return
            
            res_job = await db.execute(select(Job).where(Job.id == application.job_id))
            job = res_job.scalar_one_or_none()
            if not job:
                 logger.error(f"Job not found for application: {application.id}")
                 await websocket.close(code=4004)
                 return

            # ── 2. Create interview session row in PostgreSQL ──────────────
            # Check if an active session already exists (for ONGOING status)
            res_sess = await db.execute(
                select(DBInterviewSession)
                .where(DBInterviewSession.interview_id == interview.id)
                .order_by(DBInterviewSession.started_at.desc())
            )
            db_session = res_sess.scalar_one_or_none()
            
            if not db_session:
                db_session = DBInterviewSession(interview_id=interview.id)
                db.add(db_session)
                interview.status = InterviewStatus.ONGOING
                await db.commit()
                await db.refresh(db_session)
                
            session_id = db_session.id
            interview_id = interview.id

        # ── 3. Accept WebSocket connection ────────────────────────────────
        logger.info("Before ws_manager.connect")
        await ws_manager.connect(str(session_id), websocket)
        logger.info("After ws_manager.connect")
        logger.info(f"Interview WebSocket connected: session={session_id}")

        await ws_manager.send_json(str(session_id), {
            "type": "session_started",
            "session_id": session_id
        })

        resume_text = ""
        if application.resume_url and os.path.exists(application.resume_url):
            with open(application.resume_url, "rb") as f:
                file_content = f.read()
                resume_text = await ai_engine.extract_text_from_pdf(file_content)

        initial_questions = await ai_engine.generate_interview_questions(
            job_description=job.description,
            resume_text=resume_text
        )

        await interview_state_manager.initialize_session(
            session_id, initial_questions
        )

        await ws_manager.send_json(str(session_id), {
            "type": "question",
            "data": initial_questions[0],
            "index": 0,
            "total": len(initial_questions),
        })

        silence_timeout = 45.0 # 45 seconds to answer
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=silence_timeout)
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "answer_audio":
                    logger.info(f"Received audio answer for session {session_id}")
                    state = await interview_state_manager.get_state(session_id)
                    if not state:
                        logger.error(f"State not found for session {session_id}")
                        break
                        
                    current_idx = state["current_question_index"]
                    current_question = state["questions"][current_idx]

                    logger.info(f"Transcribing audio...")
                    transcript = await ai_engine.transcribe_audio(message.get("data", ""))
                    logger.info(f"Transcript: {transcript}")
                    
                    evaluation = await ai_engine.evaluate_answer(current_question, transcript)
                    score = evaluation.get("score", 0.0)
                    logger.info(f"Score: {score}")

                    state["answers"].append(transcript)
                    state["scores"].append(score)
                    
                    # Log to DB
                    async with async_session() as db:
                        qa_log = QALog(
                            session_id=session_id,
                            question=current_question,
                            answer_transcript=transcript,
                            score=score,
                            timestamp=datetime.now(timezone.utc),
                        )
                        db.add(qa_log)
                        await db.commit()

                    await ws_manager.send_json(str(session_id), {
                        "type": "transcript",
                        "data": transcript,
                    })

                    # Generate Follow-up Question
                    logger.info(f"Generating follow-up question...")
                    followup = await ai_engine.generate_followup_question(current_question, transcript)
                    
                    if followup:
                        logger.info(f"Follow-up: {followup}")
                        # Insert follow-up into questions list
                        state["questions"].insert(current_idx + 1, followup)
                        state["current_question_index"] += 1
                        await interview_state_manager.update_state(session_id, state)
                        
                        await ws_manager.send_json(str(session_id), {
                            "type": "question",
                            "data": followup,
                            "index": state["current_question_index"],
                            "total": len(state["questions"]),
                            "is_followup": True
                        })
                    else:
                        logger.info("No follow-up generated. Moving to next question.")
                        state["current_question_index"] += 1
                        if state["current_question_index"] < len(state["questions"]):
                            await interview_state_manager.update_state(session_id, state)
                            next_q = state["questions"][state["current_question_index"]]
                            await ws_manager.send_json(str(session_id), {
                                "type": "question",
                                "data": next_q,
                                "index": state["current_question_index"],
                                "total": len(state["questions"]),
                            })
                        else:
                            logger.info("Interview complete.")
                            await ws_manager.send_json(str(session_id), {
                                "type": "interview_complete",
                                "data": "Interview completed successfully.",
                            })
                            break

                elif msg_type == "ping":
                    await ws_manager.send_json(str(session_id), {"type": "pong"})

                elif msg_type == "proctoring_event":
                    # ... (proctoring event logic remains same)
                    event = message.get("event")
                    async with async_session() as db:
                        log = ProctoringLog(
                            session_id=session_id,
                            event_type=ProctoringEventType(event),
                            timestamp=datetime.now(timezone.utc),
                        )
                        db.add(log)
                        await db.commit()

                    await ws_manager.send_json(str(session_id), {
                        "type": "warning",
                        "data": f"Proctoring violation detected: {event}",
                    })

            except asyncio.TimeoutError:
                # Handle Silence
                state = await interview_state_manager.get_state(session_id)
                if state:
                    current_idx = state["current_question_index"]
                    current_question = state["questions"][current_idx]
                    
                    await ws_manager.send_json(str(session_id), {
                        "type": "nudge",
                        "message": "I haven't heard from you in a while. Would you like me to repeat the question or move to the next one?",
                        "question": current_question
                    })
                continue

    except WebSocketDisconnect:
        logger.info(f"Interview WebSocket disconnected: session={session_id}")

    except Exception as e:
        logger.error(f"FATAL ERROR in interview_websocket: {e}", exc_info=True)
        # Attempt to inform the client of the error before closing
        try:
            await ws_manager.send_json(str(session_id), {
                "type": "error",
                "message": "An unexpected error occurred.",
            })
            await websocket.close(code=4000)
        except:
            pass

    finally:
        # ── 6. Finalize session in PostgreSQL ─────────────────────────
        async with async_session() as db:
            result = await db.execute(
                select(DBInterviewSession).where(DBInterviewSession.id == session_id)
            )
            db_sess = result.scalar_one_or_none()
            if db_sess:
                db_sess.ended_at = datetime.now(timezone.utc)

            result = await db.execute(
                select(Interview).where(Interview.id == interview_id)
            )
            interv = result.scalar_one_or_none()
            if interv and interv.status == InterviewStatus.ONGOING:
                interv.status = InterviewStatus.COMPLETED

            await db.commit()

        await interview_state_manager.clear_state(session_id)
        ws_manager.disconnect(str(session_id))
        logger.info(f"Interview session finalized: session={session_id}")

        # --- Generate Evaluation Report and Update Application Status ---
        if db_sess:
            # 1. Aggregate scores from QALog
            qa_logs_result = await db.execute(
                select(QALog).where(QALog.session_id == db_sess.id)
            )
            qa_logs = qa_logs_result.scalars().all()
            
            total_qa_score = 0.0
            if qa_logs:
                total_qa_score = sum(log.score for log in qa_logs) / len(qa_logs)
            
            # 2. Determine recommendation based on score
            recommendation = RecommendationType.REJECTED
            if total_qa_score > 6.0: # Score is out of 10, so 6.0 is 60%
                recommendation = RecommendationType.SELECTED
            else:
                recommendation = RecommendationType.REJECTED

            # 3. Generate summary (can be a simple concatenation or AI generated)
            summary_text = "No questions answered during the interview."
            if qa_logs:
                summary_text = f"""Interview Questions and Answers:
"""
                for i, log in enumerate(qa_logs):
                    summary_text += f"{i+1}. Q: {log.question}\n   A: {log.answer_transcript}\n   Score: {log.score}/10\n"
            
            evaluation_report = EvaluationReport(
                session_id=db_sess.id,
                total_score=round(total_qa_score, 2),
                recommendation=recommendation,
                summary=summary_text,
            )
            db.add(evaluation_report)

            # 4. Update Application status
            if interv:
                result_app = await db.execute(select(Application).where(Application.id == interv.application_id))
                application_to_update = result_app.scalar_one_or_none()
                if application_to_update:
                    if recommendation == RecommendationType.SELECTED:
                        application_to_update.status = ApplicationStatus.SHORTLISTED
                    else:
                        application_to_update.status = ApplicationStatus.REJECTED
        
        await db.commit() 
        if db_sess:
            await db.refresh(db_sess) 
        if interv:
            await db.refresh(interv)
        if 'application_to_update' in locals() and application_to_update:
            await db.refresh(application_to_update)
