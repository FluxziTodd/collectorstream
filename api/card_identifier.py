"""
Multi-Model Card Identification Service
Implements CardLister methodology for 90%+ accuracy
"""

import base64
import httpx
import os
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class GradingInfo(BaseModel):
    company: Optional[str] = None
    grade: Optional[str] = None
    certNumber: Optional[str] = None

class VisualCues(BaseModel):
    borderColor: Optional[str] = None
    foilPattern: Optional[str] = None
    serialNumber: Optional[str] = None
    rookieLogo: bool = False
    autograph: bool = False
    relic: bool = False

class FieldConfidence(BaseModel):
    playerName: float = 0.0
    team: float = 0.0
    year: float = 0.0
    set: float = 0.0
    cardNumber: float = 0.0
    manufacturer: float = 0.0

class CardIdentificationResult(BaseModel):
    playerName: Optional[str] = None
    team: Optional[str] = None
    year: Optional[str] = None
    set: Optional[str] = None
    cardNumber: Optional[str] = None
    manufacturer: Optional[str] = None
    sport: Optional[str] = None
    parallelVariant: Optional[str] = None
    estimatedValue: Optional[float] = None
    confidence: float
    fieldConfidence: Optional[FieldConfidence] = None
    visualCues: Optional[VisualCues] = None
    grading: Optional[GradingInfo] = None
    modelUsed: str = "unknown"
    needsConfirmation: bool = False


