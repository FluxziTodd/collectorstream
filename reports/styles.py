"""CSS styles for CollectorStream - Lovable design system."""

# Design tokens
COLORS = {
    'bg_primary': '#0a0a0a',
    'bg_secondary': '#111111',
    'bg_card': '#151515',
    'border': '#1f1f1f',
    'border_hover': '#2a2a2a',
    'accent': '#10b981',  # Emerald green
    'accent_dark': '#059669',
    'text_primary': '#ffffff',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
}

CSS_LANDING = """
/* CollectorStream - Landing Page Styles */
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --bg-primary: #0a0a0a;
    --bg-secondary: #111111;
    --bg-card: #151515;
    --border: #1f1f1f;
    --border-hover: #2a2a2a;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    overflow-x: hidden;
}

/* Top accent bar */
.top-bar {
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%);
}

/* Header */
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 48px;
    max-width: 1400px;
    margin: 0 auto;
}

.logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 20px;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
}

.logo svg {
    width: 24px;
    height: 24px;
    color: var(--accent);
}

.logo span:last-child {
    color: var(--accent);
}

.nav-links {
    display: flex;
    gap: 32px;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: var(--text-primary);
}

.nav-auth {
    display: flex;
    align-items: center;
    gap: 16px;
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
}

.btn-primary {
    background: var(--accent);
    color: #000;
}

.btn-primary:hover {
    background: var(--accent-dark);
    transform: translateY(-1px);
}

.btn-outline {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
}

.btn-outline:hover {
    border-color: var(--accent);
    color: var(--accent);
}

.btn-ghost {
    background: transparent;
    color: var(--text-secondary);
}

.btn-ghost:hover {
    color: var(--text-primary);
}

/* Hero Section */
.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1400px;
    margin: 0 auto;
    padding: 60px 48px 40px;
    min-height: 500px;
}

.hero-content {
    max-width: 600px;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 20px;
    font-size: 13px;
    color: var(--accent);
    margin-bottom: 24px;
}

.hero-badge svg {
    width: 16px;
    height: 16px;
}

.hero h1 {
    font-size: 56px;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 20px;
}

.hero h1 .highlight {
    color: var(--accent);
}

.hero-subtitle {
    font-size: 18px;
    color: var(--text-secondary);
    margin-bottom: 32px;
    line-height: 1.7;
}

.hero-cta {
    display: flex;
    gap: 16px;
    margin-bottom: 40px;
}

.hero-stats {
    display: flex;
    gap: 48px;
}

.hero-stat {
    text-align: left;
}

.hero-stat-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent);
}

.hero-stat-label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.hero-image {
    flex: 1;
    max-width: 500px;
    display: flex;
    justify-content: flex-end;
}

.hero-image img {
    max-width: 100%;
    height: auto;
}

/* Ticker */
.ticker-container {
    background: var(--bg-secondary);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    overflow: hidden;
    padding: 12px 0;
}

.ticker {
    display: flex;
    animation: ticker 40s linear infinite;
    white-space: nowrap;
}

@keyframes ticker {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}

.ticker-item {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 0 24px;
    border-right: 1px solid var(--border);
}

.ticker-sport {
    display: inline-block;
    padding: 2px 8px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
}

.ticker-name {
    font-weight: 600;
    color: var(--text-primary);
}

.ticker-pos {
    color: var(--text-muted);
    font-size: 13px;
}

.ticker-mock {
    color: var(--accent);
    font-weight: 600;
}

.ticker-mock.down {
    color: var(--danger);
}

.ticker-price {
    color: var(--text-secondary);
}

/* Section styling */
.section {
    max-width: 1200px;
    margin: 0 auto;
    padding: 80px 48px;
}

.section-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 16px;
    text-align: center;
}

.section-title {
    font-size: 40px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 16px;
}

.section-subtitle {
    font-size: 16px;
    color: var(--text-secondary);
    text-align: center;
    max-width: 700px;
    margin: 0 auto 48px;
}

/* How It Works */
.how-it-works {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-top: 48px;
}

.step-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    transition: all 0.2s;
}

.step-card:hover {
    border-color: var(--accent);
    transform: translateY(-4px);
}

.step-icon {
    width: 48px;
    height: 48px;
    background: rgba(16, 185, 129, 0.1);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
}

.step-icon svg {
    width: 24px;
    height: 24px;
    color: var(--accent);
}

.step-card h3 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}

.step-card p {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
}

/* Today's Picks Table */
.picks-table-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-top: 32px;
}

.picks-table {
    width: 100%;
    border-collapse: collapse;
}

.picks-table th {
    text-align: left;
    padding: 16px 20px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
}

.picks-table td {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
}

.picks-table tr:last-child td {
    border-bottom: none;
}

.picks-table tr:hover {
    background: rgba(16, 185, 129, 0.02);
}

.player-cell {
    display: flex;
    flex-direction: column;
}

.player-cell-name {
    font-weight: 600;
    color: var(--text-primary);
}

.player-cell-pos {
    font-size: 12px;
    color: var(--text-muted);
}

.sport-badge {
    display: inline-block;
    padding: 4px 10px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
}

.mock-change {
    display: flex;
    align-items: center;
    gap: 4px;
}

.mock-change.up {
    color: var(--success);
}

.mock-change.down {
    color: var(--danger);
}

.mock-change svg {
    width: 14px;
    height: 14px;
}

.price-change {
    font-weight: 600;
}

.price-change.positive {
    color: var(--success);
}

.price-change.negative {
    color: var(--danger);
}

.signal-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

.signal-strong-buy {
    background: var(--success);
    color: #000;
}

.signal-buy {
    background: rgba(16, 185, 129, 0.2);
    color: var(--success);
}

.signal-hold {
    background: var(--bg-secondary);
    color: var(--text-muted);
}

.signal-sell {
    background: rgba(239, 68, 68, 0.2);
    color: var(--danger);
}

/* Draft Gap Chart */
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    margin-top: 48px;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
}

.chart-title {
    font-size: 18px;
    font-weight: 600;
}

.chart-subtitle {
    font-size: 14px;
    color: var(--text-muted);
    margin-top: 4px;
}

.chart-legend {
    display: flex;
    gap: 20px;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
}

.legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.legend-dot.mock {
    background: var(--warning);
}

.legend-dot.price {
    background: var(--accent);
}

.buy-window-alert {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 8px;
    margin-bottom: 24px;
    font-size: 14px;
}

.buy-window-alert svg {
    width: 16px;
    height: 16px;
    color: var(--accent);
}

.buy-window-alert strong {
    color: var(--accent);
}

/* League Selector - Primary Navigation */
.league-selector {
    background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    border-bottom: 1px solid var(--border);
    padding: 48px 0 56px;
}

.league-selector-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 48px;
    text-align: center;
}

.league-selector h2 {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
    color: var(--text-primary);
}

.league-subtitle {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 36px;
}

.league-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
}

@media (max-width: 1100px) {
    .league-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 768px) {
    .league-grid {
        grid-template-columns: 1fr 1fr;
    }
    .league-selector-inner {
        padding: 0 24px;
    }
}

@media (max-width: 500px) {
    .league-grid {
        grid-template-columns: 1fr;
    }
}

.league-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    text-align: left;
    transition: all 0.2s;
}

.league-card:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}

.league-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.league-logo {
    width: 48px;
    height: 48px;
    flex-shrink: 0;
}

.league-logo svg {
    width: 100%;
    height: 100%;
    border-radius: 8px;
}

/* Legacy support for league-icon */
.league-icon {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 800;
    color: #fff;
    flex-shrink: 0;
}

.league-wnba .league-icon { background: linear-gradient(135deg, #ff6b35 0%, #e85a24 100%); }
.league-nba .league-icon { background: linear-gradient(135deg, #1d428a 0%, #c8102e 100%); }
.league-nfl .league-icon { background: linear-gradient(135deg, #013369 0%, #d50a0a 100%); }
.league-mlb .league-icon { background: linear-gradient(135deg, #002d72 0%, #bf0d3e 100%); }
.league-nhl .league-icon { background: linear-gradient(135deg, #111 0%, #333 100%); }

.league-info h3 {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.2;
}

.league-info span {
    font-size: 12px;
    color: var(--text-muted);
}

.year-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.year-btn {
    flex: 1;
    min-width: 50px;
    padding: 10px 8px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 600;
    text-align: center;
    text-decoration: none;
    transition: all 0.15s;
}

.year-btn:hover {
    background: var(--bg-primary);
    border-color: var(--accent);
    color: var(--accent);
    transform: translateY(-1px);
}

.year-btn-primary {
    background: var(--accent);
    border-color: var(--accent);
    color: #000;
}

.year-btn-primary:hover {
    background: var(--accent-dark);
    border-color: var(--accent-dark);
    color: #000;
}

/* Compact Hero (when league selector is primary) */
.hero-compact {
    min-height: auto;
    padding: 48px 48px 32px;
}

.hero-compact .hero-content {
    max-width: 800px;
    text-align: center;
    margin: 0 auto;
}

.hero-compact h1 {
    font-size: 40px;
}

.hero-compact .hero-stats {
    justify-content: center;
}

.hero-compact .hero-badge {
    display: inline-flex;
}

/* Legacy Sports Grid (kept for compatibility) */
.sports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 40px;
}

.sport-card {
    display: flex;
    align-items: center;
    gap: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    text-decoration: none;
    transition: all 0.2s;
}

.sport-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

.sport-card-icon {
    width: 50px;
    height: 50px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    flex-shrink: 0;
}

.sport-card-wnba .sport-card-icon { background: #ff6b35; }
.sport-card-nba .sport-card-icon { background: #1d428a; }
.sport-card-nfl .sport-card-icon { background: #013369; }
.sport-card-mlb .sport-card-icon { background: #002d72; }
.sport-card-nhl .sport-card-icon { background: #000; }

.sport-card-info {
    flex: 1;
}

.sport-card-info h3 {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 2px;
}

.sport-card-info p {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 4px;
}

.sport-card-years {
    font-size: 12px;
    color: var(--accent);
    font-weight: 500;
}

.sport-card-arrow {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    transition: all 0.2s;
}

.sport-card:hover .sport-card-arrow {
    color: var(--accent);
    transform: translateX(4px);
}

.sport-card-arrow svg {
    width: 20px;
    height: 20px;
}

.sport-card-coming {
    opacity: 0.6;
}

.sport-card-coming .sport-card-years {
    color: var(--text-muted);
}

.sport-card-coming:hover {
    border-color: var(--border-hover);
    transform: none;
    box-shadow: none;
}

/* Features Grid */
.features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-top: 48px;
}

.feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px;
    transition: all 0.2s;
}

.feature-card:hover {
    border-color: var(--border-hover);
}

.feature-icon {
    width: 44px;
    height: 44px;
    background: rgba(16, 185, 129, 0.1);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

.feature-icon svg {
    width: 22px;
    height: 22px;
    color: var(--accent);
}

.feature-card h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 8px;
}

.feature-card p {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.6;
}

/* CTA Section */
.cta-section {
    max-width: 800px;
    margin: 80px auto;
    padding: 48px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    text-align: center;
}

.cta-icon {
    width: 56px;
    height: 56px;
    background: rgba(16, 185, 129, 0.1);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
}

.cta-icon svg {
    width: 28px;
    height: 28px;
    color: var(--accent);
}

.cta-section h2 {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 16px;
}

.cta-section p {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 32px;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
}

.cta-buttons {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 24px;
}

.cta-fine-print {
    font-size: 13px;
    color: var(--text-muted);
}

/* Footer */
.footer {
    border-top: 1px solid var(--border);
    padding: 64px 48px 32px;
    max-width: 1400px;
    margin: 0 auto;
}

.footer-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 48px;
    margin-bottom: 48px;
}

.footer-brand p {
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 16px;
    line-height: 1.6;
    max-width: 280px;
}

.footer-column h4 {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 20px;
}

.footer-column a {
    display: block;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    margin-bottom: 12px;
    transition: color 0.2s;
}

.footer-column a:hover {
    color: var(--text-primary);
}

.footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 32px;
    border-top: 1px solid var(--border);
}

.footer-copyright {
    font-size: 13px;
    color: var(--text-muted);
}

.footer-social {
    display: flex;
    gap: 24px;
}

.footer-social a {
    color: var(--text-muted);
    text-decoration: none;
    font-size: 13px;
    transition: color 0.2s;
}

.footer-social a:hover {
    color: var(--text-primary);
}

/* Responsive */
@media (max-width: 1024px) {
    .hero {
        flex-direction: column;
        text-align: center;
    }

    .hero-content {
        max-width: 100%;
    }

    .hero h1 {
        font-size: 40px;
    }

    .hero-cta {
        justify-content: center;
    }

    .hero-stats {
        justify-content: center;
    }

    .hero-image {
        display: none;
    }

    .how-it-works,
    .features-grid {
        grid-template-columns: 1fr;
    }

    .footer-grid {
        grid-template-columns: 1fr 1fr;
    }
}

@media (max-width: 768px) {
    .header {
        padding: 16px 24px;
    }

    .nav-links {
        display: none;
    }

    .section {
        padding: 48px 24px;
    }

    .hero {
        padding: 40px 24px;
    }

    .hero h1 {
        font-size: 32px;
    }

    .section-title {
        font-size: 28px;
    }
}
"""

