import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.database.connection import get_db
from app.database.models import UserModel
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
    Enforces strict read-only repository queries and safe response formatting.
    """
    try:
        response = analyst_agent.answer_question(question=payload.question, session=db)
        return response
    except Exception as e:
        logger.error(f"Data Analyst Q&A processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data Analyst Assistant error: {str(e)}"
        )
