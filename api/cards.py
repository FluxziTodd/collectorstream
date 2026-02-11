"""
Card management routes for CollectorStream API
CRUD operations and card identification
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import httpx
import os
import base64

from auth import get_current_user
from database import (
    create_card, get_card_by_id, get_user_cards,
    update_card, delete_card, format_card,
    add_market_price, get_latest_market_price, get_market_price_history
)
from market_value import get_market_fetcher

router = APIRouter()

# Ximilar API configuration
XIMILAR_API_KEY = os.environ.get("XIMILAR_API_KEY", "")
XIMILAR_API_URL = "https://api.ximilar.com/collectibles/v2/sport_id"

# ============================================================================
# Pydantic Models
# ============================================================================

class GradingInfo(BaseModel):
    company: Optional[str] = None
    grade: Optional[str] = None
    certNumber: Optional[str] = None

class CardCreate(BaseModel):
    playerName: str = Field(..., alias="player_name")
    team: Optional[str] = None
    year: Optional[str] = None
    set: Optional[str] = None
    cardNumber: Optional[str] = Field(None, alias="card_number")
    manufacturer: Optional[str] = None
    sport: str = "MLB"
    condition: Optional[str] = None
    gradingCompany: Optional[str] = Field(None, alias="grading_company")
    gradingGrade: Optional[str] = Field(None, alias="grading_grade")
    gradingCertNumber: Optional[str] = Field(None, alias="grading_cert_number")
    frontImageUrl: Optional[str] = Field(None, alias="front_image_url")
    backImageUrl: Optional[str] = Field(None, alias="back_image_url")
    purchasePrice: Optional[float] = Field(None, alias="purchase_price")
    estimatedValue: Optional[float] = Field(None, alias="estimated_value")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True

class CardUpdate(BaseModel):
    playerName: Optional[str] = Field(None, alias="player_name")
    team: Optional[str] = None
    year: Optional[str] = None
    set: Optional[str] = None
    cardNumber: Optional[str] = Field(None, alias="card_number")
    manufacturer: Optional[str] = None
    sport: Optional[str] = None
    condition: Optional[str] = None
    gradingCompany: Optional[str] = Field(None, alias="grading_company")
    gradingGrade: Optional[str] = Field(None, alias="grading_grade")
    gradingCertNumber: Optional[str] = Field(None, alias="grading_cert_number")
    frontImageUrl: Optional[str] = Field(None, alias="front_image_url")
    backImageUrl: Optional[str] = Field(None, alias="back_image_url")
    purchasePrice: Optional[float] = Field(None, alias="purchase_price")
    estimatedValue: Optional[float] = Field(None, alias="estimated_value")
    notes: Optional[str] = None

    class Config:
        populate_by_name = True

class CardResponse(BaseModel):
    id: str
    playerName: str
    team: Optional[str] = None
    year: Optional[str] = None
    set: Optional[str] = None
    cardNumber: Optional[str] = None
    manufacturer: Optional[str] = None
    sport: str
    condition: Optional[str] = None
    grading: Optional[GradingInfo] = None
    frontImageUrl: Optional[str] = None
    backImageUrl: Optional[str] = None
    purchasePrice: Optional[float] = None
    estimatedValue: Optional[float] = None
    notes: Optional[str] = None
    createdAt: str
    updatedAt: str

class CardListResponse(BaseModel):
    cards: List[CardResponse]
    total: int
    page: int
    perPage: int

class CardIdentificationResponse(BaseModel):
    playerName: Optional[str] = None
    team: Optional[str] = None
    year: Optional[str] = None
    set: Optional[str] = None
    cardNumber: Optional[str] = None
    manufacturer: Optional[str] = None
    sport: Optional[str] = None
    estimatedValue: Optional[float] = None
    confidence: float
    grading: Optional[GradingInfo] = None

# ============================================================================
# Routes
# ============================================================================

@router.get("", response_model=CardListResponse)
async def list_cards(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sport: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all cards for the current user."""
    result = get_user_cards(current_user["id"], page, per_page, sport)
    return {
        "cards": result["cards"],
        "total": result["total"],
        "page": result["page"],
        "perPage": result["per_page"]
    }

