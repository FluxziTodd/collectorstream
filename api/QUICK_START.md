# 🚀 Quick Start - 90% Accuracy Upgrade

## What I Just Built

✅ **Multi-Model Card Identification System** - Tries 5 AI models until confidence > 70%
✅ **Advanced VLM Prompting** - Structured JSON extraction with confidence scores
✅ **Visual Cue Detection** - Border colors, foil patterns, serial numbers, rookie logos
✅ **Automatic Fallback Chain** - If Claude fails, tries OpenRouter free models, then Ximilar
✅ **Deployment Script** - One command to update production server
✅ **Test Script** - Validate locally before deploying

## 🎯 Expected Results

**Before:** 10% confidence, all fields empty
**After:** 70-90% confidence, most fields correct

## 📝 Quick Deploy (3 Minutes)

### 1. Get OpenRouter API Key (Optional but Recommended)

```bash
# Go to https://openrouter.ai/
# Sign in with GitHub
# Go to Keys → Create Key
# Copy the key (starts with sk-or-)
```

### 2. Add to Environment

```bash
cd /Users/toddwallace/agents/sports-card-scout

# Add OpenRouter key (you already have ANTHROPIC_API_KEY)
echo 'OPENROUTER_API_KEY=sk-or-YOUR-KEY-HERE' >> .env
```

### 3. Test Locally (Optional)

```bash
cd api

# Export API keys
export $(cat ../.env | xargs)

# Test with a card image (if you have one)
python test_identification.py ~/path/to/card.jpg baseball
```

### 4. Deploy to Production

```bash
cd api
./deploy.sh

# Takes ~30 seconds
# Automatically:
# - Copies files to server
# - Adds API keys to server .env
# - Installs dependencies
# - Restarts API
```

### 5. Test from iPhone

1. Open CollectorStream app
2. Scan a card
3. Check if confidence is 70%+ (was 10%)
4. Verify fields are filled correctly

## 🔍 What Changed

### Backend Files

- **NEW:** `card_identifier.py` - Multi-model AI orchestrator (500 lines)
- **UPDATED:** `cards.py` - Uses new identifier instead of basic Ximilar
- **UPDATED:** `.env.example` - Added ANTHROPIC_API_KEY and OPENROUTER_API_KEY
- **NEW:** `deploy.sh` - Production deployment script
- **NEW:** `test_identification.py` - Local testing tool
- **NEW:** `AI_ACCURACY_UPGRADE.md` - Full documentation

### How It Works

```
1. iOS app captures card → sends to /cards/identify
2. Backend receives image → passes to MultiModelCardIdentifier
3. Try Claude 3.5 Sonnet (Anthropic) → if confidence > 70%, return ✅
4. If not, try Llama Nemotron (OpenRouter free) → if confidence > 70%, return ✅
5. If not, try Qwen 2.5 (OpenRouter free) → if confidence > 70%, return ✅
6. If not, try Llama 3.2 Vision → if confidence > 70%, return ✅
7. If not, try Gemini 2.0 → if confidence > 70%, return ✅
8. If not, try Ximilar → return whatever we get
9. Return result to iOS → show confidence + pre-fill fields
```

### What Gets Extracted

```json
{
  "playerName": "Mike Trout",
  "team": "Angels",
  "year": "2023",
  "set": "Topps Chrome",
  "cardNumber": "1",
  "manufacturer": "Topps",
  "parallelVariant": "Orange Refractor /25",
  "confidence": 0.92,
  "visualCues": {
    "borderColor": "orange",
    "foilPattern": "refractor",
    "serialNumber": "013/25",
    "rookieLogo": false
  },
  "fieldConfidence": {
    "playerName": 0.98,
    "team": 0.95,
    "year": 0.90,
    "set": 0.85,
    "cardNumber": 0.88
  }
}
```

## 📊 Monitoring

### View Logs

```bash
ssh ubuntu@api.collectorstream.com
sudo journalctl -u collectorstream-api -f

# Look for:
# ✅ "High confidence (92%) from claude-3-5-sonnet"
# 🎯 "Player: Mike Trout, Confidence: 92%"
```

### Check Results

After scanning 10 cards:
- Count how many fields were correct
- Calculate: (Correct Fields) / (Total Fields) = Accuracy %
- Target: 90%+

## 💡 Next Steps

1. **Deploy** (do this first!)
2. **Scan 10 cards** - Test with real cards from your collection
3. **Measure accuracy** - Count correct vs total fields
4. **Report results** - "8/10 cards identified correctly = 80%"
5. **Tune prompts** - If accuracy < 70%, adjust VLM prompts in card_identifier.py
6. **Add two-pass verification** - For low confidence fields, ask confirmation questions
7. **Build checklist database** - Cross-validate against known card sets

## 🆘 Troubleshooting

**Q: Still getting 10% confidence?**
A: Check API keys are set on server: `ssh ubuntu@api.collectorstream.com 'cat collectorstream-api/.env | grep ANTHROPIC'`

**Q: "Claude API error: 401"?**
A: Invalid API key. Check https://console.anthropic.com/ and regenerate

**Q: Taking too long (>10 seconds)?**
A: Check logs, model might be hitting rate limits. Add OpenRouter key for fallback.

**Q: Some fields correct, others wrong?**
A: Normal! Check field confidence scores. Fields < 0.7 need user verification.

## 🎉 Success Indicators

✅ Confidence goes from 10% → 70%+
✅ Player name filled correctly most times
✅ Year and set extracted accurately
✅ Card number identified (not always perfect)
✅ User just needs to verify, not type everything

---

**Ready to Deploy?**

```bash
cd /Users/toddwallace/agents/sports-card-scout/api
./deploy.sh
```

Then test from your iPhone! 📱
