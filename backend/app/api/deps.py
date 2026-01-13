from supabase import create_client, Client
from ..core.config import get_settings
from ..services import ChatService, LocationService
from ..core.cache import get_cache, CacheManager


def get_supabase() -> Client:
    """Dependency for Supabase client."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_chat_service(db: Client = get_supabase()) -> ChatService:
    """Dependency for ChatService."""
    return ChatService(db)


def get_location_service() -> LocationService:
    """Dependency for LocationService."""
    return LocationService()


def get_cache_manager() -> CacheManager:
    """Dependency for CacheManager."""
    return get_cache()