@router.post("", response_model=CardResponse)
async def add_card(
    card_data: CardCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new card to the collection."""
    # Convert to dict for database
    data = {
        "player_name": card_data.playerName,
        "team": card_data.team,
        "year": card_data.year,
        "set": card_data.set,
        "card_number": card_data.cardNumber,
        "manufacturer": card_data.manufacturer,
        "sport": card_data.sport,
        "condition": card_data.condition,
        "grading_company": card_data.gradingCompany,
        "grading_grade": card_data.gradingGrade,
        "grading_cert_number": card_data.gradingCertNumber,
        "front_image_url": card_data.frontImageUrl,
        "back_image_url": card_data.backImageUrl,
        "purchase_price": card_data.purchasePrice,
        "estimated_value": card_data.estimatedValue,
        "notes": card_data.notes
    }

    card = create_card(current_user["id"], data)
    return format_card(card)

@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific card."""
    card = get_card_by_id(card_id)

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return format_card(card)

@router.put("/{card_id}", response_model=CardResponse)
async def update_card_route(
    card_id: str,
    card_data: CardUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a card."""
    # Convert to dict for database
    data = {}
    if card_data.playerName is not None:
        data["player_name"] = card_data.playerName
    if card_data.team is not None:
        data["team"] = card_data.team
    if card_data.year is not None:
        data["year"] = card_data.year
    if card_data.set is not None:
        data["set"] = card_data.set
    if card_data.cardNumber is not None:
        data["card_number"] = card_data.cardNumber
    if card_data.manufacturer is not None:
        data["manufacturer"] = card_data.manufacturer
    if card_data.sport is not None:
        data["sport"] = card_data.sport
    if card_data.condition is not None:
        data["condition"] = card_data.condition
    if card_data.gradingCompany is not None:
        data["grading_company"] = card_data.gradingCompany
    if card_data.gradingGrade is not None:
        data["grading_grade"] = card_data.gradingGrade
    if card_data.gradingCertNumber is not None:
        data["grading_cert_number"] = card_data.gradingCertNumber
    if card_data.frontImageUrl is not None:
        data["front_image_url"] = card_data.frontImageUrl
    if card_data.backImageUrl is not None:
        data["back_image_url"] = card_data.backImageUrl
    if card_data.purchasePrice is not None:
        data["purchase_price"] = card_data.purchasePrice
    if card_data.estimatedValue is not None:
        data["estimated_value"] = card_data.estimatedValue
    if card_data.notes is not None:
        data["notes"] = card_data.notes

    card = update_card(card_id, current_user["id"], data)

    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return format_card(card)

@router.delete("/{card_id}")
async def delete_card_route(
    card_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a card."""
    success = delete_card(card_id, current_user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Card not found")

    return {"message": "Card deleted"}

@router.post("/identify", response_model=CardIdentificationResponse)
async def identify_card(
    image: UploadFile = File(...),
    back_image: Optional[UploadFile] = File(None),
    sport: Optional[str] = "baseball",
    current_user: dict = Depends(get_current_user)
):
    """
    Identify a card from front and back images using multi-model AI approach.
    Uses Claude Vision, OpenRouter, and Ximilar in fallback chain.
    Target: 90%+ accuracy with confidence scoring.
    """
    from card_identifier import get_identifier

    # Read front image data
    front_data = await image.read()
    front_base64 = base64.b64encode(front_data).decode()

    print(f"🔍 Identifying {sport} card...")
    print(f"📊 Front image size: {len(front_data) / 1024:.1f} KB")

    # Read back image if provided
    back_base64 = None
    if back_image:
        back_data = await back_image.read()
        back_base64 = base64.b64encode(back_data).decode()
        print(f"📊 Back image size: {len(back_data) / 1024:.1f} KB")

    # Use multi-model identifier
    try:
        identifier = get_identifier()
        result = await identifier.identify_card(front_base64, sport, back_base64)

        print(f"✅ Identification complete:")
        print(f"   Model: {result.modelUsed}")
        print(f"   Confidence: {result.confidence:.0%}")
        print(f"   Player: {result.playerName or 'Unknown'}")
        print(f"   Needs Confirmation: {result.needsConfirmation}")

        # Convert to API response format
        return CardIdentificationResponse(
            playerName=result.playerName,
            team=result.team,
            year=result.year,
            set=result.set,
            cardNumber=result.cardNumber,
            manufacturer=result.manufacturer,
            sport=result.sport,
            estimatedValue=result.estimatedValue,
            confidence=result.confidence,
            grading=result.grading
        )

    except Exception as e:
        print(f"❌ Identification error: {e}")
        import traceback
        traceback.print_exc()

        # Return low confidence result on error
        return CardIdentificationResponse(
            playerName=None,
            team=None,
            year=None,
            set=None,
            cardNumber=None,
            manufacturer=None,
            estimatedValue=None,
            confidence=0.1,
            grading=None
        )

async def identify_with_ximilar(image_base64: str) -> CardIdentificationResponse:
    """Identify card using Ximilar API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            XIMILAR_API_URL,
            headers={
                "Authorization": f"Token {XIMILAR_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "records": [
                    {"_base64": image_base64}
                ]
            },
            timeout=30.0
        )

        if response.status_code != 200:
            raise Exception(f"Ximilar API error: {response.status_code}")

        data = response.json()

        # Parse Ximilar response
        if data.get("records") and len(data["records"]) > 0:
            record = data["records"][0]

            # Extract card info from Ximilar response
            player_name = None
            team = None
            year = None
            card_set = None
            card_number = None
            manufacturer = None
            estimated_value = None
            confidence = 0.5

            # Ximilar returns structured data in various fields
            if "_objects" in record:
                for obj in record["_objects"]:
                    if obj.get("name"):
                        player_name = obj["name"]
                    if obj.get("prob"):
                        confidence = obj["prob"]

            # Check for OCR results
            if "_tags" in record:
                tags = record["_tags"]
                for tag in tags:
                    tag_name = tag.get("name", "").lower()
                    if "year" in tag_name:
                        year = tag.get("value")
                    elif "team" in tag_name:
                        team = tag.get("value")

            # Check for grading info
            grading = None
            if record.get("_grading"):
                grading_data = record["_grading"]
                grading = GradingInfo(
                    company=grading_data.get("company"),
                    grade=grading_data.get("grade"),
                    certNumber=grading_data.get("cert_number")
                )

            # Check for price estimate
            if record.get("_prices"):
                prices = record["_prices"]
                if prices:
                    estimated_value = prices[0].get("price")

            return CardIdentificationResponse(
                playerName=player_name,
                team=team,
                year=year,
                set=card_set,
                cardNumber=card_number,
                manufacturer=manufacturer,
                estimatedValue=estimated_value,
                confidence=confidence,
                grading=grading
            )

    return CardIdentificationResponse(confidence=0.1)

@router.post("/{card_id}/market-value")
async def update_card_market_value(
    card_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch current market value for a card from eBay sold listings.

    This endpoint:
    1. Fetches the card details
    2. Searches eBay for sold comps
    3. Filters out lots, reprints, and outliers
    4. Calculates median market value
    5. Stores the price in history
    6. Returns current market value
    """
    # Get the card
    card = get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch market value from eBay
    fetcher = get_market_fetcher()
    market_data = await fetcher.get_card_market_value(card)

    # Store in price history (even if null, to track when we checked)
    if market_data.get("market_price") is not None:
        add_market_price(card_id, market_data)
        print(f"✅ Stored market price for card {card_id}: ${market_data['market_price']}")

    return {
        "cardId": card_id,
        "marketPrice": market_data.get("market_price"),
        "sampleSize": market_data.get("sample_size", 0),
        "confidenceLevel": market_data.get("confidence_level", 0.0),
        "priceRangeLow": market_data.get("price_range_low"),
        "priceRangeHigh": market_data.get("price_range_high"),
        "source": market_data.get("source", "ebay_sold"),
        "checkedAt": datetime.utcnow().isoformat()
    }

@router.get("/{card_id}/market-value")
async def get_card_market_value(
    card_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the most recent market value for a card"""
    # Verify ownership
    card = get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get latest market price
    latest_price = get_latest_market_price(card_id)

    if not latest_price:
        return {
            "cardId": card_id,
            "marketPrice": None,
            "message": "No market value data available. Use POST to fetch current value."
        }

    return {
        "cardId": card_id,
        "marketPrice": latest_price["market_price"],
        "sampleSize": latest_price.get("sample_size", 0),
        "confidenceLevel": latest_price.get("confidence_level", 0.0),
        "priceRangeLow": latest_price.get("price_range_low"),
        "priceRangeHigh": latest_price.get("price_range_high"),
        "source": latest_price.get("source", "ebay_sold"),
        "checkedAt": latest_price["checked_at"]
    }

@router.get("/{card_id}/market-history")
async def get_card_price_history(
    card_id: str,
    limit: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get price history for a card (up to 365 data points)"""
    # Verify ownership
    card = get_card_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get price history
    history = get_market_price_history(card_id, limit)

    return {
        "cardId": card_id,
        "history": [
            {
                "marketPrice": h["market_price"],
                "sampleSize": h.get("sample_size", 0),
                "confidenceLevel": h.get("confidence_level", 0.0),
                "priceRangeLow": h.get("price_range_low"),
                "priceRangeHigh": h.get("price_range_high"),
                "checkedAt": h["checked_at"]
            }
            for h in history
        ],
        "total": len(history)
    }
