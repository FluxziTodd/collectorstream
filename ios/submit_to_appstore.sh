#!/bin/bash

# CollectorStream App Store Submission Script
# This script automates the Xcode build and upload process

set -e  # Exit on error

PROJECT_DIR="/Users/toddwallace/agents/sports-card-scout/ios"
SCHEME="CollectorStream"
PROJECT="CollectorStream.xcodeproj"
BUNDLE_ID="com.collectorstream.app"
APPLE_ID="todd@fluxz.com"

cd "$PROJECT_DIR"

echo "🚀 CollectorStream App Store Submission"
echo "=========================================="
echo ""

# Step 1: Clean build folder
echo "1️⃣ Cleaning build folder..."
xcodebuild clean -project "$PROJECT" -scheme "$SCHEME" > /dev/null 2>&1
echo "   ✅ Build folder cleaned"
echo ""

# Step 2: Archive the app
echo "2️⃣ Creating archive build..."
echo "   This will take 2-5 minutes..."
xcodebuild archive \
    -project "$PROJECT" \
    -scheme "$SCHEME" \
    -destination "generic/platform=iOS" \
    -archivePath "./build/CollectorStream.xcarchive" \
    -configuration Release \
    CODE_SIGN_STYLE=Automatic \
    DEVELOPMENT_TEAM="" \
    2>&1 | grep -E "(succeeded|failed|error|warning)" || true

if [ ! -d "./build/CollectorStream.xcarchive" ]; then
    echo "   ❌ Archive failed!"
    echo ""
    echo "   This usually means:"
    echo "   1. You need to configure code signing in Xcode"
    echo "   2. Your Apple Developer account isn't set up"
    echo ""
    echo "   Quick fix:"
    echo "   1. Open Xcode"
    echo "   2. Open CollectorStream.xcodeproj"
    echo "   3. Select CollectorStream target"
    echo "   4. Go to 'Signing & Capabilities'"
    echo "   5. Select your team: $APPLE_ID"
    echo "   6. Run this script again"
    exit 1
fi

echo "   ✅ Archive created successfully!"
echo ""

# Step 3: Export IPA
echo "3️⃣ Exporting IPA for App Store..."
cat > ./build/ExportOptions.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>destination</key>
    <string>upload</string>
    <key>uploadSymbols</key>
    <true/>
    <key>uploadBitcode</key>
    <false/>
</dict>
</plist>
EOF

xcodebuild -exportArchive \
    -archivePath "./build/CollectorStream.xcarchive" \
    -exportPath "./build" \
    -exportOptionsPlist "./build/ExportOptions.plist" \
    2>&1 | grep -E "(succeeded|failed|error)" || true

if [ ! -f "./build/CollectorStream.ipa" ]; then
    echo "   ❌ Export failed - needs manual code signing setup"
    echo ""
    echo "   Please use Xcode to upload instead:"
    echo "   1. Open Xcode"
    echo "   2. Window → Organizer"
    echo "   3. Select the archive"
    echo "   4. Click 'Distribute App'"
    echo "   5. Follow the wizard"
    exit 1
fi

echo "   ✅ IPA exported successfully!"
echo ""

# Step 4: Validate
echo "4️⃣ Validating app..."
xcrun altool --validate-app \
    -f "./build/CollectorStream.ipa" \
    -t ios \
    -u "$APPLE_ID" \
    --password "@keychain:AC_PASSWORD" \
    2>&1 | tail -5

echo ""

# Step 5: Upload
echo "5️⃣ Uploading to App Store Connect..."
echo "   This may take 5-10 minutes..."
echo ""

xcrun altool --upload-app \
    -f "./build/CollectorStream.ipa" \
    -t ios \
    -u "$APPLE_ID" \
    --password "@keychain:AC_PASSWORD" \
    2>&1

echo ""
echo "✨ Upload complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Wait 10-30 minutes for processing"
echo "2. Go to https://appstoreconnect.apple.com"
echo "3. Select CollectorStream app"
echo "4. Select version 1.0"
echo "5. Click '+' under Build section"
echo "6. Select the uploaded build"
echo "7. Fill in all metadata (see APP_STORE_METADATA.md)"
echo "8. Upload screenshots from app-store-assets/screenshots/"
echo "9. Submit for review!"
echo ""
echo "Questions? Check SUBMISSION_GUIDE.md for detailed help."
echo ""
