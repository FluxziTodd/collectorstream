#!/bin/bash

# This script will be uploaded to the server and fix cards.py

cd /home/ubuntu/collectorstream-api

echo "Step 1: Restoring from backup..."
cp cards.py.backup cards.py

echo "Step 2: Applying fix with Python..."
python3 << 'ENDPYTHON'
import re

with open('cards.py', 'r') as f:
    content = f.read()

# Find the identify_card function and replace it
new_func = """@router.post("/identify", response_model=CardIdentificationResponse)
async def identify_card(
    image: UploadFile = File(...),
    sport: Optional[str] = "baseball",
    current_user: dict = Depends(get_current_user)
):
    \"\"\"Identify card using multi-model AI\"\"\"
    from card_identifier import get_identifier
    
    image_data = await image.read()
    image_base64 = base64.b64encode(image_data).decode()
    
    print(f"🔍 Identifying {sport} card...")
    
    try:
        identifier = get_identifier()
        result = await identifier.identify_card(image_base64, sport)
        
        print(f"✅ {result.modelUsed}: {result.confidence:.0%}")
        
        return CardIdentificationResponse(
            playerName=result.playerName,
            team=result.team,
            year=result.year,
            set=result.set,
            cardNumber=result.cardNumber,
            manufacturer=result.manufacturer,
            estimatedValue=result.estimatedValue,
            confidence=result.confidence,
            grading=result.grading
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        return CardIdentificationResponse(confidence=0.1, grading=None)
"""

lines = content.split('\n')
start = None
end = None

for i, line in enumerate(lines):
    if '@router.post("/identify"' in line and 'response_model=CardIdentificationResponse' in line:
        start = i
    elif start is not None and line.startswith('async def identify_with_ximilar'):
        end = i
        break

if start and end:
    new_lines = lines[:start] + new_func.split('\n') + [''] + lines[end:]
    with open('cards.py', 'w') as f:
        f.write('\n'.join(new_lines))
    print("✅ Fixed cards.py")
else:
    print("❌ Pattern not found")
ENDPYTHON

echo "Step 3: Restarting service..."
sudo systemctl restart collectorstream-api

sleep 2

echo "Step 4: Checking status..."
sudo systemctl status collectorstream-api --no-pager | head -10

echo "Step 5: Testing health endpoint..."
curl -s http://localhost:8000/health

echo ""
echo "✅ Fix complete!"
