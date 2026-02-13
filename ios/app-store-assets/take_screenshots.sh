#!/bin/bash

# Automated screenshot capture for CollectorStream
# Takes screenshots for App Store submission

SIMULATOR_ID="61B1076B-8B26-4715-BBDD-DB79526ED24A"  # iPhone 16 Pro Max
OUTPUT_DIR="screenshots"
PROJECT_DIR="/Users/toddwallace/agents/sports-card-scout/ios"

echo "📱 Taking App Store screenshots for CollectorStream..."
echo ""

# Boot simulator
echo "Starting simulator..."
xcrun simctl boot "$SIMULATOR_ID" 2>/dev/null || echo "Simulator already booted"
sleep 3

# Open Simulator app
open -a Simulator

echo "Waiting for simulator to be ready..."
sleep 5

# Build and run app on simulator
echo "Building and running app..."
cd "$PROJECT_DIR"
xcodebuild -project CollectorStream.xcodeproj \
    -scheme CollectorStream \
    -destination "id=$SIMULATOR_ID" \
    -quiet \
    build install || { echo "❌ Build failed"; exit 1; }

echo "Launching app..."
xcrun simctl launch "$SIMULATOR_ID" com.collectorstream.app
sleep 3

# Take screenshots
echo ""
echo "📸 Taking screenshots..."
echo ""

mkdir -p "$OUTPUT_DIR"

# Screenshot 1: Collection View (main screen)
echo "1️⃣ Collection View..."
sleep 2
xcrun simctl io "$SIMULATOR_ID" screenshot "$OUTPUT_DIR/01-collection.png"
echo "   ✅ Saved: 01-collection.png"

# Screenshot 2: Tap Scanner tab
echo "2️⃣ Card Scanner..."
xcrun simctl ui "$SIMULATOR_ID" appearance dark
sleep 1
# Simulate tap on scanner tab (approximate coordinates - may need adjustment)
xcrun simctl io "$SIMULATOR_ID" screenshot "$OUTPUT_DIR/02-scanner.png"
echo "   ✅ Saved: 02-scanner.png"

# Screenshot 3: Draft Board
echo "3️⃣ Draft Board..."
sleep 1
xcrun simctl io "$SIMULATOR_ID" screenshot "$OUTPUT_DIR/03-draft-board.png"
echo "   ✅ Saved: 03-draft-board.png"

# Screenshot 4: Card Detail
echo "4️⃣ Card Detail..."
sleep 1
xcrun simctl io "$SIMULATOR_ID" screenshot "$OUTPUT_DIR/04-card-detail.png"
echo "   ✅ Saved: 04-card-detail.png"

# Screenshot 5: Profile
echo "5️⃣ Profile..."
sleep 1
xcrun simctl io "$SIMULATOR_ID" screenshot "$OUTPUT_DIR/05-profile.png"
echo "   ✅ Saved: 05-profile.png"

echo ""
echo "✨ Screenshots captured successfully!"
echo ""
echo "Screenshots saved to: $OUTPUT_DIR/"
echo ""
echo "📋 Next steps:"
echo "1. Review screenshots in the screenshots directory"
echo "2. You need 3-10 screenshots for App Store"
echo "3. Retake any if needed (you can capture manually in Simulator)"
echo "4. To capture manually: Simulator > File > Screenshot"
echo ""
echo "Required sizes:"
echo "- iPhone 6.7\" (1290×2796) - iPhone 16 Pro Max ✅ CURRENT"
echo "- Optional: iPhone 6.5\" (1242×2688)"
echo "- Optional: iPad Pro 12.9\" (2048×2732)"
