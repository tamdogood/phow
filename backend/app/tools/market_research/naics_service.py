"""NAICS code lookup and business type classification service."""

import json
from pathlib import Path
from typing import Any
from ...core.logging import get_logger
from ...core.llm import get_llm_service

logger = get_logger("naics_service")

# Load NAICS data from bundled JSON
_NAICS_DATA: dict | None = None


def _load_naics_data() -> dict:
    """Load NAICS data from JSON file."""
    global _NAICS_DATA
    if _NAICS_DATA is None:
        data_path = Path(__file__).parent / "data" / "naics_codes.json"
        with open(data_path, "r") as f:
            _NAICS_DATA = json.load(f)
    return _NAICS_DATA


class NAICSService:
    """Service for NAICS code lookup and business type classification."""

    def __init__(self):
        self.data = _load_naics_data()
        self.codes = self.data.get("codes", {})
        self.mappings = self.data.get("business_type_mappings", {})

    def lookup_code(self, code: str) -> dict[str, Any] | None:
        """
        Look up a NAICS code.

        Args:
            code: NAICS code (2-6 digits)

        Returns:
            Code info or None if not found
        """
        return self.codes.get(code)

    def search_by_keyword(self, keyword: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Search NAICS codes by keyword.

        Args:
            keyword: Search keyword
            limit: Maximum results to return

        Returns:
            List of matching NAICS codes
        """
        keyword_lower = keyword.lower()
        matches = []

        for code, info in self.codes.items():
            score = 0
            # Check title
            if keyword_lower in info.get("title", "").lower():
                score += 3
            # Check description
            if keyword_lower in info.get("description", "").lower():
                score += 2
            # Check keywords
            for kw in info.get("keywords", []):
                if keyword_lower in kw.lower():
                    score += 4
                    break

            if score > 0:
                matches.append({"score": score, **info})

        # Sort by score descending, then by code length (more specific first)
        matches.sort(key=lambda x: (-x["score"], -len(x["code"])))
        return matches[:limit]

    def get_parent_industry(self, code: str) -> dict[str, Any] | None:
        """
        Get the parent industry for a NAICS code.

        Args:
            code: NAICS code

        Returns:
            Parent industry info or None
        """
        info = self.codes.get(code)
        if info and info.get("parent_code"):
            return self.codes.get(info["parent_code"])
        # Try progressively shorter codes
        for length in range(len(code) - 1, 1, -1):
            parent = self.codes.get(code[:length])
            if parent:
                return parent
        return None

    def get_related_industries(self, code: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get related industries (siblings under same parent).

        Args:
            code: NAICS code
            limit: Maximum results

        Returns:
            List of related industry codes
        """
        # Get 2-digit sector code
        sector = code[:2]
        related = []

        for c, info in self.codes.items():
            if c.startswith(sector) and c != code and len(c) == len(code):
                related.append(info)

        return related[:limit]

    def map_business_type(self, business_type: str) -> list[str]:
        """
        Map a business type description to NAICS codes.

        Args:
            business_type: Business type (e.g., "coffee shop", "gym")

        Returns:
            List of matching NAICS codes
        """
        business_lower = business_type.lower().strip()

        # Direct mapping lookup
        if business_lower in self.mappings:
            return self.mappings[business_lower]

        # Try partial matches
        for key, codes in self.mappings.items():
            if key in business_lower or business_lower in key:
                return codes

        # Fall back to keyword search
        results = self.search_by_keyword(business_type, limit=3)
        return [r["code"] for r in results if len(r["code"]) >= 4]

    async def classify_business_type(self, description: str) -> dict[str, Any]:
        """
        Use LLM to classify a business description to NAICS codes.

        Args:
            description: Free-form business description

        Returns:
            Classification result with NAICS codes and confidence
        """
        # First try direct mapping
        direct_codes = self.map_business_type(description)
        if direct_codes:
            return {
                "description": description,
                "naics_codes": direct_codes,
                "primary_code": direct_codes[0],
                "primary_info": self.lookup_code(direct_codes[0]),
                "method": "direct_mapping",
                "confidence": "high",
            }

        # Fall back to LLM classification
        try:
            llm_service = get_llm_service()
            llm = llm_service.get_llm()

            # Build a simplified list of common codes for the prompt
            common_codes = [
                f"{code}: {info['title']}"
                for code, info in self.codes.items()
                if len(code) == 6  # Most specific codes
            ][:50]

            prompt = f"""Classify this business into a NAICS code.

Business description: {description}

Common NAICS codes:
{chr(10).join(common_codes[:30])}

Respond with ONLY the 6-digit NAICS code that best matches, nothing else."""

            response = await llm.ainvoke(prompt)
            code_guess = response.content.strip()[:6]

            # Validate the code exists
            if code_guess in self.codes:
                return {
                    "description": description,
                    "naics_codes": [code_guess],
                    "primary_code": code_guess,
                    "primary_info": self.lookup_code(code_guess),
                    "method": "llm_classification",
                    "confidence": "medium",
                }

        except Exception as e:
            logger.warning("LLM classification failed", error=str(e))

        # Return best keyword search result
        results = self.search_by_keyword(description, limit=1)
        if results:
            return {
                "description": description,
                "naics_codes": [results[0]["code"]],
                "primary_code": results[0]["code"],
                "primary_info": results[0],
                "method": "keyword_search",
                "confidence": "low",
            }

        return {
            "description": description,
            "naics_codes": [],
            "primary_code": None,
            "primary_info": None,
            "method": "none",
            "confidence": "none",
        }

    def get_industry_hierarchy(self, code: str) -> list[dict[str, Any]]:
        """
        Get the full industry hierarchy for a code (sector -> subsector -> industry -> etc).

        Args:
            code: NAICS code

        Returns:
            List from broadest to most specific
        """
        hierarchy = []
        for length in [2, 3, 4, 5, 6]:
            if length <= len(code):
                partial = code[:length]
                info = self.codes.get(partial)
                if info:
                    hierarchy.append(info)
        return hierarchy


# Singleton instance
_naics_service: NAICSService | None = None


def get_naics_service() -> NAICSService:
    global _naics_service
    if _naics_service is None:
        _naics_service = NAICSService()
    return _naics_service
