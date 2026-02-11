# CollectorStream

A comprehensive sports card collection management system with AI-powered card scanning, real-time market value tracking, and mock draft analysis.

## Project Structure

```
├── ios/                          # iOS Scanner App (Swift/SwiftUI)
│   ├── CollectorStream/          # Main app code
│   │   ├── Views/               # SwiftUI views
│   │   │   ├── Scanner/        # Camera scanner with AI identification
│   │   │   ├── Main/           # Collection, profile, draft boards
│   │   │   └── Auth/           # Authentication views
│   │   ├── Services/           # API client, authentication, card ID
│   │   ├── Models/             # Data models
│   │   ├── Theme/              # UI components and styling
│   │   └── Utils/              # Vision detection, blur detection
│   └── README.md               # iOS-specific documentation
│
├── api/                         # FastAPI Backend
│   ├── main.py                 # API server entry point
│   ├── auth.py                 # JWT authentication
│   ├── cards.py                # Card CRUD endpoints
│   ├── images.py               # Image upload handling
│   ├── admin.py                # Admin management endpoints
│   └── card_identifier.py      # Multi-model AI card identification
│
├── db/                          # Database models and utilities
│   ├── models.py               # SQLAlchemy models
│   └── normalize.py            # Data normalization
│
├── scrapers/                    # Mock draft scraping
│   ├── base.py                 # Base scraper class
│   ├── registry.py             # Scraper registry
│   ├── nfl/                    # NFL draft scrapers
│   └── nba/                    # NBA draft scrapers
│
├── analysis/                    # Analytics and reporting
│   ├── portfolio_tracker.py   # Portfolio performance analysis
│   ├── card_prices.py          # Price tracking
│   └── movers.py               # Price movement detection
│
├── integrated-dashboard.html    # Production web portal
├── portal/                      # Legacy portal (deprecated)
└── config/                      # Configuration files
    └── sources.yaml            # Mock draft sources

```

## Features

### iOS Scanner App
- **AI-Powered Card Scanning**: Uses multi-model AI (Claude, GPT-4, OpenRouter) for 90%+ accuracy
- **Real-time Card Detection**: Vision framework for automatic card boundary detection
- **Blur Detection**: Ensures high-quality scans before submission
- **Collection Management**: Browse, edit, and track your card collection
- **Market Value Tracking**: Real-time eBay market value integration
- **Authentication**: Secure JWT-based authentication with keychain storage

### Web Portal
- **Integrated Dashboard**: Single-page application with mock drafts and portfolio
- **Portfolio Management**: Visual card gallery with thumbnails
- **Performance Analytics**: Track ROI, profit/loss, top performers
- **Grouping & Filtering**: Group by sport, team, player, year
- **Admin Dashboard**: User management, admin controls, system stats
- **Password Reset**: Email reset links or set passwords directly

### Backend API
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Multi-Model AI**: Fallback chain across 5+ AI services for card identification
- **Image Storage**: Local uploads with S3/CloudFront-ready URLs
- **Market Value API**: eBay integration for real-time pricing
- **Admin Endpoints**: User/admin management, scraper controls

### Mock Draft Scraping
- **Multi-Sport Support**: NFL, NBA (expandable to MLB, NHL)
- **Automated Scraping**: Scheduled scraping from 15+ sources
- **Data Normalization**: Standardized player data across sources
- **Consensus Rankings**: Aggregated draft position predictions

## Tech Stack

- **iOS**: Swift 5.9+, SwiftUI, Vision Framework, Combine
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Uvicorn
- **Database**: PostgreSQL (production), SQLite (development)
- **AI Services**: Anthropic Claude, OpenAI GPT-4, OpenRouter
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Infrastructure**: AWS (S3, CloudFront, EC2), Nginx

## Getting Started

### iOS App Setup

```bash
cd ios
open CollectorStream.xcodeproj

# Update API base URL in Services/APIClient.swift if needed
# Run on simulator or device (iOS 17.0+)
```

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys:
# - ANTHROPIC_API_KEY (for Claude)
# - OPENAI_API_KEY (for GPT-4)
# - OPENROUTER_API_KEY (for free models)

# Run development server
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Web Portal Setup