class MultiModelCardIdentifier:
    """
    Multi-model card identification with automatic fallback chain.
    Based on CardLister's approach achieving 90%+ accuracy.
    """

    def __init__(self):
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.ximilar_key = os.environ.get("XIMILAR_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self.cardsight_key = os.environ.get("CARDSIGHT_API_KEY", "")

        # Model priority chain (CardSight is PRIMARY - specialized for sports cards)
        self.models = [
            {"name": "cardsight", "provider": "cardsight", "priority": 1},
            {"name": "gpt-4o", "provider": "openai", "priority": 2},
            {"name": "claude-3-5-sonnet", "provider": "anthropic", "priority": 3},
            {"name": "nvidia/llama-3.1-nemotron-70b-instruct:free", "provider": "openrouter", "priority": 4},
            {"name": "qwen/qwen-2.5-72b-instruct:free", "provider": "openrouter", "priority": 5},
            {"name": "meta-llama/llama-3.2-90b-vision-instruct:free", "provider": "openrouter", "priority": 6},
            {"name": "google/gemini-2.0-flash-exp:free", "provider": "openrouter", "priority": 7},
        ]

    async def identify_card(self, front_base64: str, sport: str = "baseball", back_base64: str = None) -> CardIdentificationResult:
        """
        Identify a card using multi-model approach with front and back images.
        Falls back through model chain until confidence > 0.7 or all models exhausted.
        """
        print(f"🔍 Starting card identification (suggested sport: {sport})...")
        if back_base64:
            print(f"📸 Using BOTH front and back images for identification")

        # Auto-detect sport using GPT-4o before CardSight (for accuracy)
        if self.openai_key or self.anthropic_key:
            detected_sport = await self._detect_sport(front_base64)
            if detected_sport and detected_sport != sport:
                print(f"🏀 Auto-detected sport: {detected_sport} (overriding {sport})")
                sport = detected_sport
            else:
                print(f"✅ Confirmed sport: {sport}")

        for model_config in self.models:
            try:
                print(f"📡 Trying model: {model_config['name']} (provider: {model_config['provider']})")

                if model_config["provider"] == "cardsight" and self.cardsight_key:
                    result = await self._identify_with_cardsight(front_base64, sport, back_base64)
                elif model_config["provider"] == "openai" and self.openai_key:
                    result = await self._identify_with_openai(front_base64, sport, back_base64)
                elif model_config["provider"] == "anthropic" and self.anthropic_key:
                    result = await self._identify_with_claude(front_base64, sport, back_base64)
                elif model_config["provider"] == "openrouter" and self.openrouter_key:
                    result = await self._identify_with_openrouter(front_base64, sport, model_config["name"], back_base64)
                else:
                    print(f"⚠️  Skipping {model_config['name']} - API key not configured")
                    continue

                if result and result.confidence > 0.7:
                    print(f"✅ High confidence ({result.confidence:.0%}) from {model_config['name']}")
                    result.modelUsed = model_config['name']
                    return result
                elif result and result.confidence > 0.3:
                    print(f"⚠️  Low confidence ({result.confidence:.0%}) from {model_config['name']}")
                    result.modelUsed = model_config['name']
                    result.needsConfirmation = True
                    return result

            except Exception as e:
                print(f"❌ Error with {model_config['name']}: {str(e)[:100]}")
                continue

        # All models failed - try Ximilar as last resort
        if self.ximilar_key:
            try:
                print("📡 Trying Ximilar as fallback...")
                result = await self._identify_with_ximilar(image_base64)
                if result:
                    result.modelUsed = "ximilar"
                    return result
            except Exception as e:
                print(f"❌ Ximilar error: {str(e)[:100]}")

        # All models exhausted - return low confidence result
        print("⚠️  All models exhausted - returning low confidence")
        return CardIdentificationResult(
            sport=sport,
            confidence=0.1,
            modelUsed="none",
            needsConfirmation=True
        )

    async def _detect_sport(self, front_base64: str) -> Optional[str]:
        """Quick sport detection using vision model."""
        try:
            prompt = """Look at this sports trading card. What sport is it?
Respond with ONLY ONE WORD from: baseball, basketball, football, hockey, soccer

If you see WNBA branding or women's basketball, respond: basketball"""

            if self.openai_key:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.openai_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "gpt-4o-mini",
                            "max_tokens": 10,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{front_base64}"}},
                                    {"type": "text", "text": prompt}
                                ]
                            }]
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        sport = data["choices"][0]["message"]["content"].strip().lower()
                        return sport if sport in ["baseball", "basketball", "football", "hockey", "soccer"] else None
            elif self.anthropic_key:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": self.anthropic_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 10,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": front_base64}},
                                    {"type": "text", "text": prompt}
                                ]
                            }]
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        sport = data["content"][0]["text"].strip().lower()
                        return sport if sport in ["baseball", "basketball", "football", "hockey", "soccer"] else None
        except Exception as e:
            print(f"⚠️  Sport detection failed: {str(e)[:50]}")
        return None

    async def _identify_with_cardsight(self, front_base64: str, sport: str, back_base64: str = None) -> Optional[CardIdentificationResult]:
        """Identify card using CardSight AI (specialized sports card service)."""

        # Map sport to CardSight segment
        sport_segment_map = {
            "baseball": "baseball",
            "basketball": "basketball",
            "football": "football",
            "hockey": "hockey",
            "soccer": "soccer",
            "wnba": "basketball",  # WNBA uses basketball segment
            "nba": "basketball",
            "nfl": "football",
            "mlb": "baseball",
            "nhl": "hockey"
        }

        segment = sport_segment_map.get(sport.lower(), "baseball")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # CardSight expects multipart/form-data with 'file' field
            # Note: CardSight only accepts one image, so we'll send the front image
            front_image_bytes = base64.b64decode(front_base64)

            files = {
                "image": ("card.jpg", front_image_bytes, "image/jpeg")
            }

            response = await client.post(
                f"https://api.cardsight.ai/v1/identify/card/{segment}",
                headers={
                    "X-API-Key": self.cardsight_key
                },
                files=files
            )

            if response.status_code != 200:
                raise Exception(f"CardSight API error: {response.status_code} - {response.text}")

            data = response.json()

            if not data.get("success"):
                raise Exception(f"CardSight identification failed: {data}")

            # Process detections (can have multiple cards)
            detections = data.get("detections", [])
            if not detections:
                return CardIdentificationResult(
                    confidence=0.3,
                    modelUsed="cardsight"
                )

            # Use first detection (highest confidence)
            detection = detections[0]

            # Map confidence string to float
            confidence_map = {
                "High": 0.9,
                "Medium": 0.7,
                "Low": 0.5
            }
            confidence = confidence_map.get(detection.get("confidence", "Low"), 0.5)

            # Get AI identification (always present)
            ai_id = detection.get("aiIdentification", {})

            # Get full card data if matched in catalog
            card_data = detection.get("card", {})

            # Prefer catalog data, fallback to AI identification
            player_name = card_data.get("name") or ai_id.get("name")
            year = card_data.get("year") or ai_id.get("year")
            set_name = card_data.get("setName") or ai_id.get("set")
            card_number = card_data.get("number") or ai_id.get("number")
            manufacturer = card_data.get("manufacturer")
            release_name = card_data.get("releaseName") or ai_id.get("release")

            # Handle parallel variants
            parallel_info = card_data.get("parallel")
            parallel_variant = None
            if parallel_info:
                parallel_variant = parallel_info.get("name")
                if parallel_info.get("numberedTo"):
                    parallel_variant += f" /{parallel_info['numberedTo']}"

            return CardIdentificationResult(
                playerName=player_name,
                team=None,  # CardSight doesn't return team
                year=year,
                set=f"{release_name} {set_name}".strip() if release_name and set_name else (release_name or set_name),
                cardNumber=card_number,
                manufacturer=manufacturer,
                sport=sport,
                parallelVariant=parallel_variant,
                estimatedValue=None,  # CardSight doesn't provide values in identify endpoint
                confidence=confidence,
                modelUsed="cardsight"
            )

    async def _identify_with_claude(self, front_base64: str, sport: str, back_base64: str = None) -> Optional[CardIdentificationResult]:
        """Identify card using Claude Vision (Anthropic API) with front and back images."""

        prompt = self._build_extraction_prompt(sport, has_back=bool(back_base64))

        # Build content array
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": front_base64
                }
            }
        ]

        if back_base64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": back_base64
                }
            })

        content.append({
            "type": "text",
            "text": prompt
        })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": content
                        }
                    ]
                }
            )

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")

            data = response.json()
            text_response = data["content"][0]["text"]

            # Parse JSON from response
            return self._parse_vlm_response(text_response, "claude", sport)

    async def _identify_with_openai(self, front_base64: str, sport: str, back_base64: str = None) -> Optional[CardIdentificationResult]:
        """Identify card using OpenAI GPT-4 Vision with front and back images."""

        prompt = self._build_extraction_prompt(sport, has_back=bool(back_base64))

        # Build content array with both images if available
        content = []

        # Add front image
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{front_base64}"
            }
        })

        # Add back image if provided
        if back_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{back_base64}"
                }
            })

        # Add text prompt
        content.append({
            "type": "text",
            "text": prompt
        })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": content
                        }
                    ]
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

            data = response.json()
            text_response = data["choices"][0]["message"]["content"]

            return self._parse_vlm_response(text_response, "gpt-4o", sport)

    async def _identify_with_openrouter(self, front_base64: str, sport: str, model: str, back_base64: str = None) -> Optional[CardIdentificationResult]:
        """Identify card using OpenRouter API with front and back images."""

        prompt = self._build_extraction_prompt(sport, has_back=bool(back_base64))

        # Build content array
        content = [
            {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{front_base64}"
            }
        ]

        if back_base64:
            content.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{back_base64}"
            })

        content.append({
            "type": "text",
            "text": prompt
        })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": content
                        }
                    ]
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

            data = response.json()
            text_response = data["choices"][0]["message"]["content"]

            return self._parse_vlm_response(text_response, model, sport)

    async def _identify_with_ximilar(self, image_base64: str) -> Optional[CardIdentificationResult]:
        """Identify card using Ximilar API (sports card specific service)."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.ximilar.com/collectibles/v2/sport_id",
                headers={
                    "Authorization": f"Token {self.ximilar_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "records": [{"_base64": image_base64}]
                }
            )

            if response.status_code != 200:
                raise Exception(f"Ximilar API error: {response.status_code}")

            data = response.json()

            if data.get("records") and len(data["records"]) > 0:
                record = data["records"][0]

                player_name = None
                confidence = 0.5

                if "_objects" in record:
                    for obj in record["_objects"]:
                        if obj.get("name"):
                            player_name = obj["name"]
                        if obj.get("prob"):
                            confidence = obj["prob"]

                return CardIdentificationResult(
                    playerName=player_name,
                    confidence=confidence,
                    modelUsed="ximilar"
                )

        return None

    def _build_extraction_prompt(self, sport: str, has_back: bool = False) -> str:
        """Build detailed extraction prompt for VLM."""

        images_instruction = "I'm providing BOTH the front and back images of the card." if has_back else "I'm providing the front image of the card."
        back_note = "\n\n**IMPORTANT:** The BACK of the card contains critical info like card number (usually top right), set name (bottom), manufacturer (bottom left), and year/stats. Extract ALL details from BOTH images." if has_back else ""

        return f"""You are an expert at identifying sports cards. {images_instruction}

