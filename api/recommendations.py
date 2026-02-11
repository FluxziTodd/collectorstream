"""
AI-Powered Card Investment Recommendations
Analyzes price trends, volatility, and momentum to provide buy/hold/sell recommendations
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
import statistics
from datetime import datetime, timedelta
from auth import get_current_user
from database import get_card_by_id, get_market_price_history, get_user_cards

router = APIRouter()

# ============================================================================
# Trend Analysis Functions
# ============================================================================

def calculate_trend(prices: List[float], days: int) -> float:
    """Calculate percentage change over a period."""
    if len(prices) < 2:
        return 0.0

    # Use prices from the specified period
    relevant_prices = prices[-days:] if len(prices) >= days else prices

    if len(relevant_prices) < 2:
        return 0.0

    first_price = relevant_prices[0]
    last_price = relevant_prices[-1]

    if first_price == 0:
        return 0.0

    return ((last_price - first_price) / first_price) * 100


def calculate_volatility(prices: List[float]) -> float:
    """Calculate volatility as coefficient of variation (std dev / mean)."""
    if len(prices) < 2:
        return 0.0

    try:
        mean = statistics.mean(prices)
        if mean == 0:
            return 0.0

        stdev = statistics.stdev(prices)
        return (stdev / mean) * 100
    except statistics.StatisticsError:
        return 0.0


def detect_momentum(prices: List[float]) -> str:
    """Detect momentum: ACCELERATING, DECELERATING, or STEADY."""
    if len(prices) < 3:
        return "STEADY"

    # Split into two halves and compare trends
    mid = len(prices) // 2
    first_half = prices[:mid]
    second_half = prices[mid:]

    if len(first_half) < 2 or len(second_half) < 2:
        return "STEADY"

    trend_first = calculate_trend(first_half, len(first_half))
    trend_second = calculate_trend(second_half, len(second_half))

    difference = abs(trend_second - trend_first)

    if difference < 5:
        return "STEADY"
    elif trend_second > trend_first:
        return "ACCELERATING"
    else:
        return "DECELERATING"


def analyze_card_trends(card: Dict[str, Any], price_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze multiple timeframe trends for a card."""
    if not price_history:
        return {
            "trend_7d": 0.0,
            "trend_30d": 0.0,
            "trend_90d": 0.0,
            "volatility": 0.0,
            "momentum": "STEADY",
            "sample_size": 0
        }

    # Sort by date (oldest first)
    sorted_history = sorted(price_history, key=lambda x: x.get("checked_at", ""))
    prices = [h.get("market_price", 0) for h in sorted_history]

    return {
        "trend_7d": calculate_trend(prices, 7),
        "trend_30d": calculate_trend(prices, 30),
        "trend_90d": calculate_trend(prices, 90),
        "volatility": calculate_volatility(prices),
        "momentum": detect_momentum(prices),
        "sample_size": len(prices)
    }


def calculate_days_held(card: Dict[str, Any]) -> int:
    """Calculate number of days card has been held."""
    try:
        created_at = card.get("created_at") or card.get("createdAt")
        if not created_at:
            return 0

        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days = (datetime.utcnow() - created_date).days
        return max(0, days)
    except Exception:
        return 0