```bash
# Portal is a static site - just open in browser or serve with:
python -m http.server 8080
# Open http://localhost:8080/integrated-dashboard.html

# Or deploy to S3:
aws s3 sync . s3://collectorstream-site/ --exclude "*" --include "*.html" --include "*.css" --include "*.js"
```

## API Endpoints

### Authentication
- `POST /v1/auth/register` - Register new user
- `POST /v1/auth/login` - Login (returns JWT token)
- `GET /v1/auth/validate` - Validate token

### Cards
- `GET /v1/cards` - List user's cards
- `POST /v1/cards` - Add new card
- `PUT /v1/cards/{id}` - Update card
- `DELETE /v1/cards/{id}` - Delete card
- `POST /v1/cards/{id}/market-value` - Refresh market value

### Card Identification
- `POST /v1/cards/identify` - AI card identification (multipart/form-data with front/back images)

### Admin
- `GET /v1/admin/users` - List all users
- `PUT /v1/admin/users/{id}` - Update user
- `DELETE /v1/admin/users/{id}` - Delete user
- `POST /v1/admin/users/{id}/reset-password` - Send password reset email
- `POST /v1/admin/users/{id}/set-password` - Set password directly
- `GET /v1/admin/admins` - List admins
- `POST /v1/admin/admins` - Add admin
- `DELETE /v1/admin/admins/{id}` - Remove admin
- `GET /v1/admin/stats` - System statistics

## Card Identification AI Models

The system uses a fallback chain for maximum reliability:

1. **CardSight API** (specialized sports card identifier)
2. **Claude 3.5 Sonnet** (Anthropic) - Most accurate
3. **GPT-4o** (OpenAI)
4. **OpenRouter Free Models**:
   - Llama 3.2 11B Vision
   - Gemini 2.0 Flash
   - Qwen 2 VL 7B
5. **Ximilar API** (computer vision backup)

Returns structured JSON with:
- Player name
- Team
- Year
- Set/manufacturer
- Card number
- Estimated value
- Confidence score

## Deployment

### Production Server (AWS EC2)
```bash
ssh -i ~/.ssh/vintagecar-key-fluxzi.pem ec2-user@13.216.187.156

# API runs as systemd service
sudo systemctl status collectorstream-api
sudo systemctl restart collectorstream-api

# Logs
sudo journalctl -u collectorstream-api -f

# Nginx config
sudo vim /etc/nginx/conf.d/collectorstream-api.conf
```

### CloudFront Deployment
```bash
# Deploy web portal
aws s3 cp integrated-dashboard.html s3://collectorstream-site/index.html --profile fluxzi

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id E26VWZLVN1SVFJ \
  --paths "/index.html" "/" \
  --profile fluxzi
```

## Environment Variables

Required environment variables in `.env`:

```bash
# API Keys (at least one required for card identification)
ANTHROPIC_API_KEY=sk-ant-api03-xxx
OPENAI_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-or-xxx

# Database
DATABASE_URL=postgresql://user:pass@localhost/collectorstream

# API Configuration
API_BASE_URL=https://api.collectorstream.com
JWT_SECRET_KEY=your-secret-key-here

# Image Storage
UPLOAD_DIR=/home/ec2-user/sports-card-scout/uploads
```

## iOS Scanner App Reusability

The iOS scanner can be easily adapted for other scanning applications:

### Key Reusable Components

1. **CameraScannerView.swift**: Complete camera interface with AVFoundation
2. **VisionCardDetector.swift**: Vision framework rectangle detection (adaptable to any document)
3. **BlurDetector.swift**: Blur detection for quality control
4. **CardIdentificationService.swift**: Multi-model AI service (swap prompts for different use cases)

### Adaptation Steps

1. Replace `CardIdentificationService` AI prompts with your use case
2. Update `Card` model with your data structure
3. Modify `APIClient` to point to your backend
4. Customize UI theme in `Theme/` directory
5. Update `Info.plist` with your app name and permissions

### Example Use Cases
- **Receipt Scanning**: OCR + expense categorization
- **Document Scanning**: ID cards, passports, contracts
- **Product Scanning**: Barcode + product lookup
- **Business Cards**: Contact extraction
- **Book Scanning**: ISBN + metadata lookup

## License

MIT License - feel free to reuse and adapt for your projects.

## Author

Built with Claude Code by Anthropic.
