from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "anthropic"  # "openai" or "anthropic"

    # Google Maps
    google_maps_api_key: str = ""

    # Yelp Fusion API
    yelp_api_key: str = ""

    # Weather & Events APIs (for Social Media Coach)
    openweathermap_api_key: str = ""
    eventbrite_api_key: str = ""
    newsapi_key: str = ""

    # Market Research APIs
    bls_api_key: str = ""  # Bureau of Labor Statistics
    fred_api_key: str = ""  # Federal Reserve Economic Data

    # Location Intelligence APIs (Phase 1 - Free)
    walkscore_api_key: str = ""  # Walk Score API
    crimemapping_api_key: str = ""  # CrimeMapping API
    eia_api_key: str = ""  # Energy Information Administration

    # Scraping Infrastructure
    scraping_proxy_url: str = ""  # ScrapingBee/Bright Data/Apify
    scraping_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600  # 1 hour default cache TTL

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Reputation Hub Feature Flags
    reputation_hub_enabled: bool = True
    reputation_live_connectors_enabled: bool = True
    reputation_oauth_enabled: bool = True

    # Reputation Hub Security
    reputation_token_encryption_key: str = ""

    # Reputation Hub OAuth/Connector Config
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""
    google_business_account_id: str = ""
    google_business_location_id: str = ""
    yelp_business_id: str = ""

    # Reputation Hub Usage/Plan defaults
    reputation_default_plan: str = "starter"

    # App settings
    debug: bool = False
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
