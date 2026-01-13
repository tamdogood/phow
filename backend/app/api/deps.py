from fastapi import Depends
from supabase import create_client, Client
from ..core.config import get_settings
from ..services import ChatService, LocationService, TrackingService
from ..core.cache import get_cache, CacheManager

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Dependency for Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_client


def get_tracking_service(db: Client = Depends(get_supabase)) -> TrackingService:
    """Dependency for TrackingService."""
    return TrackingService(db)


def get_chat_service(db: Client = Depends(get_supabase)) -> ChatService:
    """Dependency for ChatService."""
    return ChatService(db)


def get_location_service() -> LocationService:
    """Dependency for LocationService."""
    return LocationService()


def get_cache_manager() -> CacheManager:
    """Dependency for CacheManager."""
    return get_cache()
