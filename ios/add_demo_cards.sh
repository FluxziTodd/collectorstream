#!/bin/bash
# Add sample cards to demo account

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOTE0YjkwY2QtOTNiMS00YjY1LWIxYzQtZDJmNmRmMTU2MjU4IiwiZXhwIjoxNzcxNDYyMzk3LCJpYXQiOjE3NzA4NTc1OTd9.kGtCW0R5gt_onbU8zUCFG_uGibfaY3LomMyWLbRR7Wo"

echo "Adding sample cards to demo account..."

# Sample card 1
curl -X POST 'https://api.collectorstream.com/v1/cards' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "player_name": "Caitlin Clark",
    "year": 2024,
    "brand": "Panini",
    "card_number": "RC-1",
    "sport": "basketball",
    "team": "Indiana Fever",
    "purchase_price": 150.00,
    "estimated_value": 250.00
  }' 2>&1 | grep -q '"id"' && echo "✅ Added Caitlin Clark card"

# Sample card 2
curl -X POST 'https://api.collectorstream.com/v1/cards' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "player_name": "Victor Wembanyama",
    "year": 2023,
    "brand": "Panini",
    "card_number": "RC-5",
    "sport": "basketball",
    "team": "San Antonio Spurs",
    "purchase_price": 500.00,
    "estimated_value": 800.00
  }' 2>&1 | grep -q '"id"' && echo "✅ Added Victor Wembanyama card"

echo "Demo account ready!"
