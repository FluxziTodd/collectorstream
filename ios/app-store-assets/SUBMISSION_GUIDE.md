# CollectorStream App Store Submission Guide

## ✅ Everything is Ready!

All assets have been generated and prepared. Follow these steps to submit your app.

---

## 📁 What's Been Created

All files are in: `/Users/toddwallace/agents/sports-card-scout/ios/app-store-assets/`

1. **App Icons** (`icons/` folder)
   - ✅ 1024x1024 (App Store)
   - ✅ 180x180, 120x120, 167x167, 152x152, 76x76 (various devices)

2. **Screenshots** (`screenshots/` folder)
   - ✅ 5 screenshots at 1290×2796 (iPhone 16 Pro Max size)
   - ✅ Collection, Scanner, Draft Board, Card Detail, Profile

3. **Privacy Policy**
   - ✅ File: `/Users/toddwallace/agents/sports-card-scout/privacy.html`
   - 📋 **ACTION NEEDED:** Upload to https://collectorstream.com/privacy

4. **Metadata Document**
   - ✅ File: `APP_STORE_METADATA.md`
   - Contains all text, descriptions, keywords ready to copy/paste

---

## 🚀 Step-by-Step Submission Process

### STEP 1: Upload Privacy Policy (5 minutes)

```bash
# Upload privacy.html to your website at:
https://collectorstream.com/privacy

# Verify it loads correctly in a browser
```

---

### STEP 2: Configure Code Signing in Xcode (10 minutes)

1. Open `CollectorStream.xcodeproj` in Xcode
2. Click on the project in navigator
3. Select "CollectorStream" target
4. Go to "Signing & Capabilities" tab
5. Check ✅ "Automatically manage signing"
6. Select your Apple Developer Team from dropdown
7. Bundle ID should be: `com.collectorstream.app`

**Troubleshooting:**
- If team not showing: Xcode > Settings > Accounts > Add your Apple ID
- If errors: Click "Download Manual Profiles"

---

### STEP 3: Add App Icons to Xcode (5 minutes)

1. In Xcode, open `Assets.xcassets` (in Project Navigator)
2. Click on `AppIcon`
3. Drag and drop icons from `app-store-assets/icons/` into correct slots:
   - 1024×1024 → App Store iOS slot
   - 180×180 → iPhone App iOS 60pt @3x
   - 120×120 → iPhone App iOS 60pt @2x
   - 167×167 → iPad Pro App iOS 83.5pt @2x
   - 152×152 → iPad App iOS 76pt @2x
   - 76×76 → iPad App iOS 76pt @1x

---

### STEP 4: Create Archive Build (15 minutes)

1. In Xcode menubar:
   - Product → Destination → **"Any iOS Device (arm64)"**

2. Create Archive:
   - Product → **Archive**
   - Wait for build (2-5 minutes)

3. In Organizer window (opens automatically):
   - Click **"Validate App"**
   - Select your certificate
   - Click **"Validate"**
   - Fix any errors if they appear

4. Upload to App Store:
   - Click **"Distribute App"**
   - Select **"App Store Connect"**
   - Click **"Upload"**
   - Check these options:
     - ✅ Upload symbols
     - ✅ Manage version/build
   - Click **"Upload"**
   - **Wait 10-30 minutes for processing**

---

### STEP 5: Create App in App Store Connect (20 minutes)

1. **Go to:** https://appstoreconnect.apple.com

2. **Click:** My Apps → + → New App

3. **Fill out New App form:**
   - Platform: iOS
   - Name: `CollectorStream`
   - Primary Language: English
   - Bundle ID: Select `com.collectorstream.app`
   - SKU: `collectorstream-ios-1`
   - User Access: Full Access
   - Click **Create**

4. **Go to App Information tab:**
   - Category:
     - Primary: `Sports`
     - Secondary: `Finance`
   - Privacy Policy URL: `https://collectorstream.com/privacy`
   - Click **Save**

5. **Go to Pricing and Availability:**
   - Price: Select **Free**
   - Availability: All countries
   - Click **Save**

---

### STEP 6: Fill Out Version 1.0 Information (30 minutes)

Still in App Store Connect, go to **1.0 Prepare for Submission** tab:

1. **Screenshots:**
   - Click **+ iPhone 6.7"**
   - Upload all 5 screenshots from `app-store-assets/screenshots/`
   - Order: 01, 02, 03, 04, 05

2. **Promotional Text:**
   ```
   Track your sports card collection with AI-powered valuations, market insights, and draft board analysis. Scan, organize, and invest smarter.
   ```

3. **Description:**
   Copy from `APP_STORE_METADATA.md` → Description section

4. **Keywords:**
   ```
   sports cards,trading cards,baseball,basketball,football,hockey,portfolio,collection,scanner,invest
   ```

