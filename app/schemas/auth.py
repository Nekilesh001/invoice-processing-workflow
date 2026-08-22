from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Payload for user authentication login."""
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """User profile response representation."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT Access Token response payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
