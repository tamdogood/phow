"""Consumer Analysis Service - Sentiment analysis, pain points, journey mapping, profiles."""

from typing import Any
from ..core.logging import get_logger

logger = get_logger("service.consumer_analysis")


# Aspect categories for sentiment analysis
ASPECT_CATEGORIES = {
    "service": ["service", "staff", "friendly", "rude", "helpful", "attentive", "wait", "slow"],
    "quality": ["quality", "fresh", "delicious", "taste", "flavor", "authentic", "mediocre"],
    "price": ["price", "expensive", "cheap", "value", "worth", "overpriced", "affordable"],
    "atmosphere": ["atmosphere", "ambiance", "vibe", "cozy", "loud", "noisy", "clean", "dirty"],
    "location": ["location", "parking", "convenient", "accessible", "crowded"],
}

# Pain point categories
PAIN_POINT_CATEGORIES = {
    "wait_times": ["wait", "slow", "long", "forever", "took forever", "waited"],
    "pricing": ["expensive", "overpriced", "pricey", "cost", "too much"],
    "quality": ["cold", "stale", "bland", "disappointing", "mediocre", "undercooked"],
    "service": ["rude", "ignored", "unfriendly", "poor service", "attitude"],
    "cleanliness": ["dirty", "unclean", "messy", "gross", "hygiene"],
    "hours": ["closed", "hours", "early", "late", "not open"],
    "parking": ["parking", "no parking", "hard to park"],
    "portions": ["small", "tiny", "portion", "not enough"],
}

# Customer journey stages
JOURNEY_STAGES = [
    {
        "stage": "awareness",
        "description": "How customers discover the business",
        "touchpoints": ["social media", "word of mouth", "search engines", "advertising", "walking by"],
    },
    {
        "stage": "consideration",
        "description": "How customers evaluate options",
        "touchpoints": ["reviews", "website", "menu", "photos", "pricing"],
    },
    {
        "stage": "purchase",
        "description": "The transaction experience",
        "touchpoints": ["ordering", "payment", "checkout", "staff interaction"],
    },
    {
        "stage": "experience",
        "description": "Consuming the product/service",
        "touchpoints": ["product quality", "atmosphere", "service quality", "wait time"],
    },
    {
        "stage": "loyalty",
        "description": "Post-purchase relationship",
        "touchpoints": ["follow-up", "loyalty program", "repeat visits", "referrals"],
    },
]


