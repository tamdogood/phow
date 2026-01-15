"""LangChain tools for the Review Responder agent."""

import json
from langchain_core.tools import tool

from ...core.logging import get_logger

logger = get_logger("review_responder.tools")


@tool
def analyze_review_sentiment(review_text: str, review_rating: int | None = None) -> str:
    """Analyze the sentiment and extract key issues from a customer review.

    Args:
        review_text: The full text of the customer review
        review_rating: Optional star rating (1-5) if available

    Returns:
        Analysis including sentiment, key issues, and emotional tone
    """
    logger.info("Analyzing review sentiment", text_length=len(review_text), rating=review_rating)

    # Determine sentiment based on keywords and rating
    text_lower = review_text.lower()

    # Negative indicators
    negative_keywords = [
        "disappointed",
        "terrible",
        "awful",
        "worst",
        "horrible",
        "never again",
        "rude",
        "slow",
        "cold",
        "dirty",
        "overpriced",
        "waste",
        "disgusting",
        "unacceptable",
        "frustrated",
        "angry",
        "upset",
        "complained",
        "refund",
        "waited",
        "ignored",
        "wrong order",
        "mistake",
        "bad",
        "poor",
    ]

    # Positive indicators
    positive_keywords = [
        "amazing",
        "excellent",
        "wonderful",
        "fantastic",
        "great",
        "love",
        "delicious",
        "friendly",
        "best",
        "recommend",
        "perfect",
        "outstanding",
        "impressed",
        "return",
        "awesome",
        "favorite",
        "incredible",
        "pleasant",
        "helpful",
        "clean",
        "quick",
        "fresh",
        "quality",
    ]

    negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
    positive_count = sum(1 for kw in positive_keywords if kw in text_lower)

    # Determine sentiment
    if review_rating:
        if review_rating >= 4:
            base_sentiment = "positive"
        elif review_rating <= 2:
            base_sentiment = "negative"
        else:
            base_sentiment = "mixed"
    else:
        if positive_count > negative_count + 2:
            base_sentiment = "positive"
        elif negative_count > positive_count + 2:
            base_sentiment = "negative"
        elif positive_count > 0 and negative_count > 0:
            base_sentiment = "mixed"
        else:
            base_sentiment = "neutral"

    # Extract key issues
    issues = []
    issue_categories = {
        "service_speed": ["slow", "waited", "long wait", "took forever", "delayed"],
        "food_quality": [
            "cold",
            "stale",
            "undercooked",
            "overcooked",
            "bland",
            "tasteless",
            "fresh",
            "delicious",
        ],
        "staff_attitude": [
            "rude",
            "unfriendly",
            "ignored",
            "dismissive",
            "friendly",
            "helpful",
            "attentive",
        ],
        "cleanliness": ["dirty", "unclean", "messy", "clean", "spotless"],
        "pricing": ["overpriced", "expensive", "value", "cheap", "worth it", "reasonable"],
        "order_accuracy": ["wrong order", "mistake", "forgot", "missing", "incorrect"],
        "ambiance": ["loud", "noisy", "cramped", "cozy", "atmosphere", "ambiance", "vibe"],
    }

    for category, keywords in issue_categories.items():
        for kw in keywords:
            if kw in text_lower:
                issues.append(category.replace("_", " ").title())
                break

    issues = list(set(issues))  # Remove duplicates

    # Determine emotional tone
    if any(word in text_lower for word in ["angry", "furious", "outraged", "livid"]):
        emotional_tone = "angry"
    elif any(word in text_lower for word in ["disappointed", "let down", "expected more"]):
        emotional_tone = "disappointed"
    elif any(word in text_lower for word in ["frustrated", "annoyed", "irritated"]):
        emotional_tone = "frustrated"
    elif any(word in text_lower for word in ["love", "amazing", "wonderful", "best"]):
        emotional_tone = "enthusiastic"
    elif any(word in text_lower for word in ["happy", "pleased", "satisfied", "enjoyed"]):
        emotional_tone = "satisfied"
    else:
        emotional_tone = "neutral"

    # Determine review type
    if base_sentiment == "positive" and not issues:
        review_type = "praise"
    elif base_sentiment == "negative" and issues:
        review_type = "complaint"
    elif base_sentiment == "mixed":
        review_type = "constructive_feedback"
    else:
        review_type = "general_feedback"

    return json.dumps(
        {
            "sentiment": base_sentiment,
            "rating": review_rating,
            "key_issues": issues if issues else ["No specific issues identified"],
            "emotional_tone": emotional_tone,
            "review_type": review_type,
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
        }
    )


