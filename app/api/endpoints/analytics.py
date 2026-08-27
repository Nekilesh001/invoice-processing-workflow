import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.database.connection import get_db
from app.database.models import UserModel, AnalystQueryModel
from app.agents.data_analyst_agent import InvoiceDataAnalystAgent
from app.schemas.multi_agent import AnalyticsQuestionRequest, AnalyticsQuestionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics & Business Intelligence"])
analyst_agent = InvoiceDataAnalystAgent()


@router.post("/ask", response_model=AnalyticsQuestionResponse)
def ask_invoice_data_analyst(
    payload: AnalyticsQuestionRequest,
    current_user: UserModel = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> AnalyticsQuestionResponse:
    """
    Data Analyst Agent Endpoint:
    Answers natural-language business intelligence queries regarding accounts payable data.
    Enforces strict read-only repository queries, records Q&A in database history, and safe response formatting.
    """
    try:
        response = analyst_agent.answer_question(question=payload.question, session=db)
        
        # Persist Q&A record into MySQL database
        user_id = current_user.id if current_user else None
        record = AnalystQueryModel(
            user_id=user_id,
            question=payload.question,
            answer=response.answer,
            tools_used=response.tools_used,
            sources=response.sources
        )
        db.add(record)
        db.commit()

        return response
    except Exception as e:
        db.rollback()
        logger.error(f"Data Analyst Q&A processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data Analyst Assistant error: {str(e)}"
        )


@router.get("/history")
def get_analyst_chat_history(
    limit: int = 20,
    current_user: UserModel = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Retrieves past Data Analyst Assistant Q&A history records from database.
    """
    records = db.query(AnalystQueryModel).order_by(AnalystQueryModel.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "tools_used": r.tools_used or [],
            "sources": r.sources or [],
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reversed(records)
    ]


@router.delete("/history")
def clear_analyst_chat_history(
    current_user: UserModel = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Clears Data Analyst Assistant Q&A history records from database.
    """
    db.query(AnalystQueryModel).delete()
    db.commit()
    return {"message": "Data Analyst history cleared successfully."}