class ConsumerAnalysisService:
    """Service for consumer insights, sentiment analysis, and journey mapping."""

    def __init__(self):
        self._llm_service = None

    @property
    def llm_service(self):
        """Lazy load LLM service."""
        if self._llm_service is None:
            from ..core.llm import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def analyze_sentiment(self, reviews: list[dict]) -> dict[str, Any]:
        """
        Analyze sentiment from reviews with aspect-level breakdown.

        Args:
            reviews: List of review dictionaries with 'text' and optionally 'rating'

        Returns:
            Sentiment analysis with overall score and aspect breakdown
        """
        logger.info("Analyzing sentiment", review_count=len(reviews))

        if not reviews:
            return {
                "overall_sentiment": 0,
                "sentiment_label": "neutral",
                "aspect_sentiments": {},
                "confidence": 0,
                "review_count": 0,
            }

        # Calculate overall sentiment from ratings if available
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        overall_from_ratings = sum(ratings) / len(ratings) if ratings else 3.0

        # Normalize to -1 to 1 scale (rating 1-5 -> -1 to 1)
        overall_sentiment = (overall_from_ratings - 3) / 2

        # Analyze aspects
        aspect_sentiments = self._analyze_aspects(reviews)

        # Determine label
        if overall_sentiment > 0.3:
            label = "positive"
        elif overall_sentiment < -0.3:
            label = "negative"
        else:
            label = "neutral"

        return {
            "overall_sentiment": round(overall_sentiment, 2),
            "sentiment_label": label,
            "average_rating": round(overall_from_ratings, 1) if ratings else None,
            "aspect_sentiments": aspect_sentiments,
            "confidence": min(1.0, len(reviews) / 20),  # More reviews = higher confidence
            "review_count": len(reviews),
        }

    def _analyze_aspects(self, reviews: list[dict]) -> dict[str, dict]:
        """Analyze sentiment for each aspect category."""
        aspects = {}

        for category, keywords in ASPECT_CATEGORIES.items():
            mentions = []
            positive_count = 0
            negative_count = 0

            for review in reviews:
                text = review.get("text", "").lower()
                rating = review.get("rating", 3)

                # Check if any keyword is mentioned
                for keyword in keywords:
                    if keyword in text:
                        mentions.append(text)
                        if rating >= 4:
                            positive_count += 1
                        elif rating <= 2:
                            negative_count += 1
                        break

            if mentions:
                total = positive_count + negative_count
                sentiment = (positive_count - negative_count) / total if total > 0 else 0
                aspects[category] = {
                    "sentiment": round(sentiment, 2),
                    "mention_count": len(mentions),
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                }

        return aspects

    def extract_themes(self, reviews: list[dict]) -> dict[str, Any]:
        """
        Extract themes from reviews grouped by category.

        Args:
            reviews: List of review dictionaries

        Returns:
            Themes grouped by category with frequency and sentiment
        """
        logger.info("Extracting themes", review_count=len(reviews))

        if not reviews:
            return {"themes": [], "categories": {}}

        # Extract themes using keyword matching (LLM-assisted in production)
        themes = {}

        positive_keywords = [
            "friendly", "fast", "clean", "fresh", "quality", "delicious",
            "great service", "love", "best", "amazing", "excellent",
            "convenient", "cozy", "recommend", "perfect", "wonderful",
        ]

        negative_keywords = [
            "slow", "rude", "dirty", "expensive", "overpriced", "cold",
            "wait", "crowded", "small", "noisy", "disappointing",
            "mediocre", "average", "poor service", "terrible", "worst",
        ]

        for review in reviews:
            text = review.get("text", "").lower()
            rating = review.get("rating", 3)
            is_positive = rating >= 4

            # Check positive keywords
            for keyword in positive_keywords:
                if keyword in text:
                    if keyword not in themes:
                        themes[keyword] = {
                            "theme": keyword,
                            "frequency": 0,
                            "sentiment": "positive",
                            "examples": [],
                        }
                    themes[keyword]["frequency"] += 1
                    if len(themes[keyword]["examples"]) < 2:
                        themes[keyword]["examples"].append(text[:150])

            # Check negative keywords
            for keyword in negative_keywords:
                if keyword in text:
                    if keyword not in themes:
                        themes[keyword] = {
                            "theme": keyword,
                            "frequency": 0,
                            "sentiment": "negative",
                            "examples": [],
                        }
                    themes[keyword]["frequency"] += 1
                    if len(themes[keyword]["examples"]) < 2:
                        themes[keyword]["examples"].append(text[:150])

        # Sort by frequency
        sorted_themes = sorted(themes.values(), key=lambda x: x["frequency"], reverse=True)

        # Group by category
        categories = {
            "product": [],
            "service": [],
            "experience": [],
            "value": [],
            "location": [],
        }

        category_keywords = {
            "product": ["fresh", "quality", "delicious", "cold", "mediocre", "taste"],
            "service": ["friendly", "rude", "fast", "slow", "great service", "poor service"],
            "experience": ["cozy", "noisy", "crowded", "clean", "dirty", "atmosphere"],
            "value": ["expensive", "overpriced", "worth", "affordable"],
            "location": ["convenient", "parking", "accessible"],
        }

        for theme in sorted_themes[:15]:
            categorized = False
            for cat, keywords in category_keywords.items():
                if any(kw in theme["theme"] for kw in keywords):
                    categories[cat].append(theme)
                    categorized = True
                    break
            if not categorized:
                categories["experience"].append(theme)

        return {
            "themes": sorted_themes[:15],
            "categories": {k: v for k, v in categories.items() if v},
            "total_reviews_analyzed": len(reviews),
        }

    def identify_pain_points(self, reviews: list[dict]) -> dict[str, Any]:
        """
        Identify and rank customer pain points from reviews.

        Args:
            reviews: List of review dictionaries

        Returns:
            Ranked pain points with frequency and severity
        """
        logger.info("Identifying pain points", review_count=len(reviews))

        if not reviews:
            return {"pain_points": [], "opportunities": []}

        pain_points = {}

        for review in reviews:
            text = review.get("text", "").lower()
            rating = review.get("rating", 3)

            # Focus on negative reviews
            if rating <= 3:
                for category, keywords in PAIN_POINT_CATEGORIES.items():
                    for keyword in keywords:
                        if keyword in text:
                            if category not in pain_points:
                                pain_points[category] = {
                                    "issue": category.replace("_", " ").title(),
                                    "frequency": 0,
                                    "severity": 0,
                                    "examples": [],
                                }
                            pain_points[category]["frequency"] += 1
                            # Lower rating = higher severity
                            pain_points[category]["severity"] += (4 - rating)
                            if len(pain_points[category]["examples"]) < 2:
                                pain_points[category]["examples"].append(text[:150])
                            break

        # Calculate average severity and rank
        for pp in pain_points.values():
            if pp["frequency"] > 0:
                pp["severity"] = round(pp["severity"] / pp["frequency"], 1)

        # Sort by frequency * severity
        sorted_pain_points = sorted(
            pain_points.values(),
            key=lambda x: x["frequency"] * x["severity"],
            reverse=True,
        )

        # Generate opportunities from pain points
        opportunities = self._get_opportunities_from_pain_points(sorted_pain_points)

        return {
            "pain_points": sorted_pain_points,
            "opportunities": opportunities,
            "total_negative_reviews": len([r for r in reviews if r.get("rating", 3) <= 3]),
        }

    def _get_opportunities_from_pain_points(self, pain_points: list[dict]) -> list[dict]:
        """Generate opportunities from identified pain points."""
        opportunity_map = {
            "Wait Times": {
                "opportunity": "Fast service differentiation",
                "description": "Implement efficient operations to minimize wait times",
                "priority": "high",
            },
            "Pricing": {
                "opportunity": "Value positioning",
                "description": "Offer better value through quality, portions, or loyalty programs",
                "priority": "medium",
            },
            "Quality": {
                "opportunity": "Quality leadership",
                "description": "Focus on consistent, high-quality products",
                "priority": "high",
            },
            "Service": {
                "opportunity": "Service excellence",
                "description": "Train staff for exceptional customer service",
                "priority": "high",
            },
            "Cleanliness": {
                "opportunity": "Cleanliness standards",
                "description": "Implement rigorous cleanliness protocols",
                "priority": "high",
            },
            "Hours": {
                "opportunity": "Extended hours",
                "description": "Consider extended or flexible operating hours",
                "priority": "medium",
            },
            "Parking": {
                "opportunity": "Parking solutions",
                "description": "Partner with nearby lots or offer valet service",
                "priority": "low",
            },
            "Portions": {
                "opportunity": "Portion optimization",
                "description": "Offer various portion sizes or value options",
                "priority": "medium",
            },
        }

        opportunities = []
        for pp in pain_points[:5]:
            issue = pp["issue"]
            if issue in opportunity_map:
                opp = opportunity_map[issue].copy()
                opp["based_on"] = f"{pp['frequency']} complaints about {issue.lower()}"
                opportunities.append(opp)

        return opportunities

    def map_customer_journey(
        self,
        business_type: str,
        reviews: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Map the typical customer journey for a business type.

        Args:
            business_type: Type of business
            reviews: Optional reviews to extract journey insights

        Returns:
            Customer journey map with stages, touchpoints, and opportunities
        """
        logger.info("Mapping customer journey", business_type=business_type)

        journey = []

        # Build journey with insights from reviews if available
        review_insights = self._extract_journey_insights(reviews) if reviews else {}

        for stage_template in JOURNEY_STAGES:
            stage = {
                "stage": stage_template["stage"],
                "description": stage_template["description"],
                "touchpoints": stage_template["touchpoints"],
                "insights": review_insights.get(stage_template["stage"], []),
                "opportunities": self._get_stage_opportunities(
                    stage_template["stage"], business_type, review_insights
                ),
            }
            journey.append(stage)

        return {
            "business_type": business_type,
            "journey_stages": journey,
            "key_moments": self._identify_key_moments(journey),
            "review_insights_available": bool(reviews),
        }

    def _extract_journey_insights(self, reviews: list[dict]) -> dict[str, list[str]]:
        """Extract insights for each journey stage from reviews."""
        insights = {stage["stage"]: [] for stage in JOURNEY_STAGES}

        stage_keywords = {
            "awareness": ["found", "discovered", "heard about", "recommended", "saw"],
            "consideration": ["looked at", "checked", "reviews", "menu", "prices"],
            "purchase": ["ordered", "checkout", "paid", "ordering"],
            "experience": ["food", "service", "atmosphere", "quality", "taste"],
            "loyalty": ["back", "again", "regular", "always", "favorite"],
        }

        for review in reviews:
            text = review.get("text", "").lower()
            for stage, keywords in stage_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        # Extract a short relevant snippet
                        idx = text.find(keyword)
                        start = max(0, idx - 30)
                        end = min(len(text), idx + 50)
                        snippet = text[start:end].strip()
                        if snippet and len(insights[stage]) < 3:
                            insights[stage].append(f"...{snippet}...")
                        break

        return insights

    def _get_stage_opportunities(
        self, stage: str, business_type: str, insights: dict
    ) -> list[str]:
        """Get opportunities for a journey stage."""
        opportunities = {
            "awareness": [
                "Optimize Google Business Profile for local search",
                "Encourage social media sharing and check-ins",
                "Implement referral program",
            ],
            "consideration": [
                "Maintain high ratings through quality and service",
                "Keep menu and photos updated online",
                "Respond professionally to all reviews",
            ],
            "purchase": [
                "Streamline ordering process",
                "Train staff on upselling techniques",
                "Offer multiple payment options",
            ],
            "experience": [
                "Focus on consistency in product quality",
                "Create memorable atmosphere",
                "Ensure staff provides excellent service",
            ],
            "loyalty": [
                "Implement loyalty/rewards program",
                "Collect feedback and act on it",
                "Create exclusive offers for returning customers",
            ],
        }

        return opportunities.get(stage, ["Focus on customer satisfaction"])

    def _identify_key_moments(self, journey: list[dict]) -> list[dict]:
        """Identify key moments of truth in the journey."""
        moments = []

        # First impression
        moments.append({
            "moment": "First Impression",
            "stage": "experience",
            "impact": "high",
            "description": "Initial impression sets expectations for entire visit",
        })

        # Service interaction
        moments.append({
            "moment": "Service Interaction",
            "stage": "purchase",
            "impact": "high",
            "description": "Staff interaction significantly impacts satisfaction",
        })

        # Product delivery
        moments.append({
            "moment": "Product Quality",
            "stage": "experience",
            "impact": "high",
            "description": "Core product experience drives loyalty decisions",
        })

        # Problem resolution
        moments.append({
            "moment": "Problem Resolution",
            "stage": "experience",
            "impact": "critical",
            "description": "How problems are handled can create loyal advocates or detractors",
        })

        return moments

    def build_consumer_profile(
        self,
        location: dict,
        business_type: str,
        demographics: dict,
        reviews: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Build psychographic consumer profile for target market.

        Args:
            location: Location info
            business_type: Type of business
            demographics: Demographic data
            reviews: Optional reviews to infer behavioral data

        Returns:
            Consumer profile with personas and insights
        """
        logger.info("Building consumer profile", business_type=business_type)

        # Extract demographic insights
        median_income = demographics.get("median_income", 60000)
        age_distribution = demographics.get("age_distribution", {})
        education = demographics.get("education", {})

        # Infer values and preferences from demographics
        income_segment = self._get_income_segment(median_income)
        dominant_age = self._get_dominant_age_group(age_distribution)

        # Build persona
        persona = self._build_persona(
            business_type, income_segment, dominant_age, demographics
        )

        # Extract behavioral insights from reviews
        behavioral_insights = {}
        if reviews:
            sentiment = self.analyze_sentiment(reviews)
            themes = self.extract_themes(reviews)
            behavioral_insights = {
                "key_drivers": [t["theme"] for t in themes.get("themes", [])[:5] if t.get("sentiment") == "positive"],
                "pain_points": [t["theme"] for t in themes.get("themes", [])[:5] if t.get("sentiment") == "negative"],
                "average_satisfaction": sentiment.get("average_rating"),
            }

        return {
            "location": location.get("address", str(location)),
            "business_type": business_type,
            "primary_persona": persona,
            "demographic_summary": {
                "income_segment": income_segment,
                "dominant_age_group": dominant_age,
                "median_income": median_income,
            },
            "behavioral_insights": behavioral_insights,
            "targeting_recommendations": self._get_targeting_recommendations(
                persona, income_segment, business_type
            ),
        }

    def _get_income_segment(self, median_income: int) -> str:
        """Determine income segment from median income."""
        if median_income >= 100000:
            return "affluent"
        elif median_income >= 75000:
            return "upper_middle"
        elif median_income >= 50000:
            return "middle"
        elif median_income >= 35000:
            return "lower_middle"
        else:
            return "budget_conscious"

    def _get_dominant_age_group(self, age_distribution: dict) -> str:
        """Get the dominant age group from distribution."""
        if not age_distribution:
            return "mixed"

        # Find the largest segment
        max_segment = max(age_distribution.items(), key=lambda x: x[1], default=("mixed", 0))
        return max_segment[0]

    def _build_persona(
        self,
        business_type: str,
        income_segment: str,
        dominant_age: str,
        demographics: dict,
    ) -> dict:
        """Build a customer persona."""
        # Base persona attributes by income segment
        persona_templates = {
            "affluent": {
                "values": ["quality", "convenience", "experience", "premium service"],
                "price_sensitivity": "low",
                "decision_factors": ["quality", "reputation", "ambiance"],
            },
            "upper_middle": {
                "values": ["quality", "value", "convenience"],
                "price_sensitivity": "moderate",
                "decision_factors": ["quality", "value", "reviews"],
            },
            "middle": {
                "values": ["value", "convenience", "reliability"],
                "price_sensitivity": "moderate",
                "decision_factors": ["price", "quality", "convenience"],
            },
            "lower_middle": {
                "values": ["affordability", "reliability", "family-friendly"],
                "price_sensitivity": "high",
                "decision_factors": ["price", "portions", "convenience"],
            },
            "budget_conscious": {
                "values": ["affordability", "value deals", "accessibility"],
                "price_sensitivity": "very high",
                "decision_factors": ["price", "deals", "location"],
            },
        }

        template = persona_templates.get(income_segment, persona_templates["middle"])

        # Age-based adjustments
        if "18-34" in dominant_age or "young" in dominant_age.lower():
            template["preferences"] = ["social media presence", "Instagram-worthy", "trendy"]
            template["channels"] = ["Instagram", "TikTok", "Google Maps"]
        elif "35-54" in dominant_age:
            template["preferences"] = ["reliability", "family-friendly", "convenience"]
            template["channels"] = ["Google", "Facebook", "Yelp"]
        else:
            template["preferences"] = ["quality", "service", "familiarity"]
            template["channels"] = ["Google", "word of mouth", "local news"]

        return {
            "name": f"Typical {business_type.title()} Customer",
            "income_segment": income_segment,
            "age_group": dominant_age,
            **template,
        }

    def _get_targeting_recommendations(
        self,
        persona: dict,
        income_segment: str,
        business_type: str,
    ) -> list[dict]:
        """Generate targeting recommendations based on persona."""
        recommendations = []

        # Channel recommendations
        channels = persona.get("channels", [])
        if channels:
            recommendations.append({
                "area": "Marketing Channels",
                "recommendation": f"Focus on {', '.join(channels[:2])} for reaching target customers",
                "priority": "high",
            })

        # Messaging recommendations
        values = persona.get("values", [])
        if values:
            recommendations.append({
                "area": "Messaging",
                "recommendation": f"Emphasize {', '.join(values[:2])} in marketing materials",
                "priority": "high",
            })

        # Pricing recommendations
        price_sensitivity = persona.get("price_sensitivity", "moderate")
        if price_sensitivity in ["high", "very high"]:
            recommendations.append({
                "area": "Pricing Strategy",
                "recommendation": "Consider value bundles, loyalty discounts, or happy hour specials",
                "priority": "high",
            })
        elif price_sensitivity == "low":
            recommendations.append({
                "area": "Pricing Strategy",
                "recommendation": "Focus on premium experience; price is less of a barrier",
                "priority": "medium",
            })

        return recommendations


# Singleton instance
_service: ConsumerAnalysisService | None = None


def get_consumer_analysis_service() -> ConsumerAnalysisService:
    """Get or create the consumer analysis service singleton."""
    global _service
    if _service is None:
        _service = ConsumerAnalysisService()
    return _service
