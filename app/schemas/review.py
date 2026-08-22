from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ReviewActionRequest(BaseModel):
    """Schema for human reviewer decision payload (approval / rejection)."""
    reviewer: Optional[str] = Field("Finance Reviewer", description="Identity or title of the human reviewer")
    comment: Optional[str] = Field(None, description="Optional notes for approval, mandatory for rejection")
    notes: Optional[str] = Field(None, description="Fallback alias for comment")

    def get_effective_comment(self) -> Optional[str]:
        val = self.comment if (self.comment and self.comment.strip()) else self.notes
        return val.strip() if (val and val.strip()) else None

    @field_validator("comment", "notes")
    def validate_comment_length(cls, v):
        if v and len(v) > 2000:
            raise ValueError("Reviewer comment cannot exceed 2000 characters.")
        return v


class ReviewActionResponse(BaseModel):
    """Schema for review decision audit log item."""
    id: int
    action: str
    reviewer: str
    comment: Optional[str] = None
    previous_status: str
    new_status: str
    created_at: str
