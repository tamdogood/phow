"""Financial Analysis Service - Revenue projections, break-even, scenarios, viability."""

import json
from pathlib import Path
from typing import Any
from ..core.logging import get_logger

logger = get_logger("service.financial_analysis")


class FinancialAnalysisService:
    """Service for financial projections and scenario modeling."""

    def __init__(self):
        self._benchmarks = None
        self._naics_service = None

    @property
    def benchmarks(self) -> dict:
        """Lazy load industry benchmarks."""
        if self._benchmarks is None:
            benchmarks_path = Path(__file__).parent.parent / "tools" / "market_research" / "data" / "industry_benchmarks.json"
            with open(benchmarks_path) as f:
                self._benchmarks = json.load(f)
        return self._benchmarks

    @property
    def naics_service(self):
        """Lazy load NAICS service."""
        if self._naics_service is None:
            from ..tools.market_research.naics_service import get_naics_service
            self._naics_service = get_naics_service()
        return self._naics_service

    def get_industry_benchmark(self, naics_code: str) -> dict:
        """Get benchmark data for an industry."""
        benchmarks = self.benchmarks.get("benchmarks", {})
        return benchmarks.get(naics_code, self.benchmarks.get("default", {}))

    def project_revenue(
        self,
        business_type: str,
        location: dict,
        market_data: dict,
        scenario: str = "moderate",
    ) -> dict[str, Any]:
        """
        Project revenue for a business.

        Args:
            business_type: Type of business
            location: Location info
            market_data: Market data including demographics, competition
            scenario: "conservative", "moderate", or "optimistic"

        Returns:
            Revenue projection with methodology
        """
        logger.info("Projecting revenue", business_type=business_type, scenario=scenario)

        # Get NAICS code and benchmarks
        codes = self.naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "default"
        benchmark = self.get_industry_benchmark(naics_code)

        # Get market factors
        som = market_data.get("som", {}).get("value", 0)
        population = market_data.get("demographics", {}).get("total_population", 50000)
        median_income = market_data.get("demographics", {}).get("median_income", 60000)
        competition = len(market_data.get("competitors", []))

        # Calculate scenario multipliers
        scenario_multipliers = {
            "conservative": 0.7,
            "moderate": 1.0,
            "optimistic": 1.3,
        }
        multiplier = scenario_multipliers.get(scenario, 1.0)

        # Calculate revenue projection
        avg_ticket = benchmark.get("avg_ticket", 30)
        transactions = benchmark.get("transactions_per_day", {})

        # Adjust transactions based on scenario
        if scenario == "conservative":
            daily_transactions = transactions.get("low", 50)
        elif scenario == "optimistic":
            daily_transactions = transactions.get("high", 200)
        else:
            daily_transactions = transactions.get("median", 100)

        # Adjust for market factors
        income_factor = min(1.3, max(0.7, median_income / 60000))
        competition_factor = max(0.6, 1 - (competition * 0.03))  # Each competitor reduces by 3%
        population_factor = min(1.2, max(0.8, population / 50000))

        adjusted_transactions = int(daily_transactions * income_factor * competition_factor * population_factor)

        # Calculate projections
        daily_revenue = adjusted_transactions * avg_ticket
        monthly_revenue = daily_revenue * 26  # Assume 26 operating days
        annual_revenue = monthly_revenue * 12

        # Apply seasonal adjustment (average)
        annual_revenue = int(annual_revenue * multiplier)
        monthly_revenue = int(annual_revenue / 12)

        return {
            "scenario": scenario,
            "business_type": business_type,
            "naics_code": naics_code,
            "projections": {
                "daily_revenue": int(daily_revenue * multiplier),
                "monthly_revenue": monthly_revenue,
                "annual_revenue": annual_revenue,
            },
            "assumptions": {
                "avg_ticket": avg_ticket,
                "daily_transactions": adjusted_transactions,
                "operating_days_per_month": 26,
                "income_factor": round(income_factor, 2),
                "competition_factor": round(competition_factor, 2),
            },
            "benchmark_comparison": {
                "industry_avg": benchmark.get("avg_revenue_per_location", 500000),
                "industry_range": benchmark.get("revenue_range", {}),
                "vs_industry_avg": round((annual_revenue / benchmark.get("avg_revenue_per_location", 500000)) * 100, 1),
            },
            "confidence": self._calculate_projection_confidence(market_data),
        }

    def calculate_break_even(
        self,
        business_type: str,
        revenue_projection: dict | None = None,
        fixed_costs: float | None = None,
        variable_cost_percent: float | None = None,
    ) -> dict[str, Any]:
        """
        Calculate break-even point.

        Args:
            business_type: Type of business
            revenue_projection: Revenue projection (or will use benchmark)
            fixed_costs: Monthly fixed costs (or will use benchmark)
            variable_cost_percent: Variable cost as % of revenue (or will use benchmark)

        Returns:
            Break-even analysis
        """
        logger.info("Calculating break-even", business_type=business_type)

        # Get benchmarks
        codes = self.naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "default"
        benchmark = self.get_industry_benchmark(naics_code)

        cost_structure = benchmark.get("cost_structure", {})

        # Use provided values or benchmarks
        if variable_cost_percent is None:
            variable_cost_percent = cost_structure.get("cogs_percent", 30)

        if fixed_costs is None:
            # Estimate fixed costs from benchmark
            avg_revenue = benchmark.get("avg_revenue_per_location", 500000)
            monthly_revenue = avg_revenue / 12
            fixed_cost_percent = (
                cost_structure.get("labor_percent", 30)
                + cost_structure.get("rent_percent", 10)
                + cost_structure.get("utilities_percent", 3)
                + cost_structure.get("other_percent", 10)
            )
            fixed_costs = monthly_revenue * (fixed_cost_percent / 100)

        # Get monthly revenue
        if revenue_projection:
            monthly_revenue = revenue_projection.get("projections", {}).get("monthly_revenue", 50000)
        else:
            monthly_revenue = benchmark.get("avg_revenue_per_location", 500000) / 12

        # Calculate contribution margin
        contribution_margin_percent = 100 - variable_cost_percent

        # Break-even revenue
        break_even_revenue = (fixed_costs * 100) / contribution_margin_percent

        # Break-even units (transactions)
        avg_ticket = benchmark.get("avg_ticket", 30)
        break_even_units = int(break_even_revenue / avg_ticket)

        # Months to break even (startup recovery)
        startup_costs = benchmark.get("startup_costs", {}).get("median", 200000)
        monthly_profit = monthly_revenue * (contribution_margin_percent / 100) - fixed_costs

        if monthly_profit > 0:
            months_to_recover = int(startup_costs / monthly_profit)
        else:
            months_to_recover = None  # Not profitable

        # Benchmark comparison
        benchmark_months = benchmark.get("break_even_months", {})

        return {
            "business_type": business_type,
            "break_even_revenue": {
                "monthly": int(break_even_revenue),
                "annual": int(break_even_revenue * 12),
            },
            "break_even_units": {
                "monthly": break_even_units,
                "daily": int(break_even_units / 26),
            },
            "startup_recovery": {
                "startup_costs": int(startup_costs),
                "monthly_profit": int(monthly_profit) if monthly_profit else 0,
                "months_to_recover": months_to_recover,
            },
            "cost_structure": {
                "fixed_costs_monthly": int(fixed_costs),
                "variable_cost_percent": variable_cost_percent,
                "contribution_margin_percent": contribution_margin_percent,
            },
            "benchmark_comparison": {
                "industry_months": benchmark_months,
                "assessment": self._assess_break_even(months_to_recover, benchmark_months),
            },
        }

    def _assess_break_even(self, months: int | None, benchmark: dict) -> str:
        """Assess break-even timeline vs benchmark."""
        if months is None:
            return "challenging - projected costs exceed revenue"

        optimistic = benchmark.get("optimistic", 12)
        realistic = benchmark.get("realistic", 18)
        conservative = benchmark.get("conservative", 24)

        if months <= optimistic:
            return "excellent - faster than industry optimistic estimate"
        elif months <= realistic:
            return "good - within typical industry range"
        elif months <= conservative:
            return "acceptable - longer but within conservative estimate"
        else:
            return "concerning - slower than industry conservative estimate"

    def run_scenario(
        self,
        base_analysis: dict,
        modifications: dict,
    ) -> dict[str, Any]:
        """
        Run what-if scenario analysis.

        Args:
            base_analysis: Base financial analysis
            modifications: Scenario modifications (e.g., {"price_change": 10, "cost_reduction": 5})

        Returns:
            Scenario comparison with impact analysis
        """
        logger.info("Running scenario analysis", modifications=modifications)

        base_revenue = base_analysis.get("projections", {}).get("annual_revenue", 500000)
        base_profit_margin = base_analysis.get("profit_margin", 10)

        # Apply modifications
        price_change = modifications.get("price_change", 0)  # Percent
        cost_reduction = modifications.get("cost_reduction", 0)  # Percent
        volume_change = modifications.get("volume_change", 0)  # Percent
        rent_change = modifications.get("rent_change", 0)  # Percent

        # Calculate new revenue
        price_factor = 1 + (price_change / 100)
        volume_factor = 1 + (volume_change / 100)
        new_revenue = base_revenue * price_factor * volume_factor

        # Adjust profit margin
        margin_adjustment = cost_reduction - rent_change
        new_profit_margin = base_profit_margin + margin_adjustment

        # Calculate profits
        base_profit = base_revenue * (base_profit_margin / 100)
        new_profit = new_revenue * (new_profit_margin / 100)

        return {
            "scenario_name": modifications.get("name", "Custom Scenario"),
            "base_case": {
                "annual_revenue": base_revenue,
                "profit_margin": base_profit_margin,
                "annual_profit": int(base_profit),
            },
            "scenario_case": {
                "annual_revenue": int(new_revenue),
                "profit_margin": round(new_profit_margin, 1),
                "annual_profit": int(new_profit),
            },
            "impact": {
                "revenue_change": int(new_revenue - base_revenue),
                "revenue_change_percent": round(((new_revenue / base_revenue) - 1) * 100, 1),
                "profit_change": int(new_profit - base_profit),
                "profit_change_percent": round(((new_profit / base_profit) - 1) * 100, 1) if base_profit > 0 else 0,
            },
            "modifications_applied": modifications,
        }

    def calculate_financial_viability(
        self,
        business_type: str,
        revenue_projection: dict,
        market_data: dict,
    ) -> dict[str, Any]:
        """
        Calculate overall financial viability score.

        Args:
            business_type: Type of business
            revenue_projection: Revenue projection
            market_data: Market data

        Returns:
            Viability score with breakdown
        """
        logger.info("Calculating financial viability", business_type=business_type)

        # Get benchmarks
        codes = self.naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "default"
        benchmark = self.get_industry_benchmark(naics_code)

        # Calculate sub-scores
        scores = {}

        # Revenue potential (vs benchmark)
        projected_revenue = revenue_projection.get("projections", {}).get("annual_revenue", 0)
        benchmark_revenue = benchmark.get("avg_revenue_per_location", 500000)
        revenue_ratio = projected_revenue / benchmark_revenue
        scores["revenue_potential"] = min(100, int(revenue_ratio * 80))

        # Margin expectations
        profit_margins = benchmark.get("profit_margin", {})
        expected_margin = profit_margins.get("median", 10)
        scores["margin_expectations"] = min(100, int(expected_margin * 5))

        # Break-even timeline
        break_even = self.calculate_break_even(business_type, revenue_projection)
        months = break_even.get("startup_recovery", {}).get("months_to_recover")
        if months:
            scores["break_even_timeline"] = max(0, 100 - (months * 3))
        else:
            scores["break_even_timeline"] = 20

        # Market growth
        trends = market_data.get("trends", {})
        trend_direction = trends.get("trend_direction", "stable")
        trend_scores = {"strongly_growing": 90, "growing": 75, "stable": 50, "declining": 25}
        scores["market_growth"] = trend_scores.get(trend_direction, 50)

        # Competition impact
        competition = len(market_data.get("competitors", []))
        scores["competition_impact"] = max(30, 100 - (competition * 5))

        # Calculate overall score (weighted)
        weights = {
            "revenue_potential": 0.25,
            "margin_expectations": 0.20,
            "break_even_timeline": 0.25,
            "market_growth": 0.15,
            "competition_impact": 0.15,
        }

        overall_score = sum(scores[k] * weights[k] for k in weights)

        # Determine level
        if overall_score >= 70:
            level = "strong"
            recommendation = "Financial projections support business viability. Proceed with confidence."
        elif overall_score >= 50:
            level = "moderate"
            recommendation = "Viable with proper execution. Focus on operational efficiency."
        else:
            level = "challenging"
            recommendation = "Financial challenges present. Consider cost reduction or differentiation."

        return {
            "business_type": business_type,
            "viability_score": int(overall_score),
            "viability_level": level,
            "score_breakdown": scores,
            "weights": weights,
            "recommendation": recommendation,
            "risk_factors": self._identify_risk_factors(scores, break_even),
            "key_metrics": {
                "projected_annual_revenue": projected_revenue,
                "expected_profit_margin": f"{expected_margin}%",
                "months_to_break_even": months,
                "startup_costs": break_even.get("startup_recovery", {}).get("startup_costs"),
            },
        }

    def _calculate_projection_confidence(self, market_data: dict) -> dict:
        """Calculate confidence level for projections."""
        data_points = 0
        max_points = 5

        if market_data.get("demographics"):
            data_points += 1
        if market_data.get("competitors"):
            data_points += 1
        if market_data.get("som"):
            data_points += 1
        if market_data.get("trends"):
            data_points += 1
        if market_data.get("economic"):
            data_points += 1

        confidence = data_points / max_points

        if confidence >= 0.8:
            level = "high"
        elif confidence >= 0.5:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": round(confidence, 2),
            "data_points_available": data_points,
        }

    def _identify_risk_factors(self, scores: dict, break_even: dict) -> list[dict]:
        """Identify key risk factors from analysis."""
        risks = []

        if scores.get("revenue_potential", 0) < 50:
            risks.append({
                "factor": "Revenue potential",
                "severity": "high",
                "description": "Projected revenue below industry average",
            })

        if scores.get("break_even_timeline", 0) < 50:
            risks.append({
                "factor": "Break-even timeline",
                "severity": "medium",
                "description": "Longer than typical break-even period",
            })

        if scores.get("competition_impact", 0) < 50:
            risks.append({
                "factor": "Competition",
                "severity": "medium",
                "description": "High competition may impact market share",
            })

        if scores.get("market_growth", 0) < 40:
            risks.append({
                "factor": "Market growth",
                "severity": "medium",
                "description": "Industry showing slow or negative growth",
            })

        return risks if risks else [{"factor": "None significant", "severity": "low", "description": "No major risk factors identified"}]

    def get_financial_summary(
        self,
        business_type: str,
        location: dict,
        market_data: dict,
    ) -> dict[str, Any]:
        """
        Get comprehensive financial summary.

        Args:
            business_type: Type of business
            location: Location info
            market_data: Market data

        Returns:
            Comprehensive financial analysis
        """
        logger.info("Generating financial summary", business_type=business_type)

        # Run all scenarios
        conservative = self.project_revenue(business_type, location, market_data, "conservative")
        moderate = self.project_revenue(business_type, location, market_data, "moderate")
        optimistic = self.project_revenue(business_type, location, market_data, "optimistic")

        # Calculate break-even
        break_even = self.calculate_break_even(business_type, moderate)

        # Calculate viability
        viability = self.calculate_financial_viability(business_type, moderate, market_data)

        # Get benchmarks
        codes = self.naics_service.map_business_type(business_type)
        naics_code = codes[0] if codes else "default"
        benchmark = self.get_industry_benchmark(naics_code)

        return {
            "business_type": business_type,
            "location": location.get("address") if isinstance(location, dict) else str(location),
            "naics_code": naics_code,
            "revenue_scenarios": {
                "conservative": conservative["projections"],
                "moderate": moderate["projections"],
                "optimistic": optimistic["projections"],
            },
            "break_even": {
                "monthly_revenue_needed": break_even["break_even_revenue"]["monthly"],
                "transactions_needed_daily": break_even["break_even_units"]["daily"],
                "months_to_recover_startup": break_even["startup_recovery"]["months_to_recover"],
            },
            "viability": {
                "score": viability["viability_score"],
                "level": viability["viability_level"],
                "recommendation": viability["recommendation"],
            },
            "industry_benchmarks": {
                "avg_revenue": benchmark.get("avg_revenue_per_location"),
                "profit_margin_range": benchmark.get("profit_margin"),
                "startup_costs": benchmark.get("startup_costs"),
            },
            "key_insights": self._generate_financial_insights(
                moderate, break_even, viability, benchmark
            ),
        }

    def _generate_financial_insights(
        self,
        projection: dict,
        break_even: dict,
        viability: dict,
        benchmark: dict,
    ) -> list[str]:
        """Generate key financial insights."""
        insights = []

        # Revenue insight
        projected = projection.get("projections", {}).get("annual_revenue", 0)
        industry_avg = benchmark.get("avg_revenue_per_location", 500000)
        if projected >= industry_avg:
            insights.append(f"Projected revenue (${projected:,}) meets or exceeds industry average")
        else:
            insights.append(f"Projected revenue below industry average - consider differentiation")

        # Break-even insight
        months = break_even.get("startup_recovery", {}).get("months_to_recover")
        if months:
            if months <= 12:
                insights.append(f"Fast break-even timeline ({months} months) reduces risk")
            elif months <= 24:
                insights.append(f"Typical break-even timeline ({months} months)")
            else:
                insights.append(f"Extended break-even timeline ({months} months) - ensure adequate funding")

        # Viability insight
        score = viability.get("viability_score", 50)
        if score >= 70:
            insights.append("Strong financial viability - favorable conditions for success")
        elif score >= 50:
            insights.append("Moderate viability - focus on execution and cost management")
        else:
            insights.append("Financial challenges present - consider alternative approaches")

        return insights


# Singleton instance
_service: FinancialAnalysisService | None = None


def get_financial_analysis_service() -> FinancialAnalysisService:
    """Get or create the financial analysis service singleton."""
    global _service
    if _service is None:
        _service = FinancialAnalysisService()
    return _service
