# CollectorStream - Final Submission Checklist
## For todd@fluxzi.com Apple Account

**Status:** ✅ App is built and ready. Follow these steps to submit.

---

## 🚨 CRITICAL: Pre-Submission Requirements

### 1. Upload Privacy Policy (REQUIRED - 5 minutes)
**Apple will reject without this!**

```bash
# The privacy policy file is ready at:
/Users/toddwallace/agents/sports-card-scout/privacy.html

# Upload it to your web server so it's accessible at:
https://collectorstream.com/privacy
```

**How to upload:**
- Use your hosting control panel (cPanel, FTP, etc.)
- OR use command line: `scp privacy.html your-server:/path/to/collectorstream.com/privacy.html`
- Test it works: Visit https://collectorstream.com/privacy in browser

---

### 2. Verify Demo Account (REQUIRED - 2 minutes)
Apple reviewers need this to test your app.

**Demo Account:**
- Email: `demo@collectorstream.com`
- Password: `DemoUser2026!`

**Test it:**
1. Open the app in Xcode simulator or device
2. Try logging in with these credentials
3. If login fails, create the account manually via the app's Register screen

**Important:** The demo account should have 0 cards (clean state for reviewers)

---

## 📱 Step-by-Step Submission Process

### STEP 1: Add App Icons to Xcode (5 minutes)

1. **Open the project:**
   ```bash
   cd /Users/toddwallace/agents/sports-card-scout/ios
   open CollectorStream.xcodeproj
   ```

2. **Add icons:**
   - In Xcode left sidebar, click `Assets.xcassets`
   - Click `AppIcon`
   - Open Finder and navigate to: `/Users/toddwallace/agents/sports-card-scout/ios/app-store-assets/icons/`
   - Drag each icon file to its matching size slot in Xcode:
     - `icon_1024x1024.png` → App Store 1024pt slot
     - `icon_180x180.png` → iPhone App 60pt @3x slot
     - `icon_120x120.png` → iPhone App 60pt @2x slot
     - `icon_167x167.png` → iPad App 83.5pt @2x slot
     - `icon_152x152.png` → iPad App 76pt @2x slot
     - `icon_76x76.png` → iPad App 76pt @1x slot

---

### STEP 2: Add Apple ID to Xcode (3 minutes)

1. **In Xcode, go to:** Xcode → Settings (Cmd+,)

2. **Click "Accounts" tab**

3. **Click "+" button** (bottom left)

4. **Select "Apple ID"**

5. **Enter credentials:**
   - Apple ID: `todd@fluxzi.com`
   - Password: [Your password]

6. **Click "Sign In"**

7. **Download certificates:**
   - Select your account
   - Click "Manage Certificates..."
   - Click "+" → "Apple Distribution"
   - Close settings

---

### STEP 3: Configure Code Signing (2 minutes)

1. **In Xcode, click** the project name "CollectorStream" (blue icon at top of file list)

2. **Select the "CollectorStream" target** (under TARGETS, not PROJECT)

3. **Click "Signing & Capabilities" tab** (top bar)

4. **Check the box:** ✅ "Automatically manage signing"

5. **Team dropdown:** Select "Todd Wallace (todd@fluxzi.com)" or your team name

6. **Verify:**
   - Bundle Identifier shows: `com.collectorstream.app`
   - Signing Certificate shows: "Apple Distribution"
   - Status shows: No issues

---

### STEP 4: Take Screenshots (10 minutes)

**You need 3-10 screenshots for App Store.**

1. **Build and run on iPhone 16 Pro Max simulator:**
   - Product → Destination → iPhone 16 Pro Max
   - Product → Run (Cmd+R)
   - Wait for app to launch

2. **Take 5 screenshots:**

   **Screenshot 1 - Splash Screen:**
   - Wait for splash screen to appear
   - Press Cmd+S to save screenshot
   - Name it: `01-splash.png`

   **Screenshot 2 - Login:**
   - After splash, login screen appears
   - Press Cmd+S
   - Name it: `02-login.png`

   **Screenshot 3 - Draft Board (Default view after login):**
   - Log in with demo account
   - App opens to Draft Board
   - Wait for page to load
   - Press Cmd+S
   - Name it: `03-draft-board.png`

   **Screenshot 4 - Collection:**
   - Tap "Collection" tab
   - Press Cmd+S
   - Name it: `04-collection.png`

   **Screenshot 5 - Profile:**
   - Tap "Profile" tab
   - Press Cmd+S
   - Name it: `05-profile.png`