Analyze the {sport} card and extract all visible information.{back_note}

**CRITICAL INSTRUCTIONS:**
1. Look at ALL images carefully (front AND back if provided)
2. Extract ALL visible text, numbers, logos, and details
3. Card number is usually on the BACK in top right corner (e.g., "No. 95")
4. Set name and manufacturer are usually on the BACK at bottom
5. Return ONLY valid JSON, no other text
6. Use null for fields you cannot determine
7. Provide confidence scores (0.0 to 1.0) for each field

**JSON FORMAT (respond ONLY with this JSON, nothing else):**
{{
    "playerName": "Full player name exactly as shown",
    "team": "Team name or abbreviation",
    "year": "Card year (YYYY format)",
    "set": "Card set name (e.g., 'Topps Chrome', 'Panini Prizm')",
    "cardNumber": "Card number (e.g., '#23', 'RC-5')",
    "manufacturer": "Card manufacturer (Topps, Panini, Upper Deck, etc.)",
    "parallelVariant": "Parallel/variant name if any (Refractor, Orange /25, etc.)",
    "estimatedValue": 10.50,
    "visualCues": {{
        "borderColor": "Border color if distinctive",
        "foilPattern": "Refractor/foil pattern if present",
        "serialNumber": "Serial number if visible (e.g., '045/199')",
        "rookieLogo": true/false,
        "autograph": true/false,
        "relic": true/false
    }},
    "fieldConfidence": {{
        "playerName": 0.0-1.0,
        "team": 0.0-1.0,
        "year": 0.0-1.0,
        "set": 0.0-1.0,
        "cardNumber": 0.0-1.0,
        "manufacturer": 0.0-1.0
    }},
    "overallConfidence": 0.0-1.0
}}

