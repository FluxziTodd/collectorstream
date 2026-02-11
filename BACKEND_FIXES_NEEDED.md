# Backend API Fixes Needed for CollectorStream

## Summary
The iOS app is working correctly and sending all data properly. However, the backend API has issues storing and returning certain fields.

## Issue 1: Estimated Value Not Being Stored

**What's happening:**
- iOS sends: `estimatedValue: 8.0`
- Backend stores: ❌ Not stored
- Backend returns: `estimatedValue: 0.0`

**Where to fix:**
- File: `/Users/toddwallace/agents/sports-card-scout/api/models.py`
- Ensure the `Card` model has `estimated_value` field
- File: `/Users/toddwallace/agents/sports-card-scout/api/routes/cards.py`
- POST `/cards` endpoint must accept and save `estimated_value`
- GET `/cards` endpoint must return `estimated_value` in response

**Expected behavior:**
```python
# Card model should include:
estimated_value = db.Column(db.Float, nullable=True)

# POST /cards should handle:
card.estimated_value = request.json.get('estimatedValue')

# GET /cards should return:
{
    "estimatedValue": card.estimated_value,
    ...
}
```

---

## Issue 2: Sport Detection Not Working

**What's happening:**
- AI identification doesn't return `sport` field
- iOS defaults to "Baseball" for all cards
- WNBA cards are being tagged as MLB

**Where to fix:**
- File: `/Users/toddwallace/agents/sports-card-scout/api/services/card_identifier.py`
- Add sport detection to the AI identification logic
- Return `sport` field in the identification response

**Expected behavior:**
```python
# Identification response should include:
{
    "playerName": "...",
    "team": "...",
    "sport": "wnba",  # ← ADD THIS
    "estimatedValue": 8.0,
    ...
}
```

**Sport values to return:**
- "baseball" or "mlb"
- "basketball" or "nba"
- "wnba"
- "football" or "nfl"
- "hockey" or "nhl"
- "soccer"

---

## Issue 3: Image URLs Require Authentication

**What's happening:**
- Images upload successfully
- Image URLs are stored correctly
- But images might require authentication to access

**Where to check:**
- File: `/etc/nginx/conf.d/collectorstream-api.conf`
- Ensure `/uploads/` location is publicly accessible:

```nginx
location /uploads/ {
    alias /home/ec2-user/sports-card-scout/uploads/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    # Make sure no auth_request or other auth directive is here
}
```

**iOS workaround applied:**
- Created `AuthenticatedAsyncImage` that includes Bearer token
- Should work either way (public or authenticated access)

---

## Testing Checklist

After making backend fixes:

- [ ] Scan a card with AI identification
- [ ] Check iOS console logs:
  ```
  💰 Estimated value: 8.0 (when creating)
  🏀 Sport: wnba (when identified as WNBA)
  ```
- [ ] Save the card
- [ ] Fetch cards and verify:
  ```
  estimatedValue: 8.0 (not 0.0)
  sport: basketball (for WNBA card)
  ```
- [ ] Check collection view shows:
  - Correct sport badge
  - Estimated value
  - Total collection value sum
  - Thumbnails display

---

## iOS App Status

✅ **COMPLETE AND WORKING:**
- Vision-based card detection and cropping
- Image upload with proper URLs
- Card creation with all fields
- Thumbnail display with authentication
- "Scan Another" prompt
- All data being sent correctly to API

❌ **BLOCKED BY BACKEND:**
- Estimated value storage/retrieval
- Sport auto-detection
- Collection value summation (depends on estimated_value being returned)

---

## Priority Order

1. **HIGH**: Fix `estimated_value` storage (makes value tracking work)
2. **HIGH**: Fix sport detection (makes sport categorization work)
3. **MEDIUM**: Verify image serving config (thumbnails might already work with auth)

---

## Questions?

The iOS app is sending debug logs for everything. Check Xcode console when testing to see exactly what's being sent vs. what's being returned.