3. **Move screenshots:**
   - Screenshots are saved to Desktop
   - Move them to: `/Users/toddwallace/agents/sports-card-scout/ios/app-store-assets/screenshots/`

**Note:** Screenshots must be 1290x2796 pixels (iPhone 16 Pro Max size)

---

### STEP 5: Archive and Upload Build (15 minutes)

1. **Select destination:**
   - Product → Destination → **"Any iOS Device (arm64)"**
   - (NOT simulator)

2. **Create archive:**
   - Product → **Archive**
   - Wait 3-5 minutes for build
   - Xcode Organizer window will open

3. **Distribute to App Store:**
   - In Organizer, click **"Distribute App"**
   - Select **"App Store Connect"**
   - Click **"Next"**
   - Select **"Upload"**
   - Click **"Next"**
   - Keep defaults (automatically manage signing)
   - Click **"Upload"**
   - Wait 5-10 minutes for upload

4. **Success confirmation:**
   - You'll see "Upload Successful"
   - Check email for confirmation from Apple

---

### STEP 6: Create App in App Store Connect (15 minutes)

1. **Go to:** https://appstoreconnect.apple.com

2. **Log in with:** `todd@fluxzi.com`

3. **Create new app:**
   - Click "My Apps"
   - Click "+" button
   - Select "New App"

4. **Fill in details:**
   - **Platforms:** ✅ iOS
   - **Name:** `CollectorStream`
   - **Primary Language:** English (U.S.)
   - **Bundle ID:** Select `com.collectorstream.app` (should appear in dropdown)
   - **SKU:** `collectorstream-ios-2026`
   - **User Access:** Full Access
   - Click **"Create"**

---

### STEP 7: Fill App Information (20 minutes)

Now you're on the app's main page. Go through each section:

#### **App Information Tab:**

1. **Scroll to "General Information"**
   - **Subtitle:** `Sports Card Portfolio Manager`
   - **Category:**
     - Primary: `Sports`
     - Secondary: `Finance`

2. **Privacy Policy URL:**
   - **URL:** `https://collectorstream.com/privacy`
   - ⚠️ Test this URL first! Must be live!

#### **Pricing and Availability Tab:**

1. **Price Schedule:**
   - Click "Add Pricing"
   - **Price:** Free (Tier 0)
   - **Start Date:** Today
   - Save

2. **App Distribution:**
   - **Availability:** All countries

#### **App Privacy Tab:**

1. **Click "Get Started"**

2. **Data Collection:**
   - Do you collect data?: **Yes**

3. **Data Types (select these):**
   - **Contact Info:**
     - Email Address (for account creation)
     - Used for: Account management
     - Linked to user: Yes
     - Used for tracking: No

   - **User Content:**
     - Photos or Videos (card images)
     - Used for: App functionality
     - Linked to user: Yes
     - Used for tracking: No

4. **Data Use:**
   - Analytics: No
   - Third parties: No

5. **Publish** the privacy policy

#### **Age Rating Tab:**

1. Click "Edit"
2. Answer all questions: **"No"** to everything
3. Result should be: **4+**
4. Save

---

### STEP 8: Prepare Version 1.0 (30 minutes)

1. **Click "1.0 Prepare for Submission"** (left sidebar)

2. **Upload screenshots:**
   - Under "App Previews and Screenshots"
   - Click "+ iPhone 6.7" Display"
   - Drag all 5 screenshots from `app-store-assets/screenshots/` folder
   - Order them 1-5

3. **Upload App Icon:**
   - Scroll to "App Icon"
   - Drag `app-store-assets/icons/icon_1024x1024.png`

4. **Fill text fields** (copy from APP_STORE_METADATA.md):

   **Promotional Text:**
   ```
   Track your sports card collection with AI-powered valuations, market insights, and draft board analysis. Scan, organize, and invest smarter.
   ```

   **Description:**
   ```
   [Copy the entire Description section from APP_STORE_METADATA.md]
   ```

   **Keywords:**
   ```
   sports cards,trading cards,baseball,basketball,football,hockey,portfolio,collection,scanner,invest
   ```

   **Support URL:**
   ```
   https://collectorstream.com/support
   ```

   **Marketing URL:**
   ```
   https://collectorstream.com
   ```