**EXAMPLES:**

Modern base card:
{{"playerName": "Mike Trout", "team": "Angels", "year": "2023", "set": "Topps Chrome", "cardNumber": "1", "manufacturer": "Topps", "parallelVariant": null, "fieldConfidence": {{"playerName": 0.95, "year": 0.90, "set": 0.85}}, "overallConfidence": 0.90}}

Parallel card:
{{"playerName": "Shohei Ohtani", "team": "Dodgers", "year": "2024", "set": "Panini Prizm", "cardNumber": "50", "manufacturer": "Panini", "parallelVariant": "Orange Refractor /25", "visualCues": {{"borderColor": "orange", "foilPattern": "refractor", "serialNumber": "013/25"}}, "fieldConfidence": {{"playerName": 0.98, "year": 0.95}}, "overallConfidence": 0.92}}

**RULES:**
- If you see a rookie logo (RC), set rookieLogo: true
- If card has refractor/shimmer/foil, describe the pattern
- If you see numbers like "045/199", that's the serial number
- Border colors indicate parallel variants (orange, blue, gold, etc.)
- Confidence < 0.7 means you're unsure - be honest!
- Return ONLY JSON, no markdown, no explanation"""

    def _parse_vlm_response(self, text: str, model: str, sport: str = "baseball") -> Optional[CardIdentificationResult]:
        """Parse VLM JSON response into CardIdentificationResult."""

        try:
            # Clean markdown code blocks if present
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)

            # Calculate overall confidence
            overall_conf = data.get("overallConfidence", 0.5)

            # Extract field confidences
            field_conf_data = data.get("fieldConfidence", {})
            field_conf = FieldConfidence(
                playerName=field_conf_data.get("playerName", 0.5),
                team=field_conf_data.get("team", 0.5),
                year=field_conf_data.get("year", 0.5),
                set=field_conf_data.get("set", 0.5),
                cardNumber=field_conf_data.get("cardNumber", 0.5),
                manufacturer=field_conf_data.get("manufacturer", 0.5)
            )

            # Extract visual cues
            visual_cues_data = data.get("visualCues", {})
            visual_cues = VisualCues(
                borderColor=visual_cues_data.get("borderColor"),
                foilPattern=visual_cues_data.get("foilPattern"),
                serialNumber=visual_cues_data.get("serialNumber"),
                rookieLogo=visual_cues_data.get("rookieLogo", False),
                autograph=visual_cues_data.get("autograph", False),
                relic=visual_cues_data.get("relic", False)
            )

            result = CardIdentificationResult(
                playerName=data.get("playerName"),
                team=data.get("team"),
                year=data.get("year"),
                set=data.get("set"),
                cardNumber=data.get("cardNumber"),
                manufacturer=data.get("manufacturer"),
                sport=sport,
                parallelVariant=data.get("parallelVariant"),
                estimatedValue=data.get("estimatedValue"),
                confidence=overall_conf,
                fieldConfidence=field_conf,
                visualCues=visual_cues,
                modelUsed=model,
                needsConfirmation=(overall_conf < 0.7)
            )

            print(f"✅ Parsed result: Player={result.playerName}, Value=${result.estimatedValue or 0}, Confidence={result.confidence:.0%}")
            return result

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from {model}: {str(e)}")
            print(f"📄 Raw response: {text[:200]}...")
            return None
        except Exception as e:
            print(f"❌ Error parsing response from {model}: {str(e)}")
            return None


# Global identifier instance
_identifier = None

def get_identifier() -> MultiModelCardIdentifier:
    """Get or create global identifier instance."""
    global _identifier
    if _identifier is None:
        _identifier = MultiModelCardIdentifier()
    return _identifier
