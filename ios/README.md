# CollectorStream iOS App

A native iOS app for scanning and managing your sports card collection, integrated with CollectorStream.com.

## Features

### Card Scanning
- **Camera-based scanning** with real-time edge detection using Apple Vision framework
- **Front and back capture** for complete card documentation
- **Automatic card identification** using AI (Ximilar API integration)
- **OCR text extraction** for player names, card numbers, and metadata
- **Grading recognition** for PSA, BGS, SGC, CGC graded cards

### Collection Management
- **Cloud sync** with CollectorStream.com portal
- **Multi-sport support**: WNBA, NBA, NFL, MLB, NHL
- **Estimated values** and purchase price tracking
- **Gain/loss calculations** for your collection
- **Search and filter** by sport, player, team, year

### Draft Boards
- **Embedded web view** showing CollectorStream draft boards
- **Sport and year selection** for all supported leagues
- **Stay up-to-date** on prospect rankings

### User Account
- **Secure authentication** with collectorstream.com
- **Account creation** from within the app
- **Password reset** functionality
- **Keychain storage** for secure token management

## Requirements

- iOS 16.0+
- Xcode 15.0+
- Swift 5.9+
- Device with camera (for card scanning)

## Installation

1. Open `CollectorStream.xcodeproj` in Xcode
2. Select your development team in Signing & Capabilities
3. Build and run on a physical device (camera required)

## Architecture

```
CollectorStream/
├── App/
│   ├── CollectorStreamApp.swift    # App entry point
│   ├── ContentView.swift           # Root view with auth routing
│   └── Info.plist                  # App configuration
├── Theme/
│   ├── Theme.swift                 # Design system (colors, typography)
│   └── Components.swift            # Reusable UI components
├── Services/
│   ├── AuthManager.swift           # Authentication state management
│   ├── APIClient.swift             # REST API client
│   ├── KeychainService.swift       # Secure token storage
│   └── CardIdentificationService.swift  # Vision + AI identification
├── Models/
│   └── Card.swift                  # Card model and CardStore
└── Views/
    ├── Auth/
    │   └── AuthenticationView.swift  # Login, register, password reset
    ├── Main/
    │   ├── MainTabView.swift         # Tab bar navigation
    │   ├── CollectionView.swift      # Card grid with filters
    │   ├── CardDetailView.swift      # Card detail and edit
    │   ├── DraftBoardView.swift      # Embedded draft boards
    │   └── ProfileView.swift         # User profile and settings
    └── Scanner/
        ├── ScanCardView.swift        # Scanning flow coordinator
        ├── CardScannerViewModel.swift # Scanning state management
        └── CameraScannerView.swift   # Camera preview with guides
```

## Design System

The app uses CollectorStream's dark theme with emerald accent:

| Token | Value | Usage |
|-------|-------|-------|
| `bgPrimary` | `#0a0a0a` | Main background |
| `bgSecondary` | `#111111` | Secondary background |
| `bgCard` | `#151515` | Card containers |
| `accent` | `#10b981` | Primary accent (emerald) |
| `accentDark` | `#059669` | Darker accent |
| `textPrimary` | `#ffffff` | Primary text |
| `textSecondary` | `#9ca3af` | Secondary text |

## API Integration

### Backend API
The app communicates with `https://api.collectorstream.com/v1`:

- `POST /auth/login` - User login
- `POST /auth/register` - Account creation
- `POST /auth/reset-password` - Password reset
- `GET /auth/validate` - Token validation
- `GET /cards` - Fetch user's collection
- `POST /cards` - Add new card
- `PUT /cards/:id` - Update card
- `DELETE /cards/:id` - Delete card
- `POST /cards/identify` - AI card identification
- `POST /images/upload` - Image upload

### Card Identification
The identification pipeline:

1. **Vision Framework** - Edge detection and OCR
2. **Backend API** - Sends image to Ximilar for identification
3. **Result Processing** - Extracts player, team, year, set, value

## Card Scanning Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Ready     │────▶│   Scan      │────▶│   Review    │
│   State     │     │   Front     │     │   Front     │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Card      │◀────│  Processing │◀────│   Review    │
│  Identified │     │   (AI)      │     │   Back      │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│   Add to    │
│  Collection │
└─────────────┘
```

## Environment Variables

For local development, set these in your scheme:

```
XIMILAR_API_KEY=your_api_key_here
API_BASE_URL=https://api.collectorstream.com/v1
```

## Future Enhancements

### Machine Learning
- [ ] Train custom Core ML model on sports card dataset
- [ ] On-device classification for faster identification
- [ ] Card condition grading using computer vision
- [ ] Continuous learning from user corrections

### Features
- [ ] Barcode/QR code scanning for graded slabs
- [ ] Batch scanning mode for multiple cards
- [ ] AR card display and comparison
- [ ] Price alerts and market tracking
- [ ] Social sharing of collection highlights
- [ ] Import from CSV/other platforms

### Technical
- [ ] Offline mode with local storage
- [ ] Background sync
- [ ] Push notifications for price changes
- [ ] Widget for collection value

## License

Proprietary - CollectorStream

## Support

For support, visit [collectorstream.com](https://collectorstream.com) or contact support@collectorstream.com.
