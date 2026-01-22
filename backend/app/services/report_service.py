"""Report Service - Aggregation, executive summaries, and recommendations."""

from datetime import datetime
from typing import Any
from ..core.logging import get_logger

logger = get_logger("service.report")


class ReportService:
    """Service for report generation, aggregation, and recommendations."""

    def __init__(self):
        self._llm_service = None

    @property
    def llm_service(self):
        """Lazy load LLM service."""
        if self._llm_service is None:
            from ..core.llm import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    def aggregate_report_data(self, analysis_results: dict) -> dict[str, Any]:
        """
        Aggregate analysis results into structured report sections.

        Args:
            analysis_results: Dictionary containing various analysis outputs

        Returns:
            Structured report with sections and metadata
        """
        logger.info("Aggregating report data")

        # Extract metadata
        location = analysis_results.get("location") or analysis_results.get("address", "Unknown location")
        business_type = analysis_results.get("business_type", "Unknown business")

        # Build report sections
        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "location": location,
                "business_type": business_type,
            },
            "sections": {},
        }

        # Summary section (viability scores, key metrics)
        report["sections"]["summary"] = self._build_summary_section(analysis_results)

        # Market Size section (TAM/SAM/SOM)
        if market_size := self._extract_market_size(analysis_results):
            report["sections"]["market_size"] = market_size

        # Competition section
        if competition := self._extract_competition(analysis_results):
            report["sections"]["competition"] = competition

        # Consumer Insights section
        if consumer := self._extract_consumer_insights(analysis_results):
            report["sections"]["consumer_insights"] = consumer

        # Financials section
        if financials := self._extract_financials(analysis_results):
            report["sections"]["financials"] = financials

        # Economic context
        if economic := self._extract_economic(analysis_results):
            report["sections"]["economic"] = economic

        return report

    def _build_summary_section(self, data: dict) -> dict:
        """Build the summary section from analysis data."""
        summary = {
            "viability_score": None,
            "viability_level": None,
            "key_metrics": {},
        }

        # Extract viability from various sources
        if viability := data.get("viability"):
            summary["viability_score"] = viability.get("score") or viability.get("viability_score")
            summary["viability_level"] = viability.get("level") or viability.get("viability_level")
        elif financial := data.get("financial_summary"):
            if v := financial.get("viability"):
                summary["viability_score"] = v.get("score")
                summary["viability_level"] = v.get("level")

        # Extract key metrics
        if market := data.get("market_size"):
            summary["key_metrics"]["tam"] = market.get("tam", {}).get("value")
            summary["key_metrics"]["sam"] = market.get("sam", {}).get("value")
            summary["key_metrics"]["som"] = market.get("som", {}).get("value")

        if financial := data.get("financial_summary"):
            if scenarios := financial.get("revenue_scenarios"):
                summary["key_metrics"]["projected_revenue"] = scenarios.get("moderate", {}).get("annual_revenue")
            if be := financial.get("break_even"):
                summary["key_metrics"]["months_to_break_even"] = be.get("months_to_recover_startup")

        return summary

    def _extract_market_size(self, data: dict) -> dict | None:
        """Extract market size data."""
        if market := data.get("market_size"):
            return {
                "tam": market.get("tam"),
                "sam": market.get("sam"),
                "som": market.get("som"),
                "methodology": market.get("methodology"),
                "confidence": market.get("confidence"),
            }
        return None

    def _extract_competition(self, data: dict) -> dict | None:
        """Extract competition analysis data."""
        competition = {}

        if competitors := data.get("competitors"):
            competition["competitor_count"] = len(competitors) if isinstance(competitors, list) else competitors.get("total_found", 0)
            competition["top_competitors"] = competitors[:5] if isinstance(competitors, list) else competitors.get("competitors", [])[:5]

        if swot := data.get("swot"):
            competition["swot"] = {
                "strengths": swot.get("strengths", [])[:3],
                "weaknesses": swot.get("weaknesses", [])[:3],
                "opportunities": swot.get("opportunities", [])[:3],
                "threats": swot.get("threats", [])[:3],
            }

        if five_forces := data.get("five_forces"):
            competition["five_forces"] = five_forces.get("forces")

        if pricing := data.get("pricing"):
            competition["pricing_landscape"] = {
                "dominant_tier": pricing.get("dominant_tier"),
                "distribution": pricing.get("distribution"),
            }

        return competition if competition else None

    def _extract_consumer_insights(self, data: dict) -> dict | None:
        """Extract consumer insights data."""
        consumer = {}

        if sentiment := data.get("sentiment"):
            consumer["sentiment"] = {
                "overall": sentiment.get("overall_sentiment"),
                "label": sentiment.get("sentiment_label"),
            }

        if pain_points := data.get("pain_points"):
            consumer["top_pain_points"] = pain_points.get("pain_points", [])[:5]
            consumer["opportunities"] = pain_points.get("opportunities", [])[:3]

        if profile := data.get("consumer_profile"):
            consumer["target_persona"] = profile.get("primary_persona")

        return consumer if consumer else None

    def _extract_financials(self, data: dict) -> dict | None:
        """Extract financial projections data."""
        if financial := data.get("financial_summary"):
            return {
                "revenue_scenarios": financial.get("revenue_scenarios"),
                "break_even": financial.get("break_even"),
                "viability": financial.get("viability"),
                "industry_benchmarks": financial.get("industry_benchmarks"),
            }
        return None

    def _extract_economic(self, data: dict) -> dict | None:
        """Extract economic context data."""
        if economic := data.get("economic"):
            return {
                "outlook": economic.get("outlook"),
                "key_indicators": economic.get("indicators"),
            }
        return None

    async def generate_executive_summary(self, report_data: dict) -> dict[str, Any]:
        """
        Generate LLM-powered executive summary.

        Args:
            report_data: Aggregated report data from aggregate_report_data()

        Returns:
            Executive summary with paragraphs, key findings, and recommendation
        """
        logger.info("Generating executive summary")

        metadata = report_data.get("metadata", {})
        sections = report_data.get("sections", {})

        # Build context for LLM
        context = self._build_summary_context(metadata, sections)

        # Generate summary using LLM
        prompt = f"""Based on the following market research data, generate an executive summary for a potential {metadata.get('business_type', 'business')} in {metadata.get('location', 'the target location')}.

{context}

Provide your response in the following JSON format:
{{
    "summary_paragraphs": ["paragraph 1", "paragraph 2", "paragraph 3"],
    "key_findings": ["finding 1", "finding 2", "finding 3", "finding 4", "finding 5"],
    "recommendation": {{
        "verdict": "favorable" or "neutral" or "challenging",
        "rationale": "brief explanation of recommendation"
    }}
}}

Guidelines:
- Summary should be 2-3 concise paragraphs covering market opportunity, competitive landscape, and financial outlook
- Key findings should be 5-7 actionable bullets
- Verdict should be "favorable" if viability score >= 65, "neutral" if 45-64, "challenging" if < 45
- Be specific and data-driven in your analysis"""

        try:
            response = await self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a market research analyst. Respond only with valid JSON.",
            )

            # Parse response
            import json
            result = json.loads(response.strip())

            return {
                "summary_paragraphs": result.get("summary_paragraphs", []),
                "key_findings": result.get("key_findings", []),
                "recommendation": result.get("recommendation", {
                    "verdict": self._determine_verdict(sections),
                    "rationale": "Based on available analysis data",
                }),
                "metadata": metadata,
            }

        except Exception as e:
            logger.warning("LLM summary generation failed, using fallback", error=str(e))
            return self._generate_fallback_summary(metadata, sections)

    def _build_summary_context(self, metadata: dict, sections: dict) -> str:
        """Build context string for LLM summary generation."""
        context_parts = []

        context_parts.append(f"Location: {metadata.get('location')}")
        context_parts.append(f"Business Type: {metadata.get('business_type')}")

        if summary := sections.get("summary"):
            if score := summary.get("viability_score"):
                context_parts.append(f"Viability Score: {score}/100 ({summary.get('viability_level', 'N/A')})")
            if metrics := summary.get("key_metrics"):
                if tam := metrics.get("tam"):
                    context_parts.append(f"Total Addressable Market: ${tam:,.0f}")
                if som := metrics.get("som"):
                    context_parts.append(f"Serviceable Obtainable Market: ${som:,.0f}")
                if revenue := metrics.get("projected_revenue"):
                    context_parts.append(f"Projected Annual Revenue: ${revenue:,.0f}")
                if months := metrics.get("months_to_break_even"):
                    context_parts.append(f"Months to Break-Even: {months}")

        if competition := sections.get("competition"):
            context_parts.append(f"Competitor Count: {competition.get('competitor_count', 'N/A')}")
            if swot := competition.get("swot"):
                context_parts.append(f"Key Strengths: {', '.join(s.get('factor', s) if isinstance(s, dict) else s for s in swot.get('strengths', []))}")
                context_parts.append(f"Key Threats: {', '.join(t.get('factor', t) if isinstance(t, dict) else t for t in swot.get('threats', []))}")

        if consumer := sections.get("consumer_insights"):
            if sentiment := consumer.get("sentiment"):
                context_parts.append(f"Customer Sentiment: {sentiment.get('label', 'N/A')}")
            if pain_points := consumer.get("top_pain_points"):
                issues = [p.get("issue", p) if isinstance(p, dict) else p for p in pain_points[:3]]
                context_parts.append(f"Top Customer Pain Points: {', '.join(issues)}")

        if financials := sections.get("financials"):
            if benchmarks := financials.get("industry_benchmarks"):
                context_parts.append(f"Industry Avg Revenue: ${benchmarks.get('avg_revenue', 0):,.0f}")

        return "\n".join(context_parts)

    def _determine_verdict(self, sections: dict) -> str:
        """Determine recommendation verdict from scores."""
        summary = sections.get("summary", {})
        score = summary.get("viability_score")
        if score is None:
            return "neutral"
        if score >= 65:
            return "favorable"
        if score >= 45:
            return "neutral"
        return "challenging"

    def _generate_fallback_summary(self, metadata: dict, sections: dict) -> dict:
        """Generate fallback summary when LLM fails."""
        summary_section = sections.get("summary", {})
        viability = summary_section.get("viability_score")
        level = summary_section.get("viability_level", "moderate")

        paragraphs = [
            f"This market research analysis evaluates the opportunity for a {metadata.get('business_type', 'business')} in {metadata.get('location', 'the target location')}.",
        ]

        if viability:
            paragraphs.append(f"The overall market viability score is {viability}/100, indicating a {level} opportunity.")

        findings = []
        if metrics := summary_section.get("key_metrics"):
            if tam := metrics.get("tam"):
                findings.append(f"Total Addressable Market is ${tam:,.0f}")
            if revenue := metrics.get("projected_revenue"):
                findings.append(f"Projected annual revenue is ${revenue:,.0f}")
            if months := metrics.get("months_to_break_even"):
                findings.append(f"Expected break-even timeline is {months} months")

        return {
            "summary_paragraphs": paragraphs,
            "key_findings": findings or ["Analysis data limited - additional research recommended"],
            "recommendation": {
                "verdict": self._determine_verdict(sections),
                "rationale": f"Based on viability assessment: {level}",
            },
            "metadata": metadata,
        }

    async def generate_recommendations(self, report_data: dict) -> list[dict[str, Any]]:
        """
        Generate prioritized recommendations from analysis.

        Args:
            report_data: Aggregated report data

        Returns:
            List of recommendations with title, description, rationale, priority, category
        """
        logger.info("Generating recommendations")

        sections = report_data.get("sections", {})
        metadata = report_data.get("metadata", {})

        # Build context
        context = self._build_summary_context(metadata, sections)

        prompt = f"""Based on the following market research data, generate actionable recommendations for opening a {metadata.get('business_type', 'business')} in {metadata.get('location', 'the target location')}.

{context}

Provide exactly 6-8 recommendations in the following JSON format:
{{
    "recommendations": [
        {{
            "title": "Brief recommendation title",
            "description": "Detailed description of what to do",
            "rationale": "Why this is important based on the data",
            "priority": "high" or "medium" or "low",
            "category": "immediate_actions" or "strategic_considerations" or "risk_mitigations"
        }}
    ]
}}

Guidelines:
- Include 2-3 immediate_actions (things to do in first 30 days)
- Include 2-3 strategic_considerations (longer-term planning items)
- Include 2 risk_mitigations (ways to address identified risks)
- Priorities: high = critical for success, medium = important, low = nice to have
- Be specific and actionable"""

        try:
            response = await self.llm_service.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a business strategy consultant. Respond only with valid JSON.",
            )

            import json
            result = json.loads(response.strip())
            return result.get("recommendations", [])

        except Exception as e:
            logger.warning("LLM recommendation generation failed, using fallback", error=str(e))
            return self._generate_fallback_recommendations(sections, metadata)

    def _generate_fallback_recommendations(self, sections: dict, metadata: dict) -> list[dict]:
        """Generate fallback recommendations when LLM fails."""
        recommendations = []

        # Immediate actions
        recommendations.append({
            "title": "Conduct site visits",
            "description": f"Visit the proposed location and observe foot traffic, parking, and customer flow at different times",
            "rationale": "Direct observation validates data-driven analysis",
            "priority": "high",
            "category": "immediate_actions",
        })

        recommendations.append({
            "title": "Analyze competitor pricing",
            "description": "Document competitor prices, menus, and service offerings in detail",
            "rationale": "Informs pricing strategy and differentiation opportunities",
            "priority": "high",
            "category": "immediate_actions",
        })

        # Strategic considerations
        if competition := sections.get("competition"):
            if competition.get("competitor_count", 0) > 10:
                recommendations.append({
                    "title": "Develop differentiation strategy",
                    "description": "Create clear positioning to stand out in a competitive market",
                    "rationale": f"High competition ({competition.get('competitor_count')} competitors) requires unique value proposition",
                    "priority": "high",
                    "category": "strategic_considerations",
                })

        recommendations.append({
            "title": "Build marketing launch plan",
            "description": "Develop pre-launch buzz and grand opening strategy",
            "rationale": "Strong launch builds initial customer base critical for break-even",
            "priority": "medium",
            "category": "strategic_considerations",
        })

        # Risk mitigations
        summary = sections.get("summary", {})
        if months := summary.get("key_metrics", {}).get("months_to_break_even"):
            if months and months > 18:
                recommendations.append({
                    "title": "Secure adequate funding runway",
                    "description": f"Ensure funding covers at least {months + 6} months of operations",
                    "rationale": f"Break-even timeline of {months} months requires financial buffer",
                    "priority": "high",
                    "category": "risk_mitigations",
                })

        recommendations.append({
            "title": "Develop contingency plans",
            "description": "Create backup plans for slow start scenarios including cost reduction options",
            "rationale": "Market conditions may vary from projections",
            "priority": "medium",
            "category": "risk_mitigations",
        })

        return recommendations


# Singleton instance
_service: ReportService | None = None


def get_report_service() -> ReportService:
    """Get or create the report service singleton."""
    global _service
    if _service is None:
        _service = ReportService()
    return _service