@tool
def generate_response(
    review_text: str,
    sentiment: str,
    key_issues: list[str],
    tone: str,
    business_name: str = "our team",
) -> str:
    """Generate a response draft for a customer review.

    Args:
        review_text: The original review text
        sentiment: The sentiment analysis result (positive, negative, mixed, neutral)
        key_issues: List of key issues identified in the review
        tone: The desired tone (professional, friendly, apologetic)
        business_name: Name of the business for personalization

    Returns:
        A crafted response appropriate for the review and tone
    """
    logger.info("Generating response", sentiment=sentiment, tone=tone, issues=key_issues)

    # This provides structured context for the LLM to generate the actual response
    # The LLM will use this data to craft appropriate responses

    response_guidelines = {
        "professional": {
            "opening": "Thank you for taking the time to share your feedback.",
            "style": "formal, business-focused, solution-oriented",
            "focus": "Address issues directly, maintain professionalism",
        },
        "friendly": {
            "opening": "Thanks so much for your review!",
            "style": "warm, personal, conversational",
            "focus": "Build relationship, show personality",
        },
        "apologetic": {
            "opening": "We sincerely apologize for your experience.",
            "style": "remorseful, empathetic, resolution-focused",
            "focus": "Take responsibility, offer to make it right",
        },
    }

    guidelines = response_guidelines.get(tone, response_guidelines["professional"])

    return json.dumps(
        {
            "tone": tone,
            "sentiment": sentiment,
            "key_issues": key_issues,
            "guidelines": guidelines,
            "business_name": business_name,
            "instructions": f"""Generate a {tone} response for this {sentiment} review.

Review: "{review_text[:500]}"

Key issues to address: {', '.join(key_issues)}

Guidelines:
- Opening style: {guidelines['opening']}
- Tone: {guidelines['style']}
- Focus: {guidelines['focus']}
- Keep response to 2-4 sentences
- Sign off with "{business_name}"

Generate a natural, human response that addresses the specific feedback.""",
        }
    )


@tool
def get_response_templates(scenario: str) -> str:
    """Get response templates for common review scenarios.

    Args:
        scenario: The type of scenario (positive_review, negative_review, service_complaint,
                  food_complaint, wait_time_complaint, staff_complaint, mixed_review)

    Returns:
        Response templates for the given scenario
    """
    logger.info("Getting response templates", scenario=scenario)

    templates = {
        "positive_review": {
            "professional": "Thank you for your kind words and for choosing {business}. We're delighted to hear you enjoyed your experience. We look forward to serving you again soon.",
            "friendly": "You just made our day! Thank you so much for the wonderful review. We can't wait to see you again! - The {business} Team",
            "tips": [
                "Keep it genuine and brief",
                "Mention specific things they praised",
                "Invite them to return",
            ],
        },
        "negative_review": {
            "professional": "Thank you for bringing this to our attention. We sincerely apologize that your experience did not meet expectations. Please contact us at [email/phone] so we can make this right.",
            "friendly": "We're so sorry to hear this! This isn't the experience we want for our guests. Please reach out to us directly - we'd love the chance to make it up to you.",
            "apologetic": "We deeply apologize for falling short. Your feedback helps us improve. Please contact us at [email/phone] so we can personally address your concerns and make this right.",
            "tips": [
                "Acknowledge their frustration",
                "Take responsibility",
                "Offer to continue conversation privately",
                "Don't be defensive",
            ],
        },
        "service_complaint": {
            "professional": "We apologize for the service issues you experienced. This falls short of our standards. We're addressing this with our team and would appreciate the opportunity to serve you better.",
            "tips": [
                "Acknowledge the specific service failure",
                "Show you're taking action",
                "Don't make excuses",
            ],
        },
        "food_complaint": {
            "professional": "We're sorry to hear the food didn't meet your expectations. Quality is our priority, and we take this feedback seriously. We'd love for you to give us another chance.",
            "tips": [
                "Take the quality concern seriously",
                "Avoid dismissing their experience",
                "Consider offering a replacement or refund",
            ],
        },
        "wait_time_complaint": {
            "professional": "We apologize for the extended wait time. We understand your time is valuable and we're working to improve our efficiency. Thank you for your patience and feedback.",
            "tips": [
                "Acknowledge the inconvenience",
                "Don't make excuses about being busy",
                "Show you value their time",
            ],
        },
        "staff_complaint": {
            "professional": "We're disappointed to hear about your interaction with our staff. This doesn't reflect our values. We're addressing this internally and appreciate you bringing it to our attention.",
            "tips": [
                "Take it seriously",
                "Don't publicly discuss staff discipline",
                "Show it will be addressed",
            ],
        },
        "mixed_review": {
            "professional": "Thank you for your balanced feedback. We're glad you enjoyed [positive aspect] and apologize for [negative aspect]. We're always working to improve and appreciate your insights.",
            "tips": [
                "Acknowledge both the positive and negative",
                "Don't focus only on the negative",
                "Show you're listening to all feedback",
            ],
        },
    }

    template = templates.get(scenario, templates["negative_review"])

    return json.dumps(
        {
            "scenario": scenario,
            "templates": template,
            "general_tips": [
                "Respond within 24-48 hours",
                "Keep responses under 100 words",
                "Personalize when possible",
                "Always thank them for feedback",
                "Proofread before posting",
            ],
        }
    )


# Export all tools for the agent
REVIEW_RESPONDER_TOOLS = [
    analyze_review_sentiment,
    generate_response,
    get_response_templates,
]
