#!/usr/bin/env python3
"""
Quick fix for cards.py - replaces the identify_card endpoint with new multi-model version
Run this on the server to fix the IndentationError
"""

import re

# Read the backup (clean version)
with open('/home/ubuntu/collectorstream-api/cards.py.backup', 'r') as f:
    content = f.read()

# Find the old identify_card function
old_pattern = r'@router\.post\("/identify", response_model=CardIdentificationResponse\).*?(?=@router\.|$)'

# New identify_card function with multi-model AI
new_function = '''@router.post("/identify", response_model=CardIdentificationResponse)
async def identify_card(
    image: UploadFile = File(...),
    sport: Optional[str] = "baseball",
    current_user: dict = Depends(get_current_user)
):
    """
    Identify a card from an image using multi-model AI approach.
    Uses Claude Vision, OpenRouter, and Ximilar in fallback chain.
    Target: 90%+ accuracy with confidence scoring.
    """
    from card_identifier import get_identifier

    # Read image data
    image_data = await image.read()
    image_base64 = base64.b64encode(image_data).decode()

    print(f"🔍 Identifying {sport} card...")
    print(f"📊 Image size: {len(image_data) / 1024:.1f} KB")

    # Use multi-model identifier
    try:
        identifier = get_identifier()
        result = await identifier.identify_card(image_base64, sport)

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
            confidence=result.confidence,
            needsConfirmation=result.needsConfirmation,
            visualCues={
                "borderColor": result.borderColor,
                "hasSerialNumber": result.hasSerialNumber,
                "isRefractor": result.isRefractor,
                "isAutographed": result.isAutographed
            },
            modelUsed=result.modelUsed
        )
    except Exception as e:
        print(f"❌ Identification failed: {e}")
        # Return empty response with low confidence
        return CardIdentificationResponse(
            playerName=None,
            team=None,
            year=None,
            set=None,
            cardNumber=None,
            manufacturer=None,
            confidence=0.0,
            needsConfirmation=True,
            visualCues={},
            modelUsed="error"
        )

'''

# Replace the old function with new one
updated_content = re.sub(old_pattern, new_function, content, flags=re.DOTALL)

# Write the updated file
with open('/home/ubuntu/collectorstream-api/cards.py', 'w') as f:
    f.write(updated_content)

print("✅ cards.py updated successfully!")
print("🔄 Now restart the service with: sudo systemctl restart collectorstream-api")
