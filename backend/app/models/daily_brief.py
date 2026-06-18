"""Request models for the Daily Brief API."""

from pydantic import BaseModel


class DailyBriefGenerateRequest(BaseModel):
    business_profile_id: str
