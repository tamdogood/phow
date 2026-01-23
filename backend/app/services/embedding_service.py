"""Embedding service for generating vector embeddings for RAG."""

import asyncio
from typing import Any
import geohash as gh
from langchain_openai import OpenAIEmbeddings
from supabase import Client
from ..core.config import get_settings
from ..core.logging import get_logger
from ..repositories.location_intelligence_repository import (
    DataEmbeddingRepository,
    LocationIntelligenceRepository,
)

logger = get_logger("embedding_service")


class EmbeddingService:
    """Service for generating and managing vector embeddings."""

    def __init__(self, db: Client):
        settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-ada-002",  # 1536 dimensions
        )
        self.embedding_repo = DataEmbeddingRepository(db)
        self.intel_repo = LocationIntelligenceRepository(db)

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: self.embeddings.embed_query(text)
        )
        return embedding

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: self.embeddings.embed_documents(texts)
        )
        return embeddings

    def compute_geohash(self, lat: float, lng: float, precision: int = 6) -> str:
        """Compute geohash for a location."""
        return gh.encode(lat, lng, precision=precision)

    async def embed_and_store(
        self,
        content: str,
        source_type: str,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
        metadata: dict[str, Any] | None = None,
        expires_days: int = 30,
    ) -> dict[str, Any]:
        """Generate embedding and store in database."""
        logger.info("Generating embedding", source_type=source_type, city=city)

        embedding = await self.generate_embedding(content)
        geohash = self.compute_geohash(lat, lng) if lat and lng else None

        result = await self.embedding_repo.create(
            source_type=source_type,
            content=content,
            embedding=embedding,
            metadata=metadata,
            lat=lat,
            lng=lng,
            geohash=geohash,
            city=city,
            expires_days=expires_days,
        )

        logger.info("Embedding stored", id=result.get("id"))
        return result

    async def embed_crime_data(
        self, crime_data: dict[str, Any], lat: float, lng: float, city: str
    ) -> dict[str, Any]:
        """Create embedding for crime analysis data."""
        content = self._format_crime_content(crime_data)
        return await self.embed_and_store(
            content=content,
            source_type="crime",
            lat=lat,
            lng=lng,
            city=city,
            metadata={"total_crimes": crime_data.get("total_crimes"), "safety_score": crime_data.get("safety_score")},
        )

    def _format_crime_content(self, crime_data: dict[str, Any]) -> str:
        """Format crime data for embedding."""
        city = crime_data.get("city", "Unknown")
        total = crime_data.get("total_crimes", 0)
        safety = crime_data.get("safety_score", "N/A")
        rate = crime_data.get("crime_rate", "unknown")
        violent_pct = crime_data.get("violent_crime_pct", 0)

        top_types = list(crime_data.get("by_type", {}).keys())[:5]
        types_str = ", ".join(top_types) if top_types else "N/A"

        return (
            f"Crime analysis for {city}: {total} crimes recorded. "
            f"Safety score: {safety}/100. Crime rate: {rate}. "
            f"Violent crime: {violent_pct}%. "
            f"Common types: {types_str}. "
            f"{crime_data.get('recommendation', '')}"
        )

    async def embed_health_inspection(
        self, inspection_data: dict[str, Any], lat: float, lng: float, city: str
    ) -> dict[str, Any]:
        """Create embedding for health inspection data."""
        content = self._format_health_content(inspection_data)
        return await self.embed_and_store(
            content=content,
            source_type="health",
            lat=lat,
            lng=lng,
            city=city,
            metadata={"avg_score": inspection_data.get("avg_score"), "health_rating": inspection_data.get("health_rating")},
        )

    def _format_health_content(self, data: dict[str, Any]) -> str:
        """Format health inspection data for embedding."""
        city = data.get("city", "Unknown")
        avg_score = data.get("avg_score", "N/A")
        rating = data.get("health_rating", "unknown")
        total = data.get("total_restaurants", 0)

        grades = data.get("grade_distribution", {})
        grades_str = ", ".join(f"{k}: {v}" for k, v in grades.items()) if grades else "N/A"

        return (
            f"Health inspections in {city}: {total} restaurants analyzed. "
            f"Average score: {avg_score}. Health rating: {rating}. "
            f"Grade distribution: {grades_str}. "
            f"{data.get('insight', '')}"
        )

    async def embed_walkscore(
        self, score_data: dict[str, Any], lat: float, lng: float, city: str
    ) -> dict[str, Any]:
        """Create embedding for Walk Score data."""
        content = self._format_walkscore_content(score_data)
        return await self.embed_and_store(
            content=content,
            source_type="walkscore",
            lat=lat,
            lng=lng,
            city=city,
            metadata={
                "walkscore": score_data.get("walkscore"),
                "transit_score": score_data.get("transit_score"),
                "bike_score": score_data.get("bike_score"),
            },
        )

    def _format_walkscore_content(self, data: dict[str, Any]) -> str:
        """Format Walk Score data for embedding."""
        return (
            f"Location walkability: Walk Score {data.get('walkscore', 'N/A')} "
            f"({data.get('walkscore_description', 'N/A')}). "
            f"Transit Score: {data.get('transit_score', 'N/A')} "
            f"({data.get('transit_description', 'N/A')}). "
            f"Bike Score: {data.get('bike_score', 'N/A')} "
            f"({data.get('bike_description', 'N/A')})."
        )

    async def embed_trends(
        self, trends_data: dict[str, Any], lat: float | None, lng: float | None, city: str
    ) -> dict[str, Any]:
        """Create embedding for Google Trends data."""
        content = self._format_trends_content(trends_data)
        return await self.embed_and_store(
            content=content,
            source_type="trends",
            lat=lat,
            lng=lng,
            city=city,
            metadata={"keywords": trends_data.get("keywords")},
        )

    def _format_trends_content(self, data: dict[str, Any]) -> str:
        """Format trends data for embedding."""
        keywords = data.get("keywords", [])
        geo = data.get("geo", "US")
        timeframe = data.get("timeframe", "12 months")

        # Get latest data point for each keyword
        latest = {}
        if data.get("data"):
            last_entry = data["data"][-1]
            for kw in keywords:
                if kw in last_entry:
                    latest[kw] = last_entry[kw]

        trends_str = ", ".join(f"{k}: {v}" for k, v in latest.items()) if latest else "N/A"

        return (
            f"Search trends for {', '.join(keywords)} in {geo} "
            f"over {timeframe}. Latest interest scores: {trends_str}."
        )

    async def embed_menu_pricing(
        self, menu_data: dict[str, Any], lat: float | None, lng: float | None, city: str
    ) -> dict[str, Any]:
        """Create embedding for menu/pricing data."""
        content = self._format_menu_content(menu_data)
        return await self.embed_and_store(
            content=content,
            source_type="menu",
            lat=lat,
            lng=lng,
            city=city,
            metadata={
                "avg_price": menu_data.get("avg_price"),
                "price_range": menu_data.get("price_range"),
                "business_type": menu_data.get("business_type"),
            },
        )

    def _format_menu_content(self, data: dict[str, Any]) -> str:
        """Format menu data for embedding."""
        biz_type = data.get("business_type", "restaurant")
        city = data.get("city", "Unknown")
        benchmarks = data.get("benchmarks", {})

        items_str = []
        for item, prices in benchmarks.items():
            items_str.append(
                f"{item}: ${prices.get('low', 0):.2f}-${prices.get('high', 0):.2f} "
                f"(avg ${prices.get('avg', 0):.2f})"
            )

        return (
            f"Menu pricing for {biz_type} in {city}. "
            f"Cost multiplier: {data.get('cost_multiplier', 1.0)}x. "
            f"Typical prices: {'; '.join(items_str) if items_str else 'N/A'}."
        )

    async def semantic_search(
        self,
        query: str,
        limit: int = 10,
        source_types: list[str] | None = None,
        lat: float | None = None,
        lng: float | None = None,
        city: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Perform semantic search across embeddings.

        Args:
            query: Natural language query
            limit: Maximum results
            source_types: Filter by source types
            lat/lng: Filter by location proximity
            city: Filter by city

        Returns:
            List of matching records with similarity scores
        """
        logger.info("Semantic search", query=query, source_types=source_types, city=city)

        query_embedding = await self.generate_embedding(query)
        geohash_prefix = self.compute_geohash(lat, lng, precision=4) if lat and lng else None

        results = await self.embedding_repo.semantic_search(
            query_embedding=query_embedding,
            limit=limit,
            source_types=source_types,
            geohash_prefix=geohash_prefix,
            city=city,
        )

        return results


def get_embedding_service(db: Client) -> EmbeddingService:
    """Get an embedding service instance."""
    return EmbeddingService(db)
