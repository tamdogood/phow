"""Request models for the Feasibility Study API."""

from pydantic import BaseModel


class CreateFeasibilityRequest(BaseModel):
    session_id: str
    concept: str  # food & drink type / cuisine, e.g. "specialty coffee shop"
    location_address: str
    user_id: str | None = None
    business_profile_id: str | None = None
    scale_seats: int | None = None
    startup_budget: int | None = None
