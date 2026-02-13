"""Meta reviews connector client (stub for MVP)."""

from ...services.review_errors import ProviderUnavailableError


class MetaReviewsClient:
    """Meta integration placeholder."""

    async def list_reviews(self) -> list[dict]:
        raise ProviderUnavailableError("Meta reviews connector is not available in MVP")
