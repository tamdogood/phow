"""Menu and pricing scraper for F&B competitive intelligence."""

import httpx
import re
from typing import Any
from bs4 import BeautifulSoup
from ..core.cache import cached
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger("menu_scraper")


class MenuScraper:
    """Scraper for menu and pricing data from various sources."""

    _client: httpx.AsyncClient | None = None

    def __init__(self):
        settings = get_settings()
        self.proxy_url = settings.scraping_proxy_url
        self.proxy_api_key = settings.scraping_api_key

    def _get_client(self) -> httpx.AsyncClient:
        if MenuScraper._client is None:
            MenuScraper._client = httpx.AsyncClient(timeout=60.0)
        return MenuScraper._client

    async def _fetch_with_proxy(self, url: str) -> str | None:
        """Fetch URL content, using proxy if configured."""
        try:
            if self.proxy_url and self.proxy_api_key:
                # ScrapingBee format
                proxy_params = {
                    "api_key": self.proxy_api_key,
                    "url": url,
                    "render_js": "true",
                }
                response = await self._get_client().get(
                    self.proxy_url, params=proxy_params
                )
            else:
                # Direct fetch (may be blocked)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await self._get_client().get(url, headers=headers)

            if response.status_code == 200:
                return response.text
            logger.warning("Fetch failed", url=url, status=response.status_code)
            return None
        except Exception as e:
            logger.error("Fetch error", url=url, error=str(e))
            return None

    @cached(ttl=86400, key_prefix="menu_yelp")  # Cache for 24 hours
    async def get_menu_from_yelp(self, yelp_url: str) -> dict[str, Any] | None:
        """
        Extract menu data from a Yelp business page.

        Args:
            yelp_url: Full Yelp business URL

        Returns:
            Dict with menu items and prices if available
        """
        logger.info("Fetching Yelp menu", url=yelp_url)

        # Ensure we're hitting the menu page
        if "/menu" not in yelp_url:
            menu_url = yelp_url.rstrip("/") + "/menu"
        else:
            menu_url = yelp_url

        html = await self._fetch_with_proxy(menu_url)
        if not html:
            return None

        return self._parse_yelp_menu(html)

    def _parse_yelp_menu(self, html: str) -> dict[str, Any]:
        """Parse Yelp menu page HTML."""
        soup = BeautifulSoup(html, "lxml")
        items: list[dict] = []
        categories: set[str] = set()

        # Look for menu sections
        menu_sections = soup.find_all("div", {"class": re.compile(r"menu-section")})

        for section in menu_sections:
            category_el = section.find(["h2", "h3", "h4"])
            category = category_el.get_text(strip=True) if category_el else "Other"
            categories.add(category)

            # Find menu items within section
            item_els = section.find_all("div", {"class": re.compile(r"menu-item")})
            for item_el in item_els:
                name_el = item_el.find(["h4", "h5", "span"], {"class": re.compile(r"name|title")})
                price_el = item_el.find(["span", "div"], {"class": re.compile(r"price")})
                desc_el = item_el.find(["p", "span"], {"class": re.compile(r"desc|description")})

                if name_el:
                    item = {
                        "name": name_el.get_text(strip=True),
                        "category": category,
                        "price": self._extract_price(price_el.get_text() if price_el else ""),
                        "description": desc_el.get_text(strip=True) if desc_el else None,
                    }
                    items.append(item)

        # Calculate price statistics
        prices = [i["price"] for i in items if i["price"]]
        avg_price = sum(prices) / len(prices) if prices else None
        price_range = self._determine_price_range(avg_price)

        return {
            "source": "yelp",
            "items": items,
            "categories": list(categories),
            "item_count": len(items),
            "avg_price": round(avg_price, 2) if avg_price else None,
            "price_range": price_range,
            "min_price": min(prices) if prices else None,
            "max_price": max(prices) if prices else None,
        }

    @cached(ttl=86400, key_prefix="menu_google")
    async def get_menu_from_google(self, place_id: str) -> dict[str, Any] | None:
        """
        Extract menu/popular items from Google Maps place data.
        Note: Requires Google Maps API key with Places API enabled.

        This is a placeholder for Google's menu data integration.
        """
        logger.info("Google menu extraction not fully implemented", place_id=place_id)
        return None

    def _extract_price(self, text: str) -> float | None:
        """Extract price from text string."""
        if not text:
            return None
        # Match patterns like $12.99, $12, 12.99
        match = re.search(r"\$?(\d+(?:\.\d{2})?)", text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _determine_price_range(self, avg_price: float | None) -> str:
        """Determine price range category."""
        if avg_price is None:
            return "unknown"
        if avg_price < 10:
            return "$"
        if avg_price < 20:
            return "$$"
        if avg_price < 35:
            return "$$$"
        return "$$$$"

    @cached(ttl=43200, key_prefix="price_comparison")  # 12 hours
    async def get_price_comparison(
        self,
        business_type: str,
        city: str,
        sample_items: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get average pricing for a business type in a city.
        Uses cached/aggregated data from previous scrapes.

        Args:
            business_type: Type of business (coffee_shop, pizza, burger, etc.)
            city: City name
            sample_items: Specific items to compare (e.g., ["latte", "cappuccino"])

        Returns:
            Dict with pricing benchmarks
        """
        # Default pricing benchmarks by category (can be updated with real data)
        PRICING_BENCHMARKS = {
            "coffee_shop": {
                "latte": {"low": 4.00, "avg": 5.50, "high": 7.50},
                "cappuccino": {"low": 3.50, "avg": 5.00, "high": 7.00},
                "drip_coffee": {"low": 2.00, "avg": 3.00, "high": 4.50},
                "croissant": {"low": 3.00, "avg": 4.50, "high": 6.50},
            },
            "pizza": {
                "large_pizza": {"low": 15.00, "avg": 22.00, "high": 32.00},
                "slice": {"low": 3.00, "avg": 4.50, "high": 7.00},
                "calzone": {"low": 10.00, "avg": 14.00, "high": 18.00},
            },
            "burger": {
                "burger": {"low": 10.00, "avg": 15.00, "high": 22.00},
                "fries": {"low": 4.00, "avg": 6.00, "high": 9.00},
                "shake": {"low": 5.00, "avg": 7.00, "high": 10.00},
            },
            "sushi": {
                "roll": {"low": 8.00, "avg": 14.00, "high": 22.00},
                "nigiri_2pc": {"low": 5.00, "avg": 8.00, "high": 14.00},
                "bento": {"low": 14.00, "avg": 20.00, "high": 30.00},
            },
            "mexican": {
                "taco": {"low": 3.00, "avg": 4.50, "high": 6.50},
                "burrito": {"low": 8.00, "avg": 12.00, "high": 16.00},
                "quesadilla": {"low": 8.00, "avg": 11.00, "high": 15.00},
            },
        }

        # City cost adjustments
        CITY_MULTIPLIERS = {
            "new york": 1.25,
            "san francisco": 1.30,
            "los angeles": 1.15,
            "chicago": 1.05,
            "seattle": 1.15,
            "boston": 1.20,
            "miami": 1.10,
            "denver": 1.05,
            "austin": 1.00,
            "phoenix": 0.95,
        }

        # Normalize business type
        biz_type = business_type.lower().replace(" ", "_").replace("-", "_")
        city_lower = city.lower()

        benchmarks = PRICING_BENCHMARKS.get(biz_type, {})
        multiplier = next(
            (v for k, v in CITY_MULTIPLIERS.items() if k in city_lower), 1.0
        )

        adjusted = {}
        for item, prices in benchmarks.items():
            adjusted[item] = {
                "low": round(prices["low"] * multiplier, 2),
                "avg": round(prices["avg"] * multiplier, 2),
                "high": round(prices["high"] * multiplier, 2),
            }

        return {
            "business_type": business_type,
            "city": city,
            "cost_multiplier": multiplier,
            "benchmarks": adjusted,
            "note": "Prices adjusted for local market. Actual prices may vary.",
        }


_menu_scraper: MenuScraper | None = None


def get_menu_scraper() -> MenuScraper:
    global _menu_scraper
    if _menu_scraper is None:
        _menu_scraper = MenuScraper()
    return _menu_scraper
