"""Generate the CollectorStream landing page."""

from datetime import datetime
from html import escape as html_escape
from pathlib import Path

from .styles import CSS_LANDING

# SVG Icons
ICONS = {
    'lightning': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    'radar': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/><path d="M12 2a10 10 0 0 1 7.07 17.07"/><circle cx="12" cy="12" r="2"/></svg>',
    'target': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    'bell': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    'chart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    'trending': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    'portfolio': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    'users': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    'arrow_right': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    'arrow_up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>',
    'arrow_down': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>',
    'info': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
}

# League Logos - Stylized versions
LEAGUE_LOGOS = {
    # WNBA - Basketball with W
    'wnba': '''<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="24" cy="24" r="22" fill="#ff6b35"/>
        <ellipse cx="24" cy="24" rx="22" ry="8" stroke="#fff" stroke-width="2" fill="none"/>
        <path d="M24 2 L24 46" stroke="#fff" stroke-width="2"/>
        <path d="M8 18 L14 30 L20 18 L26 30 L32 18 L38 30 L44 18" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>''',
    # NBA - Basketball silhouette
    'nba': '''<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="44" height="44" rx="6" fill="#1d428a"/>
        <circle cx="24" cy="24" r="16" stroke="#fff" stroke-width="2" fill="none"/>
        <path d="M24 8 L24 40" stroke="#fff" stroke-width="1.5"/>
        <ellipse cx="24" cy="24" rx="16" ry="6" stroke="#fff" stroke-width="1.5" fill="none"/>
        <circle cx="32" cy="16" r="3" fill="#c8102e"/>
        <path d="M18 20 Q24 28 30 20" stroke="#fff" stroke-width="2" fill="none"/>
    </svg>''',
    # NFL - Football shape with laces
    'nfl': '''<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="44" height="44" rx="6" fill="#013369"/>
        <ellipse cx="24" cy="24" rx="18" ry="10" fill="#8B4513" stroke="#fff" stroke-width="1.5"/>
        <path d="M24 14 L24 34" stroke="#fff" stroke-width="2"/>
        <path d="M20 17 L28 17" stroke="#fff" stroke-width="1.5"/>
        <path d="M20 21 L28 21" stroke="#fff" stroke-width="1.5"/>
        <path d="M20 27 L28 27" stroke="#fff" stroke-width="1.5"/>
        <path d="M20 31 L28 31" stroke="#fff" stroke-width="1.5"/>
        <path d="M19 24 L29 24" stroke="#fff" stroke-width="1.5"/>
    </svg>''',
    # MLB - Baseball with seams
    'mlb': '''<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="44" height="44" rx="6" fill="#002d72"/>
        <circle cx="24" cy="24" r="16" fill="#fff"/>
        <path d="M12 18 Q18 24 12 30" stroke="#bf0d3e" stroke-width="2" fill="none"/>
        <path d="M36 18 Q30 24 36 30" stroke="#bf0d3e" stroke-width="2" fill="none"/>
        <path d="M14 16 L16 18" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M14 20 L16 22" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M14 28 L16 26" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M14 32 L16 30" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M34 16 L32 18" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M34 20 L32 22" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M34 28 L32 26" stroke="#bf0d3e" stroke-width="1.5"/>
        <path d="M34 32 L32 30" stroke="#bf0d3e" stroke-width="1.5"/>
    </svg>''',
    # NHL - Hockey puck and stick
    'nhl': '''<svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="2" y="2" width="44" height="44" rx="6" fill="#111"/>
        <ellipse cx="24" cy="30" rx="14" ry="6" fill="#333" stroke="#fff" stroke-width="1.5"/>
        <ellipse cx="24" cy="28" rx="14" ry="6" fill="#222"/>
        <path d="M10 12 L22 28" stroke="#8B4513" stroke-width="4" stroke-linecap="round"/>
        <path d="M22 28 L20 32 L26 28" stroke="#8B4513" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <circle cx="36" cy="14" r="5" fill="#111" stroke="#fff" stroke-width="1.5"/>
    </svg>''',
}


