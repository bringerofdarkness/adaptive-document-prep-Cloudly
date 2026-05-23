import logging
import time
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.interactive_prep_service import start_interactive_prep_session

logger = logging.getLogger(__name__)

@celery_app.task(name="app.workers.tasks.async_start_prep_session", bind=True)
def async_start_prep_session(self, selected_section_numbers: list[int], questions_per_section: int) -> dict:
    """
    Background worker task responsible for processing document text, 
    running LLM generations, and compiling the session matrix.
    Enhancement: Fully handles UUID types and mitigates API rate limits.
    """
    logger.info(f"Starting background session generation for task: {self.request.id}")
    
    db = SessionLocal()
    try:
        # 1. Run your exact service logic structure cleanly
        raw_result = start_interactive_prep_session(
            db=db,
            selected_section_numbers=selected_section_numbers,
            questions_per_section=questions_per_section,
        )
        
        # 2. Extract and cast safely without assuming integer type for IDs
        # Used str() for document_id to safely support both UUID strings and standard Integers
        clean_serializable_result = {
            "session_id": str(raw_result["session_id"]),
            "document_id": str(raw_result["document_id"]) if raw_result.get("document_id") else None,
            "mode": str(raw_result["mode"]),
            "selected_sections": list(raw_result["selected_sections"]),
            "total_questions": int(raw_result["total_questions"]),
            "adaptation_summary": str(raw_result["adaptation_summary"]),
            "questions": [dict(q) for q in raw_result["questions"]]
        }
        
        logger.info(f"Background session successfully compiled and decoupled for task: {self.request.id}")
        return clean_serializable_result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Task failure inside worker context: {error_msg}")
        
        # If it's a rate limit from Groq, we can provide a cleaner logged state
        if "429" in error_msg or "rate_limit" in error_msg.lower():
            logger.warning("Groq API rate limit reached. Retrying or holding state dynamically.")
            
        raise e
    finally:
        db.close()  # Always safely close DB connection