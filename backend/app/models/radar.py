"""Request models for the Business Radar API."""

from pydantic import BaseModel


class RadarScanRequest(BaseModel):
    business_profile_id: str


class RadarSubscriptionUpdate(BaseModel):
    business_profile_id: str
    watch_topics: list[str] | None = None
    categories: list[str] | None = None
    frequency: str | None = None
    schedule_hour: int | None = None
    status: str | None = None