CSS_APP = """
/* CollectorStream - App/Dashboard Styles */
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --bg-primary: #0a0a0a;
    --bg-secondary: #111111;
    --bg-card: #151515;
    --border: #1f1f1f;
    --border-hover: #2a2a2a;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}

.top-bar {
    height: 3px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%);
}

/* App Header */
.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
}

.logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
}

.logo span:last-child {
    color: var(--accent);
}

.app-nav {
    display: flex;
    gap: 8px;
}

.app-nav a {
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.2s;
}

.app-nav a:hover {
    color: var(--text-primary);
    background: var(--bg-card);
}

.app-nav a.active {
    color: var(--accent);
    background: rgba(16, 185, 129, 0.1);
}

/* Profile Button in Header */
.profile-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--bg-card);
    border: 1px solid var(--border);
    transition: all 0.2s;
    color: var(--text-secondary);
    overflow: hidden;
    padding: 0;
    text-decoration: none;
    margin-left: 16px;
}

.profile-btn:hover {
    border-color: var(--accent);
    color: var(--accent);
}

.profile-btn img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.profile-btn svg {
    flex-shrink: 0;
}

/* Sport Selector Dropdown */
.sport-selector {
    position: relative;
    margin-right: 16px;
}

.sport-selector-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.sport-selector-btn:hover {
    border-color: var(--accent);
}

.sport-selector-btn svg {
    width: 16px;
    height: 16px;
    color: var(--text-muted);
    transition: transform 0.2s;
}

.sport-selector.open .sport-selector-btn svg {
    transform: rotate(180deg);
}

.sport-selector-btn .sport-icon {
    width: 20px;
    height: 20px;
    border-radius: 4px;
}

.sport-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    min-width: 200px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    opacity: 0;
    visibility: hidden;
    transform: translateY(-10px);
    transition: all 0.2s;
    z-index: 1000;
}

.sport-selector.open .sport-dropdown {
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}

.sport-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 6px;
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}

.sport-option:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.sport-option.active {
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent);
}

.sport-option .sport-icon {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
}

.sport-option .sport-name {
    flex: 1;
}

.sport-option .sport-count {
    font-size: 12px;
    color: var(--text-muted);
    background: var(--bg-primary);
    padding: 2px 8px;
    border-radius: 10px;
}

/* Sport-specific colors */
.sport-wnba { background: #ff6b35; color: #fff; }
.sport-nba { background: #1d428a; color: #fff; }
.sport-nfl { background: #013369; color: #fff; }
.sport-mlb { background: #002d72; color: #fff; }
.sport-nhl { background: #000; color: #fff; }

/* Main Content */
.app-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 32px;
}

.page-header {
    margin-bottom: 32px;
}

.page-title {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
}

.page-subtitle {
    font-size: 15px;
    color: var(--text-secondary);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--accent);
}

.stat-label {
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
}

/* Player Grid */
.player-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
}

.player-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s;
    text-decoration: none;
    display: block;
    position: relative;
}

.player-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
}

.player-card-inner {
    display: flex;
    align-items: stretch;
}

.rank-badge {
    position: absolute;
    top: 12px;
    left: 12px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    background: var(--accent);
    color: #000;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.rank-badge.tier-a { background: #fbbf24; }
.rank-badge.tier-b { background: #9ca3af; }
.rank-badge.tier-c { background: #d97706; color: #fff; }
.rank-badge.tier-d { background: #4b5563; color: #fff; }

.player-photo {
    width: 100px;
    height: 120px;
    object-fit: cover;
    background: var(--bg-secondary);
    flex-shrink: 0;
}

.player-info {
    padding: 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.player-name {
    font-weight: 600;
    font-size: 15px;
    color: var(--text-primary);
    margin-bottom: 4px;
}

.player-details {
    font-size: 13px;
    color: var(--text-muted);
    margin-bottom: 4px;
}

.player-school {
    font-size: 13px;
    color: var(--text-secondary);
}

.player-hometown {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.flag-icon {
    width: 18px;
    height: 13px;
    border-radius: 2px;
}

/* Tables */
.data-table-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    text-align: left;
    padding: 14px 16px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
}

.data-table td {
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
}

.data-table tr:last-child td {
    border-bottom: none;
}

.data-table tr:hover {
    background: rgba(16, 185, 129, 0.02);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
    cursor: pointer;
    border: none;
}

.btn-primary {
    background: var(--accent);
    color: #000;
}

.btn-primary:hover {
    background: var(--accent-dark);
}

.btn-outline {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
}

.btn-outline:hover {
    border-color: var(--accent);
    color: var(--accent);
}

/* Signals */
.signal-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 600;
}

.signal-strong-buy { background: var(--success); color: #000; }
.signal-buy { background: rgba(16, 185, 129, 0.2); color: var(--success); }
.signal-hold { background: var(--bg-secondary); color: var(--text-muted); }
.signal-sell { background: rgba(239, 68, 68, 0.2); color: var(--danger); }

.price-up { color: var(--success); }
.price-down { color: var(--danger); }

/* Sport badges */
.sport-badge {
    display: inline-block;
    padding: 3px 8px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted);
}

.sport-badge.wnba { border-color: #f97316; color: #f97316; }
.sport-badge.nfl { border-color: #3b82f6; color: #3b82f6; }
.sport-badge.nba { border-color: #ef4444; color: #ef4444; }
.sport-badge.mlb { border-color: #10b981; color: #10b981; }

/* Footer */
.app-footer {
    border-top: 1px solid var(--border);
    padding: 24px 32px;
    margin-top: 48px;
}

.footer-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1400px;
    margin: 0 auto;
}

.footer-copyright {
    font-size: 13px;
    color: var(--text-muted);
}

.footer-links {
    display: flex;
    gap: 24px;
}

.footer-links a {
    font-size: 13px;
    color: var(--text-muted);
    text-decoration: none;
}

.footer-links a:hover {
    color: var(--text-primary);
}

/* Responsive */
@media (max-width: 768px) {
    .app-header {
        padding: 16px;
        flex-wrap: wrap;
        gap: 16px;
    }

    .app-nav {
        width: 100%;
        overflow-x: auto;
    }

    .app-content {
        padding: 16px;
    }

    .player-grid {
        grid-template-columns: 1fr;
    }
}
"""
