#!/usr/bin/env python3
"""
Test Card Identification System
Tests the multi-model card identifier with sample images
"""

import asyncio
import base64
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from card_identifier import MultiModelCardIdentifier


async def test_with_image(image_path: str, sport: str = "baseball"):
    """Test identification with a specific image."""

    print(f"\n{'='*80}")
    print(f"🧪 Testing: {Path(image_path).name}")
    print(f"{'='*80}\n")

    # Read and encode image
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode()

        print(f"📊 Image size: {len(image_data) / 1024:.1f} KB")
        print(f"🏀 Sport: {sport}\n")

    except FileNotFoundError:
        print(f"❌ Image not found: {image_path}")
        return

    # Initialize identifier
    identifier = MultiModelCardIdentifier()

    # Check available APIs
    print("🔑 API Keys Status:")
    print(f"   Anthropic: {'✅ Configured' if identifier.anthropic_key else '❌ Missing'}")
    print(f"   OpenRouter: {'✅ Configured' if identifier.openrouter_key else '❌ Missing'}")
    print(f"   Ximilar: {'✅ Configured' if identifier.ximilar_key else '❌ Missing'}")
    print()

    # Run identification
    try:
        result = await identifier.identify_card(image_base64, sport)

        print(f"\n{'='*80}")
        print("📋 IDENTIFICATION RESULTS")
        print(f"{'='*80}\n")

        print(f"🤖 Model Used: {result.modelUsed}")
        print(f"🎯 Overall Confidence: {result.confidence:.1%}")
        print(f"⚠️  Needs Confirmation: {result.needsConfirmation}\n")

        print("📄 Extracted Fields:")
        print(f"   Player Name: {result.playerName or 'Unknown'}")
        print(f"   Team: {result.team or 'Unknown'}")
        print(f"   Year: {result.year or 'Unknown'}")
        print(f"   Set: {result.set or 'Unknown'}")
        print(f"   Card Number: {result.cardNumber or 'Unknown'}")
        print(f"   Manufacturer: {result.manufacturer or 'Unknown'}")
        print(f"   Parallel Variant: {result.parallelVariant or 'Base'}")

        if result.fieldConfidence:
            print(f"\n📊 Field Confidence Scores:")
            print(f"   Player Name: {result.fieldConfidence.playerName:.0%}")
            print(f"   Team: {result.fieldConfidence.team:.0%}")
            print(f"   Year: {result.fieldConfidence.year:.0%}")
            print(f"   Set: {result.fieldConfidence.set:.0%}")
            print(f"   Card Number: {result.fieldConfidence.cardNumber:.0%}")
            print(f"   Manufacturer: {result.fieldConfidence.manufacturer:.0%}")

        if result.visualCues:
            print(f"\n🎨 Visual Cues:")
            if result.visualCues.borderColor:
                print(f"   Border Color: {result.visualCues.borderColor}")
            if result.visualCues.foilPattern:
                print(f"   Foil Pattern: {result.visualCues.foilPattern}")
            if result.visualCues.serialNumber:
                print(f"   Serial Number: {result.visualCues.serialNumber}")
            if result.visualCues.rookieLogo:
                print(f"   ⭐ Rookie Card")
            if result.visualCues.autograph:
                print(f"   ✍️ Autograph")
            if result.visualCues.relic:
                print(f"   🎽 Game-Used Relic")

        if result.grading:
            print(f"\n🏆 Grading Info:")
            print(f"   Company: {result.grading.company}")
            print(f"   Grade: {result.grading.grade}")
            print(f"   Cert #: {result.grading.certNumber}")

        if result.estimatedValue:
            print(f"\n💰 Estimated Value: ${result.estimatedValue:.2f}")

        # Accuracy assessment
        print(f"\n{'='*80}")
        if result.confidence >= 0.9:
            print("✅ EXCELLENT - High confidence identification")
        elif result.confidence >= 0.7:
            print("✅ GOOD - Acceptable confidence, minimal verification needed")
        elif result.confidence >= 0.5:
            print("⚠️  MEDIUM - User should verify all fields")
        else:
            print("❌ LOW - Manual entry recommended")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Identification failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run tests."""

    # Check for command line image path
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        sport = sys.argv[2] if len(sys.argv) > 2 else "baseball"
        await test_with_image(image_path, sport)
        return

    print("""
🧪 Card Identification Test Suite
================================

Usage:
    python test_identification.py <image_path> [sport]

Examples:
    python test_identification.py card.jpg baseball
    python test_identification.py rookie_card.jpg football
    python test_identification.py /path/to/card.heic basketball

Sports: baseball, football, basketball, hockey

Note: Set environment variables first:
    export ANTHROPIC_API_KEY="your-key"
    export OPENROUTER_API_KEY="your-key"
    """)


if __name__ == "__main__":
    asyncio.run(main())