5. **Support URL:**
   ```
   https://collectorstream.com/support
   ```

6. **Marketing URL:**
   ```
   https://collectorstream.com
   ```

7. **Build:**
   - Click **+** under "Build"
   - Select the build you uploaded (wait if still processing)

8. **App Icon:**
   - Upload `app-store-assets/icons/icon_1024x1024.png`

9. **Version:**
   - Version: `1.0`
   - Copyright: `2026 CollectorStream`

10. **Age Rating:**
    - Click **Edit**
    - Select all **"No"** (it's a family-friendly app)
    - Age: **4+**
    - Click **Done**

11. **App Review Information:**
    - Sign-in required: **Yes**
    - Demo Account:
      - Username: `demo@collectorstream.com`
      - Password: Create a strong password
      - **⚠️ Create this demo account in your backend!**

    - Contact Info:
      - First Name: [Your name]
      - Last Name: [Your name]
      - Phone: [Your phone]
      - Email: `support@collectorstream.com`

    - Notes: Copy from `APP_STORE_METADATA.md`

12. **Export Compliance:**
    - "Does your app use encryption?" → **No**
    - (HTTPS is exempt, and we set ITSAppUsesNonExemptEncryption = false)

---

### STEP 7: Submit for Review (2 minutes)

1. Review everything one more time
2. Click **"Add for Review"**
3. Click **"Submit to App Review"**
4. Confirm submission

---

## ⏱️ What Happens Next

**Timeline:**
- ✅ Uploaded (Done!)
- ⏳ Processing: 10-30 minutes
- ⏳ Waiting for Review: 1-2 days
- ⏳ In Review: 1-3 days
- 🎉 **Ready for Sale: ~3-7 days total**

**You'll receive emails:**
1. "Ready for Review" - Your app entered the review queue
2. "In Review" - Apple is testing your app
3. "Ready for Sale" 🎉 or "Rejected" (with feedback)

---

## 📋 Pre-Submission Checklist

Before submitting, verify:

- [ ] Privacy policy is live at https://collectorstream.com/privacy
- [ ] Demo account (`demo@collectorstream.com`) is created and working
- [ ] Demo account has some sample cards to showcase features
- [ ] App builds and runs on a real device (not just simulator)
- [ ] Camera permissions work correctly
- [ ] All screenshots uploaded (5 minimum)
- [ ] App icon uploaded (1024x1024)
- [ ] All metadata filled out
- [ ] Support URL works
- [ ] Build is selected in version

---

## 🚨 Common Issues & Solutions

### Build doesn't appear in App Store Connect
- **Wait:** Processing can take 30 minutes
- **Refresh:** Close and reopen App Store Connect
- **Check email:** Look for processing errors from Apple

### "Bundle ID already exists"
- Use: `com.collectorstream.app` (already configured)
- Or create new one: `com.yourcompany.collectorstream`
- Update in Xcode project settings if changed

### Code signing errors
- Xcode > Settings > Accounts > Download Manual Profiles
- Make sure you're logged in with Apple Developer account
- Certificate must be Distribution, not Development

### Screenshots wrong size
- Must be 1290×2796 for iPhone 6.7"
- Current screenshots are correct size ✅
- If needed, retake from iPhone 16 Pro Max simulator

### Privacy Policy required
- Upload `privacy.html` to your website
- Must be accessible at exact URL you provide
- Test in browser before submitting

---

## 🎯 Quick Start Commands

```bash
# 1. Review all generated assets
cd /Users/toddwallace/agents/sports-card-scout/ios/app-store-assets
open icons/
open screenshots/
open APP_STORE_METADATA.md

# 2. Upload privacy policy to your web server
# Upload privacy.html to https://collectorstream.com/privacy

# 3. Open Xcode to start submission process
cd /Users/toddwallace/agents/sports-card-scout/ios
open CollectorStream.xcodeproj

# 4. Open App Store Connect when ready
open https://appstoreconnect.apple.com
```

---

## 📞 Support

Need help? Check:
- [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [App Store Connect Help](https://developer.apple.com/help/app-store-connect/)
- Email me for issues with this specific submission

---

## 🎉 After Approval

Once approved:

1. **App goes live** (if auto-release selected)
2. **Get your App Store link:**
   ```
   https://apps.apple.com/app/collectorstream/id[YOUR_APP_ID]
   ```

3. **Promote it:**
   - Share on social media
   - Add to website
   - Email users
   - Consider App Store Search Ads

4. **Monitor:**
   - Check App Analytics in App Store Connect
   - Read user reviews
   - Respond to feedback
   - Plan next version!

---

Good luck! You've got everything you need. The submission process is straightforward when you have all assets ready (which you do!).

Expected timeline: **App live in 3-7 days** 🚀

Questions? Let me know!