def generate_landing_page(output_dir, picks_data=None):
    """Generate the main landing page."""

    # Sample data for demonstration (will be replaced with real data)
    if not picks_data:
        picks_data = [
            {"rank": 1, "name": "JuJu Watkins", "pos": "G", "sport": "WNBA", "mock": "#1", "mock_change": 0, "price": "$125.00", "price_7d": "+8.7%", "signal": "Strong Buy"},
            {"rank": 2, "name": "Paige Bueckers", "pos": "G", "sport": "WNBA", "mock": "#2", "mock_change": 1, "price": "$89.00", "price_7d": "+5.2%", "signal": "Buy"},
            {"rank": 3, "name": "Lauren Betts", "pos": "C", "sport": "WNBA", "mock": "#3", "mock_change": 2, "price": "$45.00", "price_7d": "+3.1%", "signal": "Strong Buy"},
            {"rank": 4, "name": "Azzi Fudd", "pos": "G", "sport": "WNBA", "mock": "#4", "mock_change": 0, "price": "$62.00", "price_7d": "+1.8%", "signal": "Hold"},
            {"rank": 5, "name": "Awa Fam", "pos": "F", "sport": "WNBA", "mock": "#5", "mock_change": 3, "price": "$28.00", "price_7d": "+12.4%", "signal": "Strong Buy"},
            {"rank": 6, "name": "Flau'Jae Johnson", "pos": "G", "sport": "WNBA", "mock": "#6", "mock_change": -1, "price": "$35.00", "price_7d": "-2.1%", "signal": "Hold"},
        ]

    # Ticker data
    ticker_items = [
        {"sport": "WNBA", "name": "JuJu Watkins", "pos": "G", "mock": "+2", "price": "$125.00"},
        {"sport": "WNBA", "name": "Paige Bueckers", "pos": "G", "mock": "+1", "price": "$89.00"},
        {"sport": "WNBA", "name": "Lauren Betts", "pos": "C", "mock": "+3", "price": "$45.00"},
        {"sport": "WNBA", "name": "Azzi Fudd", "pos": "G", "mock": "—", "price": "$62.00"},
        {"sport": "WNBA", "name": "Awa Fam", "pos": "F", "mock": "+5", "price": "$28.00"},
        {"sport": "WNBA", "name": "Flau'Jae Johnson", "pos": "G", "mock": "-2", "price": "$35.00"},
    ]

    # Build ticker HTML
    ticker_html = ""
    for item in ticker_items * 3:  # Repeat for smooth scrolling
        mock_class = "down" if item["mock"].startswith("-") else ""
        ticker_html += f'''
        <div class="ticker-item">
            <span class="ticker-sport">{item["sport"]}</span>
            <span class="ticker-name">{item["name"]}</span>
            <span class="ticker-pos">{item["pos"]}</span>
            <span class="ticker-mock {mock_class}">Mock: {item["mock"]}</span>
            <span class="ticker-price">{item["price"]}</span>
        </div>'''

    # Build picks table rows
    picks_rows = ""
    for p in picks_data:
        mock_change_html = ""
        if p["mock_change"] > 0:
            mock_change_html = f'<span class="mock-change up">{ICONS["trending"]} +{p["mock_change"]}</span>'
        elif p["mock_change"] < 0:
            mock_change_html = f'<span class="mock-change down">{ICONS["arrow_down"]} {p["mock_change"]}</span>'
        else:
            mock_change_html = '<span class="mock-change">— —</span>'

        price_class = "positive" if p["price_7d"].startswith("+") else "negative"

        signal_class = {
            "Strong Buy": "signal-strong-buy",
            "Buy": "signal-buy",
            "Hold": "signal-hold",
            "Sell": "signal-sell",
        }.get(p["signal"], "signal-hold")

        picks_rows += f'''
        <tr>
            <td>{p["rank"]}</td>
            <td>
                <div class="player-cell">
                    <span class="player-cell-name">{html_escape(p["name"])}</span>
                    <span class="player-cell-pos">{p["pos"]}</span>
                </div>
            </td>
            <td><span class="sport-badge">{p["sport"]}</span></td>
            <td>{p["mock"]}</td>
            <td>{mock_change_html}</td>
            <td>{p["price"]}</td>
            <td><span class="price-change {price_class}">{p["price_7d"]}</span></td>
            <td><span class="signal-badge {signal_class}">{p["signal"]}</span></td>
        </tr>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CollectorStream — Know Who to Buy Before the Market Moves</title>
    <meta name="description" content="Predictive intelligence for sports card investors. We aggregate mock drafts, scouting reports, and real-time card prices to find breakout players early.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{CSS_LANDING}</style>
</head>
<body>
    <div class="top-bar"></div>

    <!-- Header -->
    <header class="header">
        <a href="/" class="logo">
            {ICONS["lightning"]}
            <span>Collector</span><span>Stream</span>
        </a>
        <nav class="nav-links">
            <a href="#how-it-works">How It Works</a>
            <a href="#features">Features</a>
            <a href="#picks">Today's Picks</a>
            <a href="#draft-gap">The Draft Gap</a>
        </nav>
        <div class="nav-auth" id="navAuth">
            <a href="login.html" class="btn btn-ghost">Sign In</a>
            <a href="signup.html" class="btn btn-primary">Sign Up Free</a>
        </div>
        <div class="nav-auth nav-auth-loggedin" id="navAuthLoggedIn" style="display: none;">
            <a href="portfolio.html" class="btn btn-ghost">Portfolio</a>
            <a href="profile.html" class="profile-btn" title="Account settings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            </a>
        </div>
    </header>

    <!-- League Selector - Primary Navigation -->
    <section class="league-selector" id="sports">
        <div class="league-selector-inner">
            <h2>Choose Your League & Draft Year</h2>
            <p class="league-subtitle">Track prospects, mock drafts, and card prices across all major sports</p>

            <div class="league-grid">
                <!-- WNBA -->
                <div class="league-card league-wnba">
                    <div class="league-header">
                        <div class="league-logo">{LEAGUE_LOGOS["wnba"]}</div>
                        <div class="league-info">
                            <h3>WNBA</h3>
                            <span>Women's Basketball</span>
                        </div>
                    </div>
                    <div class="year-buttons">
                        <a href="players-2026.html" class="year-btn year-btn-primary">2026</a>
                        <a href="players-2027.html" class="year-btn">2027</a>
                        <a href="players-2028.html" class="year-btn">2028</a>
                        <a href="players-2029.html" class="year-btn">2029</a>
                        <a href="players-2030.html" class="year-btn">2030</a>
                    </div>
                </div>

                <!-- NBA -->
                <div class="league-card league-nba">
                    <div class="league-header">
                        <div class="league-logo">{LEAGUE_LOGOS["nba"]}</div>
                        <div class="league-info">
                            <h3>NBA</h3>
                            <span>Men's Basketball</span>
                        </div>
                    </div>
                    <div class="year-buttons">
                        <a href="nba-players-2026.html" class="year-btn year-btn-primary">2026</a>
                        <a href="nba-players-2027.html" class="year-btn">2027</a>
                        <a href="nba-players-2028.html" class="year-btn">2028</a>
                    </div>
                </div>

                <!-- NFL -->
                <div class="league-card league-nfl">
                    <div class="league-header">
                        <div class="league-logo">{LEAGUE_LOGOS["nfl"]}</div>
                        <div class="league-info">
                            <h3>NFL</h3>
                            <span>Football</span>
                        </div>
                    </div>
                    <div class="year-buttons">
                        <a href="nfl-players-2026.html" class="year-btn year-btn-primary">2026</a>
                        <a href="nfl-players-2027.html" class="year-btn">2027</a>
                    </div>
                </div>

                <!-- MLB -->
                <div class="league-card league-mlb">
                    <div class="league-header">
                        <div class="league-logo">{LEAGUE_LOGOS["mlb"]}</div>
                        <div class="league-info">
                            <h3>MLB</h3>
                            <span>Baseball</span>
                        </div>
                    </div>
                    <div class="year-buttons">
                        <a href="mlb-players-2026.html" class="year-btn year-btn-primary">2026</a>
                        <a href="mlb-players-2027.html" class="year-btn">2027</a>
                    </div>
                </div>

                <!-- NHL -->
                <div class="league-card league-nhl">
                    <div class="league-header">
                        <div class="league-logo">{LEAGUE_LOGOS["nhl"]}</div>
                        <div class="league-info">
                            <h3>NHL</h3>
                            <span>Hockey</span>
                        </div>
                    </div>
                    <div class="year-buttons">
                        <a href="nhl-players-2026.html" class="year-btn year-btn-primary">2026</a>
                        <a href="nhl-players-2027.html" class="year-btn">2027</a>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Hero - Now secondary -->
    <section class="hero hero-compact">
        <div class="hero-content">
            <div class="hero-badge">
                {ICONS["info"]}
                Predictive intelligence for card investors
            </div>
            <h1>Know Who to Buy <span class="highlight">Before the Market Moves</span></h1>
            <p class="hero-subtitle">
                We aggregate mock drafts, scouting reports, and real-time card prices to find breakout players early — and tell you when to sell before the hype fades.
            </p>
            <div class="hero-stats">
                <div class="hero-stat">
                    <div class="hero-stat-value">100+</div>
                    <div class="hero-stat-label">MOCK DRAFTS TRACKED</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-value">Daily</div>
                    <div class="hero-stat-label">BUY / SELL SIGNALS</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-value">Free</div>
                    <div class="hero-stat-label">PORTFOLIO TRACKING</div>
                </div>
            </div>
        </div>
    </section>

    <!-- Ticker -->
    <div class="ticker-container">
        <div class="ticker">
            {ticker_html}
        </div>
    </div>

    <!-- How It Works -->
    <section class="section" id="how-it-works">
        <div class="section-label">HOW IT WORKS</div>
        <h2 class="section-title">From Mock Draft to Smart Trade</h2>
        <p class="section-subtitle">
            CollectorStream turns publicly available scouting data into actionable buy and sell signals — so you're always a step ahead.
        </p>

        <div class="how-it-works">
            <div class="step-card">
                <div class="step-icon">{ICONS["radar"]}</div>
                <h3>We Scan the Noise</h3>
                <p>Our engine monitors 100+ mock drafts, scouting reports, combine results, and social buzz daily across NFL, NBA, and MLB prospects.</p>
            </div>
            <div class="step-card">
                <div class="step-icon">{ICONS["target"]}</div>
                <h3>We Find the Gap</h3>
                <p>We compare each player's rising draft stock against their current card prices to identify the "Draft Gap" — the window where cards are still undervalued.</p>
            </div>
            <div class="step-card">
                <div class="step-icon">{ICONS["bell"]}</div>
                <h3>You Buy & Sell Smarter</h3>
                <p>Get clear Buy and Sell signals based on real data. Buy early before the market catches on, and sell at peak hype moments like Draft Day or breakout games.</p>
            </div>
        </div>
    </section>

    <!-- Today's Picks -->
    <section class="section" id="picks">
        <div class="section-label">TODAY'S PICKS</div>
        <h2 class="section-title">Top Prospects to Watch</h2>
        <p class="section-subtitle">
            Players with the biggest gap between mock draft momentum and current card prices. Updated daily.
        </p>

        <div class="picks-table-container">
            <table class="picks-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Player</th>
                        <th>Sport</th>
                        <th>Avg Mock</th>
                        <th>Mock Δ</th>
                        <th>Floor Price</th>
                        <th>7D Price</th>
                        <th>Signal</th>
                    </tr>
                </thead>
                <tbody>
                    {picks_rows}
                </tbody>
            </table>
        </div>
        <p style="text-align: center; color: var(--text-muted); font-size: 13px; margin-top: 16px;">
            Mock data for demonstration · <a href="login.html" style="color: var(--accent);">Sign up free</a> to see live signals
        </p>
    </section>

    <!-- Draft Gap -->
    <section class="section" id="draft-gap">
        <div class="section-label">THE DRAFT GAP</div>
        <h2 class="section-title">When Draft Hype Outpaces Card Prices — That's Your Window</h2>
        <p class="section-subtitle">
            This chart shows a typical "Draft Gap" pattern: a player's mock draft stock rises weeks before card prices catch up. We find these gaps every day.
        </p>

        <div class="chart-container">
            <div class="chart-header">
                <div>
                    <div class="chart-title">Example: Rising WNBA Prospect</div>
                    <div class="chart-subtitle">Mock rank vs. card floor price over 12 weeks</div>
                </div>
                <div class="chart-legend">
                    <div class="legend-item"><span class="legend-dot mock"></span> Mock Rank (inverted)</div>
                    <div class="legend-item"><span class="legend-dot price"></span> Card Price</div>
                </div>
            </div>
            <div class="buy-window-alert">
                {ICONS["lightning"]}
                <strong>Buy Window</strong> Weeks 2-5: Mock rank climbing fast, card price still flat — the ideal entry point.
            </div>
            <div style="height: 200px; display: flex; align-items: flex-end; justify-content: space-around; padding: 20px; border: 1px solid var(--border); border-radius: 8px;">
                <!-- Simple CSS chart visualization -->
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 30px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W1</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 35px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W2</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 40px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W3</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 50px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W4</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 70px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W5</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 90px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W6</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 110px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W7</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 130px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W8</span>
                </div>
                <div style="display: flex; flex-direction: column; align-items: center; gap: 8px;">
                    <div style="width: 40px; height: 150px; background: var(--accent); border-radius: 4px;"></div>
                    <span style="font-size: 11px; color: var(--text-muted);">W9</span>
                </div>
            </div>
        </div>
    </section>

    <!-- Features -->
    <section class="section" id="features">
        <h2 class="section-title">Predictive Tools for Smarter Collecting</h2>
        <p class="section-subtitle">
            Everything you need to find undervalued prospects, time your trades, and grow your collection's value — all free to use.
        </p>

        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">{ICONS["radar"]}</div>
                <h3>Mock Draft Aggregator</h3>
                <p>We scan 100+ mock drafts daily across NFL, NBA, and MLB to track which prospects are rising and falling in real time.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">{ICONS["trending"]}</div>
                <h3>Buy Early Signals</h3>
                <p>Identify players whose draft stock is climbing but card prices haven't caught up yet. Get in before the market moves.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">{ICONS["target"]}</div>
                <h3>Event-Driven Sell Alerts</h3>
                <p>Know when to sell. We flag peak-hype moments — Draft Day, combine standouts, award announcements — so you can lock in profits.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">{ICONS["chart"]}</div>
                <h3>Draft Gap Analysis</h3>
                <p>See the "Draft Gap" — the spread between a player's mock draft momentum and their current card market price — updated daily.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">{ICONS["portfolio"]}</div>
                <h3>Free Portfolio Tracking</h3>
                <p>Sign up to add your cards and track their value over time. See how your collection performs against the market with daily updates.</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">{ICONS["users"]}</div>
                <h3>Multi-Sport Coverage</h3>
                <p>NFL, NBA, WNBA, and MLB prospects all in one place. Whether it's football rookies or baseball call-ups, we've got you covered.</p>
            </div>
        </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
        <div class="cta-icon">{ICONS["lightning"]}</div>
        <h2>Start Collecting Smarter — For Free</h2>
        <p>Create a free account to unlock portfolio tracking, save your favorite prospects, and get daily buy/sell signals delivered to your dashboard.</p>
        <div class="cta-buttons">
            <a href="signup.html" class="btn btn-primary">Create Free Account {ICONS["arrow_right"]}</a>
            <a href="players-2026.html" class="btn btn-outline">Explore Without Signing Up</a>
        </div>
        <p class="cta-fine-print">No credit card required · Free forever · Premium features coming soon</p>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-grid">
            <div class="footer-brand">
                <a href="/" class="logo">
                    {ICONS["lightning"]}
                    <span>Collector</span><span>Stream</span>
                </a>
                <p>Predictive intelligence for sports card investors. We turn mock draft data into actionable buy and sell signals — free to use.</p>
            </div>
            <div class="footer-column">
                <h4>Product</h4>
                <a href="#how-it-works">How It Works</a>
                <a href="#picks">Today's Picks</a>
                <a href="#draft-gap">Draft Gap Chart</a>
                <a href="portfolio.html">Portfolio Tracker</a>
            </div>
            <div class="footer-column">
                <h4>Resources</h4>
                <a href="#">Blog</a>
                <a href="#">FAQ</a>
                <a href="#">Contact</a>
                <a href="#">Feedback</a>
            </div>
            <div class="footer-column">
                <h4>Legal</h4>
                <a href="#">Privacy Policy</a>
                <a href="#">Terms of Service</a>
                <a href="#">Cookie Policy</a>
            </div>
        </div>
        <div class="footer-bottom">
            <div class="footer-copyright">© {datetime.now().year} CollectorStream. All rights reserved.</div>
            <div class="footer-social">
                <a href="#">Twitter</a>
                <a href="#">Instagram</a>
                <a href="#">Discord</a>
            </div>
        </div>
    </footer>

    <script>
    // Check if user is logged in and update header
    (function() {{
        const token = localStorage.getItem("token");
        if (token) {{
            document.getElementById("navAuth").style.display = "none";
            document.getElementById("navAuthLoggedIn").style.display = "flex";
        }}
    }})();
    </script>

    <style>
    .profile-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--bg-card, #151515);
        border: 1px solid var(--border, #1f1f1f);
        transition: all 0.2s;
    }}
    .profile-btn:hover {{
        border-color: var(--accent, #10b981);
        background: rgba(16, 185, 129, 0.1);
    }}
    .profile-btn svg {{
        color: var(--text-secondary, #9ca3af);
    }}
    .profile-btn:hover svg {{
        color: var(--accent, #10b981);
    }}
    .nav-auth-loggedin {{
        gap: 12px;
    }}
    </style>
</body>
</html>'''

    out_path = Path(output_dir) / "index.html"
    out_path.write_text(html)
    return True