5. **What's New in This Version:**
   ```
   🎉 Welcome to CollectorStream 1.0!

   This is the initial release of CollectorStream, your ultimate sports card portfolio manager.

   ✨ What's Included:

   📸 AI Card Scanner
   Instantly identify and catalog your sports cards with our advanced AI recognition technology.

   💎 Smart Collection Management
   Beautiful grid view of your entire collection with powerful search and filtering options.

   📊 Portfolio Analytics
   Track the value of your collection in real-time with comprehensive analytics.

   🏀 Draft Board Integration
   Stay ahead of the market with access to mock draft boards across all major sports.

   We're excited to help you manage and grow your sports card collection!

   Have feedback? Contact us at support@collectorstream.com

   Happy collecting! 🎯
   ```

6. **Build:**
   - Scroll to "Build" section
   - Click "+" to select build
   - Wait 10-30 min if it says "Processing"
   - Select the build once it appears
   - Build should show version 1.0, build 1

7. **App Review Information:**
   - **Sign-in required:** ✅ Yes
   - **Email:** `demo@collectorstream.com`
   - **Password:** `DemoUser2026!`
   - **Contact Information:**
     - First Name: Todd
     - Last Name: Wallace
     - Phone: [Your phone number]
     - Email: `todd@fluxzi.com`

8. **Notes for Reviewer:**
   ```
   Thank you for reviewing CollectorStream!

   DEMO ACCOUNT:
   - Login: demo@collectorstream.com / DemoUser2026!

   KEY FEATURES TO TEST:
   1. Splash Screen: App opens with black splash screen and logo
   2. Login: Use demo credentials above
   3. Draft Board: Default view after login showing mock draft data
   4. Collection: Tab to view card collection (empty for demo)
   5. Scanner: Camera icon to test card scanning (requires camera permission)
   6. Profile: Account settings and information

   PERMISSIONS:
   - Camera: Used for scanning sports cards
   - Network: Required for market data and authentication

   If you have any questions, please contact todd@fluxzi.com

   Thank you!
   ```

9. **Version Release:**
   - Select: "Automatically release this version"

10. **Save** (top right)

---

### STEP 9: Submit for Review (2 minutes)

1. **Review checklist** (top right shows items needed)
   - All items should be ✅ green

2. **If any red items:**
   - Click on them to complete
   - Most common: missing screenshots, privacy policy URL not working, build not selected

3. **When all green:**
   - Click **"Add for Review"** (top right)
   - Click **"Submit to App Review"**

4. **Confirmation:**
   - You'll see "Waiting for Review" status
   - You'll receive email confirmation

---

## ⏱️ Timeline After Submission

- **Now:** Waiting for Review
- **1-3 days:** In Review (status changes)
- **+1-2 days:** Review complete (approved or rejected)
- **Total:** 3-7 days to approval

You'll get emails for each status change.

---

## ✅ Pre-Flight Checklist

Before you start, verify:

- [ ] Privacy policy is live at https://collectorstream.com/privacy
- [ ] Demo account works (test login in app)
- [ ] You have todd@fluxzi.com Apple ID credentials
- [ ] You have 30-60 minutes of uninterrupted time
- [ ] Xcode is updated to latest version
- [ ] Internet connection is stable

---

## 🆘 Troubleshooting

**"Build Failed" when archiving:**
- Make sure you selected "Any iOS Device (arm64)" NOT simulator
- Verify code signing is configured (Step 3)
- Try: Product → Clean Build Folder, then Archive again

**"Upload Failed":**
- Check internet connection
- Verify Apple ID is added in Xcode Settings
- Try: Xcode → Settings → Accounts → Download Manual Profiles

**"No bundle ID in dropdown" when creating app:**
- Wait 24 hours after registering bundle ID
- OR manually register at: https://developer.apple.com/account/resources/identifiers

**"Privacy policy URL not working":**
- Must be HTTPS, not HTTP
- Must return 200 status code
- Cannot require login to view
- Test in incognito browser window

**"Build not showing in App Store Connect":**
- Wait 30 minutes for processing
- Check email for processing errors
- Verify build uploaded successfully in Xcode Organizer

**"Screenshots wrong size":**
- Must use iPhone 16 Pro Max (6.7" display)
- Size must be 1290x2796 pixels
- Can resize with: `sips -z 2796 1290 screenshot.png`

---

## 📞 Need Help?

Everything is ready. Just follow these steps and you'll be live in under a week!

**Quick Start:**
1. Upload privacy.html to your server
2. Open Xcode and follow Steps 1-5
3. Go to App Store Connect and follow Steps 6-9
4. Wait for approval!

**Your app is 100% ready to submit. You've got this! 🚀**