def generate_recommendation(card: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate buy/hold/sell recommendation based on trends and metrics."""

    purchase_price = float(card.get("purchase_price") or card.get("purchasePrice") or 0)
    estimated_value = float(card.get("estimated_value") or card.get("estimatedValue") or 0)

    if purchase_price == 0:
        return {
            "action": "HOLD",
            "confidence": 0.3,
            "reasoning": "Unable to calculate ROI without purchase price data.",
            "category": "UNKNOWN",
            "metrics": metrics
        }

    profit = estimated_value - purchase_price
    roi = (profit / purchase_price) * 100
    days_held = calculate_days_held(card)

    trend_7d = metrics.get("trend_7d", 0)
    trend_30d = metrics.get("trend_30d", 0)
    trend_90d = metrics.get("trend_90d", 0)
    momentum = metrics.get("momentum", "STEADY")
    volatility = metrics.get("volatility", 0)

    # SELL Logic: Take profits on winners
    if roi > 50 and trend_30d < -5:
        return {
            "action": "SELL",
            "confidence": 0.85,
            "reasoning": f"Strong profit ({roi:.1f}% ROI) with recent downtrend. Lock in gains while value is high.",
            "category": "TAKE_PROFIT",
            "metrics": metrics
        }

    if roi > 30 and days_held < 90 and trend_7d < -10:
        return {
            "action": "SELL",
            "confidence": 0.8,
            "reasoning": f"Quick flip opportunity ({roi:.1f}% in {days_held} days) showing weakness. Exit before reversal.",
            "category": "QUICK_FLIP",
            "metrics": metrics
        }

    # CUT_LOSS Logic: Exit losing positions
    if roi < -30 and trend_30d < -5:
        return {
            "action": "CUT_LOSS",
            "confidence": 0.9,
            "reasoning": f"Significant loss ({roi:.1f}%) with continuing downtrend. Cut losses to preserve capital.",
            "category": "CUT_LOSS",
            "metrics": metrics
        }

    if roi < -25 and momentum == "ACCELERATING" and trend_30d < 0:
        return {
            "action": "CUT_LOSS",
            "confidence": 0.85,
            "reasoning": f"Loss accelerating ({roi:.1f}% ROI, {momentum.lower()} momentum). Exit before further decline.",
            "category": "CUT_LOSS",
            "metrics": metrics
        }

    # BUY_MORE Logic: Average down or add to winners
    if roi < -20 and trend_30d > 5 and momentum == "ACCELERATING":
        return {
            "action": "BUY_MORE",
            "confidence": 0.8,
            "reasoning": f"Strong recovery trend (+{trend_30d:.1f}% over 30d) after dip. Average down while momentum builds.",
            "category": "RECOVERY",
            "metrics": metrics
        }

    if roi < -10 and trend_7d > 10 and trend_30d > 0:
        return {
            "action": "BUY_MORE",
            "confidence": 0.75,
            "reasoning": f"Early recovery signal (+{trend_7d:.1f}% last 7d). Add position at discount before full rebound.",
            "category": "RECOVERY",
            "metrics": metrics
        }

    if roi > 20 and roi < 40 and trend_30d > 10 and momentum == "ACCELERATING":
        return {
            "action": "BUY_MORE",
            "confidence": 0.7,
            "reasoning": f"Momentum building (+{trend_30d:.1f}% trend) with room to run. Add to winning position.",
            "category": "MOMENTUM",
            "metrics": metrics
        }

    # HOLD Logic: Default for everything else
    category = "LONG_HOLD"
    confidence = 0.6
    reasoning = f"Steady performance ({roi:.1f}% ROI). Hold and monitor for trend changes."

    if roi > 10 and roi < 30:
        category = "LONG_HOLD"
        confidence = 0.7
        reasoning = f"Solid gain ({roi:.1f}% ROI) with stable trends. Continue holding for further appreciation."
    elif roi < 10 and roi > -10:
        category = "STEADY"
        confidence = 0.5
        reasoning = f"Neutral position ({roi:.1f}% ROI). Watch for trend development before action."
    elif trend_30d > 5:
        category = "MOMENTUM"
        confidence = 0.65
        reasoning = f"Positive momentum (+{trend_30d:.1f}% over 30d). Hold for continued growth."

    return {
        "action": "HOLD",
        "confidence": confidence,
        "reasoning": reasoning,
        "category": category,
        "metrics": metrics
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/{card_id}/recommendation")
async def get_card_recommendation(card_id: str, user = Depends(get_current_user)):
    """Get AI recommendation for a specific card."""

    # Get card
    card = get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Verify ownership
    if card.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get price history
    price_history = get_market_price_history(card_id, limit=365)

    # Analyze trends
    metrics = analyze_card_trends(card, price_history)

    # Generate recommendation
    recommendation = generate_recommendation(card, metrics)

    return recommendation


@router.get("/portfolio/recommendations")
async def get_portfolio_recommendations(user = Depends(get_current_user)):
    """Get AI recommendations for entire portfolio."""

    # Get all user cards
    result = get_user_cards(user["id"], page=1, per_page=1000)
    cards = result.get("cards", [])

    recommendations = []
    summary = {
        "buyMore": 0,
        "hold": 0,
        "sell": 0,
        "cutLoss": 0
    }

    for card in cards:
        # Get price history
        price_history = get_market_price_history(card["id"], limit=365)

        # Analyze trends
        metrics = analyze_card_trends(card, price_history)

        # Generate recommendation
        rec = generate_recommendation(card, metrics)

        # Add card info to recommendation
        recommendations.append({
            "cardId": card["id"],
            "playerName": card.get("playerName") or card.get("player_name"),
            "year": card.get("year"),
            "set": card.get("set") or card.get("card_set"),
            "action": rec["action"],
            "confidence": rec["confidence"],
            "category": rec["category"],
            "reasoning": rec["reasoning"],
            "metrics": rec["metrics"]
        })

        # Update summary
        action = rec["action"]
        if action == "BUY_MORE":
            summary["buyMore"] += 1
        elif action == "HOLD":
            summary["hold"] += 1
        elif action == "SELL":
            summary["sell"] += 1
        elif action == "CUT_LOSS":
            summary["cutLoss"] += 1

    # Sort by confidence (high to low)
    recommendations.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "recommendations": recommendations,
        "summary": summary,
        "total": len(recommendations)
    }
