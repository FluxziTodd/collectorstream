"""Generate HTML reports for WNBA prospect tracking."""

import os
from datetime import datetime
from html import escape as html_escape
from pathlib import Path

from db.models import get_connection, get_players_by_draft_year, get_latest_card_values, get_watchlist_with_prices
from analysis.movers import get_movers, get_consensus_board, card_buy_signals
from analysis.card_prices import get_best_buys, get_price_changes
from .styles import CSS_APP
from .landing import generate_landing_page

DEFAULT_OUTPUT = Path.home() / "Desktop" / "WNBA-Scout"

# Legacy WNBA-only years (for backward compatibility)
DRAFT_YEARS = [2026, 2027, 2028, 2029, 2030]

# Multi-sport configuration
SPORTS_CONFIG = {
    "wnba": {
        "name": "WNBA",
        "draft_years": [2026, 2027, 2028, 2029, 2030],
        "prefix": "",  # Empty for backward compatibility (players-2026.html)
    },
    "nba": {
        "name": "NBA",
        "draft_years": [2026, 2027, 2028],
        "prefix": "nba-",  # nba-players-2026.html
    },
    "nfl": {
        "name": "NFL",
        "draft_years": [2026, 2027],
        "prefix": "nfl-",
    },
    "mlb": {
        "name": "MLB",
        "draft_years": [2026, 2027],
        "prefix": "mlb-",
    },
    "nhl": {
        "name": "NHL",
        "draft_years": [2026, 2027],
        "prefix": "nhl-",
    },
}

CSS = CSS_APP + """
/* Page-specific overrides using new color scheme */
h1 { font-size: 28px; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }
h2 { font-size: 20px; font-weight: 600; margin: 32px 0 16px; color: var(--text-primary); border-bottom: 1px solid var(--border); padding-bottom: 12px; }
h3 { color: var(--text-secondary); font-size: 16px; margin: 20px 0 10px; }
.subtitle { color: var(--text-secondary); font-size: 15px; margin-bottom: 24px; }
.timestamp { color: var(--text-muted); font-size: 12px; margin-bottom: 20px; }
a { color: var(--accent); text-decoration: none; }
a:hover { color: var(--accent-dark); text-decoration: underline; }
table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
th {
    background: var(--bg-secondary); color: var(--text-muted); text-align: left;
    padding: 14px 16px; font-size: 12px; text-transform: uppercase;
    letter-spacing: 0.5px; font-weight: 600; border-bottom: 1px solid var(--border);
}
td { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 14px; }
tr:hover { background: rgba(16, 185, 129, 0.02); }
tr.top-5 { background: rgba(16, 185, 129, 0.05); }
tr.top-5:hover { background: rgba(16, 185, 129, 0.08); }
.rank { font-weight: bold; color: var(--accent); text-align: center; width: 40px; }
.player-name { font-weight: 600; color: var(--text-primary); }
.school { color: var(--text-secondary); }
.pos { color: var(--text-muted); text-align: center; }
.avg-rank { text-align: center; font-weight: bold; }
.sources { text-align: center; }
.source-detail { color: var(--text-muted); font-size: 12px; }
.rising { color: var(--success); }
.falling { color: var(--danger); }
.signal-rising { background: rgba(16, 185, 129, 0.05); }
.signal-new { background: rgba(59, 130, 246, 0.05); }
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: bold; text-transform: uppercase;
}
.badge-rising { background: var(--success); color: #000; }
.badge-new { background: var(--info); color: #fff; }
.empty-state { color: var(--text-muted); font-style: italic; padding: 20px; text-align: center; }

/* Player Dashboard Grid */
.player-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 15px;
    margin: 25px 0;
}
.player-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.2s;
    text-decoration: none;
    display: flex;
    align-items: stretch;
    position: relative;
}
.player-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(16, 185, 129, 0.15);
    text-decoration: none;
}
.player-card.tier-a { border-color: #ffd700; background: linear-gradient(135deg, #1a1a0a 0%, #2a2a1a 100%); }
.player-card.tier-b { border-color: #c0c0c0; }
.player-card.tier-c { border-color: #cd7f32; }
.player-card.tier-d { border-color: #666; }
.rank-badge {
    position: absolute;
    top: 10px;
    left: 10px;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 16px;
    z-index: 10;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.rank-badge.tier-a { background: linear-gradient(135deg, #ffd700 0%, #ffaa00 100%); color: #000; }
.rank-badge.tier-b { background: linear-gradient(135deg, #c0c0c0 0%, #909090 100%); color: #000; }
.rank-badge.tier-c { background: linear-gradient(135deg, #cd7f32 0%, #a65f22 100%); color: #fff; }
.rank-badge.tier-d { background: linear-gradient(135deg, #666 0%, #444 100%); color: #fff; }
.rank-badge.unranked { background: #333; color: #666; }
.player-photo {
    width: 100px;
    height: 120px;
    object-fit: cover;
    background: #0f0f0f;
    flex-shrink: 0;
}
.player-info {
    padding: 12px 15px;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-width: 0;
}
.tier-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    margin-left: 8px;
    vertical-align: middle;
}
.tier-badge.tier-a { background: #ffd700; color: #000; }
.tier-badge.tier-b { background: #c0c0c0; color: #000; }
.tier-badge.tier-c { background: #cd7f32; color: #fff; }
.tier-badge.tier-d { background: #666; color: #fff; }
.player-card-name { font-weight: bold; color: #fff; font-size: 15px; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.player-card-details { color: #888; font-size: 12px; margin-bottom: 3px; }
.player-card-school { color: #aaa; font-size: 12px; }
.player-card-hometown { color: #666; font-size: 11px; margin-top: 6px; display: flex; align-items: center; gap: 5px; }
.flag-icon { width: 18px; height: 13px; border-radius: 2px; }
.player-card-rank { color: var(--text-muted); font-size: 11px; margin-top: 4px; }
.player-card-rank span { color: var(--accent); font-weight: bold; }

/* Player Detail Page */
.player-header {
    display: flex;
    gap: 30px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}
.player-header-photo {
    width: 250px;
    height: 300px;
    object-fit: cover;
    border-radius: 12px;
    border: 3px solid #333;
    background: #0f0f0f;
}
.player-bio { flex: 1; min-width: 300px; }
.player-bio h1 { font-size: 36px; margin-bottom: 10px; }
.bio-details {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-top: 15px;
}
.bio-item {
    background: #1a1a1a;
    padding: 10px 15px;
    border-radius: 8px;
}
.bio-label { font-size: 11px; color: #888; text-transform: uppercase; }
.bio-value { font-size: 16px; font-weight: 600; color: #fff; }
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}
.status-hot { background: #ff4444; color: #fff; }
.status-cold { background: #4444ff; color: #fff; }
.status-normal { background: #444; color: #ccc; }
"""


def _html_head(title):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — CollectorStream</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="top-bar"></div>
<header class="app-header">
    <a href="/" class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Collector</span><span>Stream</span>
    </a>
"""


def _html_nav(active=None, sport="wnba"):
    """Generate navigation with sport selector.

    Args:
        active: The active page label
        sport: Current sport (wnba, nba, nfl, mlb, nhl)
    """
    sport = sport.lower()

    # Sport configurations
    sports_config = {
        "wnba": {"name": "WNBA", "years": [2026, 2027, 2028], "prefix": "", "color": "wnba"},
        "nba": {"name": "NBA", "years": [2026, 2027], "prefix": "nba-", "color": "nba"},
        "nfl": {"name": "NFL", "years": [2026, 2027], "prefix": "nfl-", "color": "nfl"},
        "mlb": {"name": "MLB", "years": [2026, 2027], "prefix": "mlb-", "color": "mlb"},
        "nhl": {"name": "NHL", "years": [2026, 2027], "prefix": "nhl-", "color": "nhl"},
    }

    current = sports_config.get(sport, sports_config["wnba"])
    prefix = current["prefix"]
    years = current["years"]

    # Build navigation links based on sport
    links = [("/", "Home")]
    for year in years[:2]:  # Show first 2 years in nav
        links.append((f"{prefix}players-{year}.html", f"{year} Prospects"))
    links.extend([
        ("buy-signals.html", "Buy Signals"),
        ("watchlist.html", "Watchlist"),
        ("portfolio.html", "Portfolio"),
    ])

    # Sport selector dropdown
    html = '''    <div class="sport-selector" id="sportSelector">
        <button class="sport-selector-btn" onclick="toggleSportDropdown()">
            <span class="sport-icon sport-''' + sport + '">' + current["name"][:1] + '''</span>
            <span>''' + current["name"] + '''</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="sport-dropdown">
'''

    # Add sport options
    for key, cfg in sports_config.items():
        active_cls = " active" if key == sport else ""
        sport_prefix = cfg["prefix"]
        first_year = cfg["years"][0]
        html += f'''            <a href="{sport_prefix}players-{first_year}.html" class="sport-option{active_cls}">
                <span class="sport-icon sport-{key}">{cfg["name"][:1]}</span>
                <span class="sport-name">{cfg["name"]}</span>
            </a>
'''

    html += '''        </div>
    </div>
'''

    # Navigation links
    html += '    <nav class="app-nav">\n'
    for href, label in links:
        cls = ' class="active"' if label == active else ""
        html += f'        <a href="{href}"{cls}>{label}</a>\n'
    html += '    </nav>\n'

    # Profile button with profile pic support
    html += '''    <a href="profile.html" class="profile-btn" id="headerProfileBtn" title="Account settings">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18" id="headerProfileIcon">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
        </svg>
    </a>
</header>
<script>
// Profile pic loader
(function() {
    var pic = localStorage.getItem("profilePic");
    if (pic) {
        var btn = document.getElementById("headerProfileBtn");
        var icon = document.getElementById("headerProfileIcon");
        if (btn && icon) {
            var img = document.createElement("img");
            img.src = pic;
            img.alt = "Profile";
            icon.style.display = "none";
            btn.appendChild(img);
        }
    }
})();

// Sport selector toggle
function toggleSportDropdown() {
    document.getElementById("sportSelector").classList.toggle("open");
}

// Close dropdown when clicking outside
document.addEventListener("click", function(e) {
    var selector = document.getElementById("sportSelector");
    if (selector && !selector.contains(e.target)) {
        selector.classList.remove("open");
    }
});
</script>
'''
    html += '<main class="app-content">\n'
    return html


def _html_foot():
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return f"""
</main>
<footer class="app-footer">
    <div class="footer-content">
        <div class="footer-copyright">© {datetime.now().year} CollectorStream. All rights reserved.</div>
        <div class="footer-links">
            <a href="/private/">Admin</a>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
        </div>
    </div>
</footer>
</body>
</html>"""


def _get_scrape_stats():
    conn = get_connection()
    stats = conn.execute("""
        SELECT source, MAX(scraped_at) as last_scrape,
               SUM(CASE WHEN status='success' THEN players_found ELSE 0 END) as total_found
        FROM scrape_log
        GROUP BY source
        ORDER BY last_scrape DESC
    """).fetchall()
    conn.close()
    return [dict(s) for s in stats]


def generate_board_page(draft_year, output_dir, sport="wnba"):
    """Generate consensus board page for a draft year.

    Args:
        draft_year: The draft year
        output_dir: Directory to write HTML file
        sport: Sport code (wnba, nba, nfl, etc.)
    """
    sport_config = SPORTS_CONFIG.get(sport.lower(), SPORTS_CONFIG["wnba"])
    sport_name = sport_config["name"]
    prefix = sport_config["prefix"]

    board = get_consensus_board(draft_year, sport=sport)
    players = get_players_by_draft_year(draft_year, sport=sport)

    if not board and not players:
        return False

    html = _html_head(f"{draft_year} {sport_name} Draft — Consensus Board")
    html += _html_nav(str(draft_year), sport=sport)
    html += f"<h1>{draft_year} {sport_name} Draft — Consensus Board</h1>\n"
    html += f'<p class="subtitle">{len(board)} prospects tracked across multiple sources</p>\n'

    if not board:
        html += '<p class="empty-state">No ranking data yet. Run scrapers to populate.</p>\n'
    else:
        html += """<table>
<tr>
  <th>#</th><th>Player</th><th>School</th><th>Pos</th>
  <th>Avg Rank</th><th>Sources</th><th>Source Rankings</th>
</tr>\n"""
        for i, p in enumerate(board, 1):
            avg = f"{p['avg_rank']:.1f}" if p["avg_rank"] else "-"
            cls = ' class="top-5"' if i <= 5 and p["avg_rank"] else ""
            sources = p.get("source_ranks") or ""
            # Format source rankings nicely
            source_parts = sources.split(",") if sources else []
            source_html = "<br>".join(source_parts) if source_parts else "-"

            html += f"""<tr{cls}>
  <td class="rank">{i}</td>
  <td class="player-name">{p['name']}</td>
  <td class="school">{p.get('school') or ''}</td>
  <td class="pos">{p.get('position') or ''}</td>
  <td class="avg-rank">{avg}</td>
  <td class="sources">{p['num_sources'] or 0}</td>
  <td class="source-detail">{source_html}</td>
</tr>\n"""
        html += "</table>\n"

    html += _html_foot()

    out_path = output_dir / f"{prefix}{draft_year}-board.html"
    out_path.write_text(html)
    return True


def generate_player_dashboard(draft_year, output_dir, sport="wnba"):
    """Generate a visual dashboard of player cards for a draft year.

    Args:
        draft_year: The draft year
        output_dir: Directory to write HTML file
        sport: Sport code (wnba, nba, nfl, etc.)
    """
    from db.models import get_players_for_dashboard

    sport_config = SPORTS_CONFIG.get(sport.lower(), SPORTS_CONFIG["wnba"])
    sport_name = sport_config["name"]
    prefix = sport_config["prefix"]

    players = get_players_for_dashboard(draft_year, sport=sport)

    if not players:
        return False

    html = _html_head(f"{draft_year} {sport_name} Draft — Players")
    html += _html_nav(f"{draft_year} Prospects", sport=sport)
    html += f"<h1>{draft_year} {sport_name} Draft — Player Dashboard</h1>\n"
    html += f'<p class="subtitle">{len(players)} prospects with photos, stats, and tier ratings</p>\n'

    # Tier summary
    tier_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    for p in players:
        if p.get('tier') in tier_counts:
            tier_counts[p['tier']] += 1

    html += '<div class="stats-grid">\n'
    for tier, count in tier_counts.items():
        colors = {'A': '#ffd700', 'B': '#c0c0c0', 'C': '#cd7f32', 'D': '#666'}
        html += f'''  <div class="stat-card">
    <div class="stat-value" style="color:{colors[tier]}">{count}</div>
    <div class="stat-label">Tier {tier}</div>
  </div>\n'''
    html += '</div>\n'

    # Player grid
    html += '<div class="player-grid">\n'

    for rank, p in enumerate(players, 1):
        tier = p.get('tier') or ''
        tier_lower = tier.lower() if tier else 'd'
        photo_url = p.get('photo_url') or f"https://ui-avatars.com/api/?name={html_escape(p['name']).replace(' ', '+')}&background=1a1a1a&color=ff6b35&size=200"

        # Country flag
        country = p.get('country') or 'US'
        flag_url = f"https://flagcdn.com/w40/{country.lower()}.png"

        # Build card HTML with prominent rank badge
        html += f'''  <a href="player-{p['id']}.html" class="player-card tier-{tier_lower}">
    <span class="rank-badge tier-{tier_lower}">{rank}</span>
    <img src="{html_escape(photo_url)}" alt="{html_escape(p['name'])}" class="player-photo" loading="lazy" onerror="this.src='https://ui-avatars.com/api/?name={html_escape(p['name']).replace(' ', '+')}&background=1a1a1a&color=ff6b35&size=200'">
    <div class="player-info">
      <div class="player-card-name">{html_escape(p['name'])}</div>
      <div class="player-card-details">{html_escape(p.get('height') or '')} | {html_escape(p.get('position') or 'Unknown')}</div>
      <div class="player-card-school">{html_escape(p.get('school') or 'Unknown')}</div>
'''
        if p.get('hometown'):
            html += f'''      <div class="player-card-hometown">
        <img src="{flag_url}" alt="{country}" class="flag-icon" onerror="this.style.display='none'">
        {html_escape(p['hometown'])}
      </div>
'''
        html += '''    </div>
  </a>
'''

    html += '</div>\n'
    html += _html_foot()

    out_path = output_dir / f"{prefix}players-{draft_year}.html"
    out_path.write_text(html)
    return True


def generate_player_detail_page(player_id, output_dir):
    """Generate a detailed page for a single player."""
    from db.models import get_player_full_profile

    profile = get_player_full_profile(player_id)
    if not profile:
        return False

    name = profile.get('name', 'Unknown')
    tier = profile.get('tier') or ''
    tier_lower = tier.lower() if tier else ''

    html = _html_head(f"{name} — Player Profile")
    html += _html_nav()

    # Photo URL with fallback
    photo_url = profile.get('photo_url') or f"https://ui-avatars.com/api/?name={html_escape(name).replace(' ', '+')}&background=1a1a1a&color=ff6b35&size=300"

    # Country flag
    country = profile.get('country') or 'US'
    flag_url = f"https://flagcdn.com/w40/{country.lower()}.png"

    # Header with photo and bio
    html += '<div class="player-header">\n'
    html += f'  <img src="{html_escape(photo_url)}" alt="{html_escape(name)}" class="player-header-photo" onerror="this.src=\'https://ui-avatars.com/api/?name={html_escape(name).replace(" ", "+")}&background=1a1a1a&color=ff6b35&size=300\'">\n'
    html += '  <div class="player-bio">\n'
    html += f'    <h1>{html_escape(name)}'
    if tier:
        colors = {'A': '#ffd700', 'B': '#c0c0c0', 'C': '#cd7f32', 'D': '#666'}
        html += f' <span class="tier-badge tier-{tier_lower}" style="display:inline-flex;vertical-align:middle;margin-left:10px;">{tier}</span>'
    html += '</h1>\n'
    html += f'    <p class="subtitle">{profile.get("draft_year", "")} WNBA Draft Prospect</p>\n'

    # Status badge if available
    status = profile.get('status')
    if status and status.get('status'):
        status_class = f"status-{status['status']}"
        html += f'    <span class="status-badge {status_class}">{status["status"].upper()}</span>\n'

    # Bio details grid
    html += '    <div class="bio-details">\n'
    bio_fields = [
        ('Height', profile.get('height')),
        ('Position', profile.get('position')),
        ('School', profile.get('school')),
        ('Draft Year', profile.get('draft_year')),
    ]
    for label, value in bio_fields:
        if value:
            html += f'''      <div class="bio-item">
        <div class="bio-label">{label}</div>
        <div class="bio-value">{html_escape(str(value))}</div>
      </div>\n'''

    # Hometown with flag
    if profile.get('hometown'):
        html += f'''      <div class="bio-item">
        <div class="bio-label">Hometown</div>
        <div class="bio-value"><img src="{flag_url}" alt="{country}" class="flag-icon" style="vertical-align:middle;margin-right:5px;" onerror="this.style.display='none'">{html_escape(profile['hometown'])}</div>
      </div>\n'''

    html += '    </div>\n'  # bio-details
    html += '  </div>\n'  # player-bio
    html += '</div>\n'  # player-header

    # Season Stats
    stats = profile.get('stats', [])
    if stats:
        html += '<h2>Season Statistics</h2>\n'
        html += '''<table>
<tr><th>Season</th><th>GP</th><th>PPG</th><th>RPG</th><th>APG</th><th>SPG</th><th>BPG</th><th>FG%</th><th>3P%</th><th>FT%</th></tr>\n'''
        for s in stats:
            def fmt(v, pct=False):
                if v is None:
                    return '-'
                if pct:
                    return f"{v*100:.1f}%" if v < 1 else f"{v:.1f}%"
                return f"{v:.1f}"

            html += f'''<tr>
  <td>{s.get('season', '-')}</td>
  <td class="avg-rank">{s.get('games_played') or '-'}</td>
  <td class="avg-rank">{fmt(s.get('points_per_game'))}</td>
  <td class="avg-rank">{fmt(s.get('rebounds_per_game'))}</td>
  <td class="avg-rank">{fmt(s.get('assists_per_game'))}</td>
  <td class="avg-rank">{fmt(s.get('steals_per_game'))}</td>
  <td class="avg-rank">{fmt(s.get('blocks_per_game'))}</td>
  <td class="avg-rank">{fmt(s.get('fg_pct'), pct=True)}</td>
  <td class="avg-rank">{fmt(s.get('three_pct'), pct=True)}</td>
  <td class="avg-rank">{fmt(s.get('ft_pct'), pct=True)}</td>
</tr>\n'''
        html += '</table>\n'
    else:
        html += '<h2>Season Statistics</h2>\n'
        html += '<p class="empty-state">No stats available. Run "python main.py stats" to scrape player statistics.</p>\n'

    # Draft Rankings
    rankings = profile.get('rankings', [])
    if rankings:
        html += '<h2>Draft Rankings</h2>\n'
        html += '''<table>
<tr><th>Source</th><th>Rank</th><th>Projected Pick</th><th>Date</th></tr>\n'''
        for r in rankings:
            html += f'''<tr>
  <td>{html_escape(r.get('source', '-'))}</td>
  <td class="avg-rank">{r.get('rank') or '-'}</td>
  <td class="avg-rank">{r.get('projected_pick') or '-'}</td>
  <td class="source-detail">{r.get('scrape_date', '-')}</td>
</tr>\n'''
        html += '</table>\n'
    else:
        html += '<h2>Draft Rankings</h2>\n'
        html += '<p class="empty-state">No rankings available.</p>\n'

    # Card Values
    card_values = profile.get('card_values', [])
    if card_values:
        html += '<h2>Card Values</h2>\n'
        html += '''<table>
<tr><th>Type</th><th>Lowest</th><th>Average</th><th>Listings</th><th>Date</th></tr>\n'''
        for cv in card_values:
            lowest = f"${cv['lowest_bin']:.2f}" if cv.get('lowest_bin') else '-'
            avg = f"${cv['avg_price']:.2f}" if cv.get('avg_price') else '-'
            html += f'''<tr>
  <td>{html_escape(cv.get('card_type', 'autograph'))}</td>
  <td class="avg-rank rising">{lowest}</td>
  <td class="avg-rank">{avg}</td>
  <td class="avg-rank">{cv.get('listing_count') or '-'}</td>
  <td class="source-detail">{cv.get('recorded_date', '-')}</td>
</tr>\n'''
        html += '</table>\n'

    # Back link
    html += f'\n<p style="margin-top:30px;"><a href="players-{profile.get("draft_year", 2026)}.html">&larr; Back to {profile.get("draft_year", 2026)} Players</a></p>\n'

    html += _html_foot()

    out_path = output_dir / f"player-{player_id}.html"
    out_path.write_text(html)
    return True


def generate_all_player_pages(output_dir):
    """Generate detail pages for all players."""
    conn = get_connection()
    players = conn.execute("SELECT id, name FROM players ORDER BY draft_year, name").fetchall()
    conn.close()

    count = 0
    for p in players:
        if generate_player_detail_page(p['id'], output_dir):
            count += 1

    return count


def generate_movers_page(output_dir):
    html = _html_head("Rising & Falling Prospects")
    html += _html_nav("Movers")
    html += "<h1>Rising & Falling Prospects</h1>\n"
    html += '<p class="subtitle">Players whose mock draft rankings changed in the last 30 days</p>\n'

    any_movers = False
    for year in DRAFT_YEARS:
        movers = get_movers(draft_year=year, days_back=30)
        if not movers:
            continue
        any_movers = True

        html += f"<h2>{year} Draft Class</h2>\n"
        html += """<table>
<tr><th>Player</th><th>Source</th><th>Was</th><th>Now</th><th>Change</th></tr>\n"""
        for m in movers:
            change = m["rank_change"] or 0
            if change > 0:
                cls = "rising"
                arrow = f"&#9650; {change}"
            elif change < 0:
                cls = "falling"
                arrow = f"&#9660; {abs(change)}"
            else:
                cls = ""
                arrow = "&#8594; 0"
            html += f"""<tr>
  <td class="player-name">{m['name']}</td>
  <td class="school">{m['source']}</td>
  <td class="avg-rank">{m.get('previous_rank', '?')}</td>
  <td class="avg-rank">{m.get('current_rank', '?')}</td>
  <td class="{cls}" style="text-align:center;font-weight:bold">{arrow}</td>
</tr>\n"""
        html += "</table>\n"

    if not any_movers:
        html += '<p class="empty-state">No ranking changes detected yet. Run scrapers at least twice (on different days) to track movement.</p>\n'

    html += _html_foot()
    (output_dir / "movers.html").write_text(html)


def generate_signals_page(output_dir):
    html = _html_head("Card Buy Signals")
    html += _html_nav("Buy Signals")
    html += "<h1>Card Buy Signals</h1>\n"
    html += '<p class="subtitle">Players whose cards may be undervalued based on draft position trends</p>\n'

    any_signals = False
    for year in DRAFT_YEARS:
        signals = card_buy_signals(draft_year=year)
        if not signals:
            continue
        any_signals = True

        html += f"<h2>{year} Draft Class</h2>\n"
        html += """<table>
<tr><th>Signal</th><th>Player</th><th>Detail</th></tr>\n"""
        for s in signals:
            if s["signal"] == "RISING":
                badge = '<span class="badge badge-rising">RISING</span>'
                row_cls = "signal-rising"
            else:
                badge = '<span class="badge badge-new">NEW ENTRY</span>'
                row_cls = "signal-new"
            html += f"""<tr class="{row_cls}">
  <td>{badge}</td>
  <td class="player-name">{s['name']}</td>
  <td>{s['detail']}</td>
</tr>\n"""
        html += "</table>\n"

    if not any_signals:
        html += '<p class="empty-state">No buy signals detected yet. Need more scrape data over time to identify trends.</p>\n'

    html += _html_foot()
    (output_dir / "buy-signals.html").write_text(html)


def generate_card_values_page(output_dir):
    """Generate card values page with eBay pricing data."""
    html = _html_head("Card Values — eBay Autograph Prices")
    html += _html_nav("Card Values")
    html += "<h1>Card Values — eBay Autograph Prices</h1>\n"
    html += '<p class="subtitle">Current Buy It Now prices for autograph cards on eBay</p>\n'

    # Best buys section
    buys = get_best_buys()
    if buys:
        html += "<h2>Best Buys — High Rank, Low Price</h2>\n"
        html += '<p class="source-detail">Players ranked high in mock drafts whose autograph cards are still affordable</p>\n'
        html += """<table>
<tr><th>#</th><th>Player</th><th>Year</th><th>Avg Rank</th>
<th>Lowest Auto</th><th>Avg Price</th><th>Listings</th><th>eBay</th></tr>\n"""
        for i, b in enumerate(buys[:25], 1):
            rank = f"{b['avg_rank']:.0f}" if b.get("avg_rank") else "?"
            lowest = f"${b['lowest_bin']:.2f}" if b.get("lowest_bin") else "-"
            avg = f"${b['avg_price']:.2f}" if b.get("avg_price") else "-"
            url = b.get("ebay_search_url") or ""
            link = f'<a href="{url}" target="_blank">Search</a>' if url else ""
            cls = ' class="top-5"' if i <= 5 else ""
            html += f"""<tr{cls}>
  <td class="rank">{i}</td>
  <td class="player-name">{b['name']}</td>
  <td class="avg-rank">{b['draft_year']}</td>
  <td class="avg-rank">{rank}</td>
  <td style="color:#00c853;font-weight:bold">{lowest}</td>
  <td class="avg-rank">{avg}</td>
  <td class="sources">{b.get('listing_count') or 0}</td>
  <td>{link}</td>
</tr>\n"""
        html += "</table>\n"

    # Per-year card values
    any_data = False
    for year in DRAFT_YEARS:
        values = get_latest_card_values(draft_year=year)
        has_prices = [v for v in values if v.get("lowest_bin")]
        if not has_prices:
            continue
        any_data = True

        html += f"<h2>{year} Draft Class — Card Prices</h2>\n"
        html += """<table>
<tr><th>Player</th><th>School</th><th>Lowest Auto</th>
<th>Avg Price</th><th>Listings</th><th>eBay</th></tr>\n"""
        for v in values:
            if not v.get("lowest_bin"):
                continue
            lowest = f"${v['lowest_bin']:.2f}" if v.get("lowest_bin") else "-"
            avg = f"${v['avg_price']:.2f}" if v.get("avg_price") else "-"
            url = v.get("ebay_search_url") or ""
            link = f'<a href="{url}" target="_blank">Search</a>' if url else ""
            html += f"""<tr>
  <td class="player-name">{v['name']}</td>
  <td class="school">{v.get('school') or ''}</td>
  <td style="color:#00c853;font-weight:bold">{lowest}</td>
  <td class="avg-rank">{avg}</td>
  <td class="sources">{v.get('listing_count') or 0}</td>
  <td>{link}</td>
</tr>\n"""
        html += "</table>\n"

    if not any_data and not buys:
        html += '<p class="empty-state">No card price data yet. Run <code>python main.py cards</code> to search eBay.</p>\n'

    # Price changes
    changes = get_price_changes()
    if changes:
        html += "<h2>Price Changes</h2>\n"
        html += """<table>
<tr><th>Player</th><th>Year</th><th>Was</th><th>Now</th><th>Change</th></tr>\n"""
        for c in changes:
            pct = c.get("pct_change")
            if pct is not None:
                if pct < 0:
                    cls = "rising"  # price dropped = good for buying
                    arrow = f"&#9660; {abs(pct):.0f}%"
                else:
                    cls = "falling"  # price went up
                    arrow = f"&#9650; {pct:.0f}%"
            else:
                cls = ""
                arrow = "-"
            html += f"""<tr>
  <td class="player-name">{c['name']}</td>
  <td class="avg-rank">{c['draft_year']}</td>
  <td class="avg-rank">${c.get('prev_price', 0):.2f}</td>
  <td class="avg-rank">${c.get('current_price', 0):.2f}</td>
  <td class="{cls}" style="text-align:center;font-weight:bold">{arrow}</td>
</tr>\n"""
        html += "</table>\n"

    html += _html_foot()
    (output_dir / "card-values.html").write_text(html)


def generate_watchlist_page(output_dir):
    """Generate watchlist page showing tracked players and card prices."""
    html = _html_head("Watchlist — Players I'm Watching")
    html += _html_nav("Watchlist")
    html += "<h1>Watchlist</h1>\n"
    html += '<p class="subtitle">Players I\'m watching for card investments</p>\n'

    data = get_watchlist_with_prices()
    if not data:
        html += '<p class="empty-state">No players on watchlist yet. Add with: <code>python main.py watchlist --add "Player Name"</code></p>\n'
    else:
        html += """<table>
<tr><th>Player</th><th>Sport</th><th>Lowest Auto</th>
<th>Avg Price</th><th>Listings</th><th>Last Checked</th><th>eBay</th></tr>\n"""
        for d in data:
            lowest = f"${d['lowest_bin']:.2f}" if d.get("lowest_bin") else "-"
            avg = f"${d['avg_price']:.2f}" if d.get("avg_price") else "-"
            listings = str(d.get("listing_count") or 0) if d.get("listing_count") else "-"
            checked = d.get("recorded_date") or "never"
            url = d.get("ebay_search_url") or ""
            link = f'<a href="{url}" target="_blank">Search</a>' if url else ""
            html += f"""<tr>
  <td class="player-name">{d['name']}</td>
  <td class="school">{d.get('sport') or ''}</td>
  <td style="color:#00c853;font-weight:bold">{lowest}</td>
  <td class="avg-rank">{avg}</td>
  <td class="sources">{listings}</td>
  <td class="school">{checked}</td>
  <td>{link}</td>
</tr>\n"""
        html += "</table>\n"

    html += _html_foot()
    (output_dir / "watchlist.html").write_text(html)


def generate_index(output_dir):
    html = _html_head("WNBA Scout — Dashboard")
    html += _html_nav("Dashboard")
    html += "<h1>WNBA Scout</h1>\n"
    html += '<p class="subtitle">Sports card investment tracker for WNBA draft prospects</p>\n'

    # Stats
    conn = get_connection()
    total_players = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    total_rankings = conn.execute("SELECT COUNT(*) FROM rankings").fetchone()[0]
    total_sources = conn.execute("SELECT COUNT(DISTINCT source) FROM rankings").fetchone()[0]
    conn.close()

    html += '<div class="stats-grid">\n'
    for val, label in [
        (total_players, "Players Tracked"),
        (total_rankings, "Total Rankings"),
        (total_sources, "Sources"),
        (len(DRAFT_YEARS), "Draft Classes"),
    ]:
        html += f"""<div class="stat-card">
  <div class="stat-value">{val}</div>
  <div class="stat-label">{label}</div>
</div>\n"""
    html += "</div>\n"

    # Draft class summaries
    html += "<h2>Draft Classes</h2>\n"
    for year in DRAFT_YEARS:
        board = get_consensus_board(year)
        ranked = [p for p in board if p["avg_rank"] is not None]
        if not board:
            continue

        html += f'<h3><a href="{year}-board.html">{year} WNBA Draft</a> — {len(board)} players'
        if ranked:
            html += f" ({len(ranked)} ranked)"
        html += "</h3>\n"

        if ranked:
            html += "<table><tr><th>#</th><th>Player</th><th>School</th><th>Avg Rank</th><th>Sources</th></tr>\n"
            for i, p in enumerate(ranked[:10], 1):
                avg = f"{p['avg_rank']:.1f}" if p["avg_rank"] else "-"
                cls = ' class="top-5"' if i <= 5 else ""
                html += f"""<tr{cls}>
  <td class="rank">{i}</td>
  <td class="player-name">{p['name']}</td>
  <td class="school">{p.get('school') or ''}</td>
  <td class="avg-rank">{avg}</td>
  <td class="sources">{p['num_sources'] or 0}</td>
</tr>\n"""
            html += "</table>\n"
            if len(ranked) > 10:
                html += f'<p><a href="{year}-board.html">View all {len(ranked)} ranked players &rarr;</a></p>\n'

    # Scrape log
    stats = _get_scrape_stats()
    if stats:
        html += "<h2>Data Sources</h2>\n"
        html += "<table><tr><th>Source</th><th>Last Scraped</th><th>Players Found</th></tr>\n"
        for s in stats:
            html += f"""<tr>
  <td>{s['source']}</td>
  <td class="school">{s['last_scrape'] or 'never'}</td>
  <td class="avg-rank">{s['total_found']}</td>
</tr>\n"""
        html += "</table>\n"

    html += _html_foot()
    (output_dir / "index.html").write_text(html)


API_ENDPOINT = "https://16bs8nqbr8.execute-api.us-east-1.amazonaws.com/trigger"


def generate_private_dashboard(output_dir):
    """Generate the password-protected admin dashboard with Run Now button."""
    private_dir = output_dir / "private"
    private_dir.mkdir(parents=True, exist_ok=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin — CollectorStream</title>
<style>{CSS}
.btn {{
    display: inline-block; padding: 14px 32px; font-size: 18px;
    font-weight: bold; color: #000; background: var(--accent); border: none;
    border-radius: 8px; cursor: pointer; transition: all 0.2s;
}}
.btn:hover {{ background: var(--accent-dark); transform: translateY(-1px); }}
.btn:disabled {{ background: var(--text-muted); cursor: not-allowed; transform: none; }}
.status-box {{
    margin-top: 20px; padding: 16px; border-radius: 8px;
    background: var(--bg-card); border: 1px solid var(--border); font-size: 14px;
}}
.status-idle {{ border-left: 4px solid var(--text-muted); }}
.status-queued {{ border-left: 4px solid var(--warning); }}
.status-running {{ border-left: 4px solid var(--info); }}
.status-completed {{ border-left: 4px solid var(--success); }}
.status-failed {{ border-left: 4px solid var(--danger); }}
.status-label {{
    display: inline-block; padding: 2px 10px; border-radius: 4px;
    font-size: 12px; font-weight: bold; text-transform: uppercase;
    margin-bottom: 8px;
}}
.label-idle {{ background: var(--bg-secondary); color: var(--text-secondary); }}
.label-queued {{ background: var(--warning); color: #000; }}
.label-running {{ background: var(--info); color: #fff; }}
.label-completed {{ background: var(--success); color: #000; }}
.label-failed {{ background: var(--danger); color: #fff; }}
</style>
</head>
<body>
<div class="container">
<div class="nav">
  <a href="/">Dashboard</a>
  <a href="/card-values.html">Card Values</a>
  <a href="/watchlist.html">Watchlist</a>
  <a href="/private/" class="active">Admin</a>
</div>

<h1>Admin Dashboard</h1>
<p class="subtitle">Trigger the full pipeline: scrape &rarr; normalize &rarr; cards &rarr; report &rarr; deploy</p>

<button class="btn" id="runBtn" onclick="triggerRun()">Run Now</button>

<div class="status-box status-idle" id="statusBox">
  <span class="status-label label-idle" id="statusLabel">IDLE</span>
  <div id="statusDetail">Checking status...</div>
</div>

<script>
const API = "{API_ENDPOINT}";
let polling = false;

function updateUI(data) {{
    const box = document.getElementById("statusBox");
    const label = document.getElementById("statusLabel");
    const detail = document.getElementById("statusDetail");
    const btn = document.getElementById("runBtn");
    const s = data.status || "idle";

    box.className = "status-box status-" + s;
    label.className = "status-label label-" + s;
    label.textContent = s.toUpperCase();
    btn.disabled = (s === "queued" || s === "running");

    let info = "";
    if (data.requested_at) info += "Requested: " + new Date(data.requested_at).toLocaleString() + "<br>";
    if (data.updated_at) info += "Updated: " + new Date(data.updated_at).toLocaleString() + "<br>";
    if (data.completed_at) info += "Completed: " + new Date(data.completed_at).toLocaleString() + "<br>";
    if (data.failed_at) info += "Failed: " + new Date(data.failed_at).toLocaleString() + "<br>";
    if (data.message) info += data.message;
    if (!info) info = "No runs yet.";
    detail.innerHTML = info;

    if (s === "queued" || s === "running") {{
        if (!polling) startPolling();
    }} else {{
        stopPolling();
    }}
}}

function checkStatus() {{
    fetch(API).then(r => r.json()).then(updateUI).catch(() => {{}});
}}

let pollTimer = null;
function startPolling() {{
    polling = true;
    pollTimer = setInterval(checkStatus, 5000);
}}
function stopPolling() {{
    polling = false;
    if (pollTimer) {{ clearInterval(pollTimer); pollTimer = null; }}
}}

function triggerRun() {{
    const btn = document.getElementById("runBtn");
    btn.disabled = true;
    btn.textContent = "Triggering...";
    fetch(API, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ action: "run" }})
    }})
    .then(r => r.json())
    .then(data => {{
        btn.textContent = "Run Now";
        if (data.status) updateUI(data.status);
        else checkStatus();
    }})
    .catch(() => {{
        btn.textContent = "Run Now";
        btn.disabled = false;
    }});
}}

// Initial status check
checkStatus();
</script>

<p class="timestamp">Report generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
</div>
</body>
</html>"""

    (private_dir / "index.html").write_text(html)


API_BASE = "https://16bs8nqbr8.execute-api.us-east-1.amazonaws.com"


def generate_login_page(output_dir):
    """Generate the sign in page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign In — CollectorStream</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-primary: #0a0a0a;
    --bg-card: #151515;
    --border: #1f1f1f;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --danger: #ef4444;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}}
.top-bar {{ height: 3px; background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%); }}
.auth-wrapper {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
}}
.auth-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 40px;
    width: 100%;
    max-width: 420px;
}}
.logo {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 8px;
    text-decoration: none;
    color: var(--text-primary);
}}
.logo svg {{ width: 28px; height: 28px; color: var(--accent); }}
.logo span:last-child {{ color: var(--accent); }}
.auth-title {{
    font-size: 24px;
    font-weight: 600;
    text-align: center;
    margin: 24px 0 8px;
}}
.auth-subtitle {{
    text-align: center;
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: 32px;
}}
.auth-subtitle a {{ color: var(--accent); text-decoration: none; }}
.auth-subtitle a:hover {{ text-decoration: underline; }}
.form-group {{
    margin-bottom: 20px;
}}
.form-group label {{
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
}}
.form-group input {{
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s;
}}
.form-group input:focus {{
    border-color: var(--accent);
    outline: none;
}}
.form-group input::placeholder {{ color: var(--text-muted); }}
.btn {{
    width: 100%;
    padding: 14px;
    font-size: 15px;
    font-weight: 600;
    color: #000;
    background: var(--accent);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 8px;
}}
.btn:hover {{ background: var(--accent-dark); }}
.btn:disabled {{ background: var(--text-muted); cursor: not-allowed; }}
.msg {{
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    display: none;
}}
.msg.visible {{ display: block; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent); color: var(--accent); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
.divider {{
    display: flex;
    align-items: center;
    margin: 24px 0;
    color: var(--text-muted);
    font-size: 13px;
}}
.divider::before, .divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}}
.divider span {{ padding: 0 16px; }}
.back-link {{
    display: block;
    text-align: center;
    margin-top: 24px;
    color: var(--text-muted);
    font-size: 14px;
    text-decoration: none;
}}
.back-link:hover {{ color: var(--text-primary); }}
</style>
</head>
<body>
<div class="top-bar"></div>
<div class="auth-wrapper">
<div class="auth-card">
    <a href="/" class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Collector</span><span>Stream</span>
    </a>

    <h1 class="auth-title">Welcome back</h1>
    <p class="auth-subtitle">Don't have an account? <a href="signup.html">Sign up free</a></p>

    <div id="msg" class="msg"></div>

    <form onsubmit="login(event)">
        <div class="form-group">
            <label>Email address</label>
            <input type="email" id="email" placeholder="you@example.com" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" id="password" placeholder="Enter your password" required>
        </div>
        <button type="submit" class="btn">Sign In</button>
    </form>

    <a href="/" class="back-link">← Back to home</a>
</div>
</div>

<script>
const API = "{API_BASE}";

// Check if already logged in
if (localStorage.getItem("token")) {{
    const redirect = new URLSearchParams(location.search).get("redirect") || "/portfolio.html";
    location.href = redirect;
}}

function showMsg(text, isError) {{
    const el = document.getElementById("msg");
    el.className = "msg visible " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
}}

async function login(e) {{
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {{
        const res = await fetch(API + "/auth/login", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{email, password}})
        }});
        const data = await res.json();
        if (!res.ok) {{ showMsg(data.error || "Invalid email or password", true); return; }}
        localStorage.setItem("token", data.token);
        localStorage.setItem("email", data.email);
        localStorage.setItem("role", data.role || "user");
        const redirect = new URLSearchParams(location.search).get("redirect") || "/portfolio.html";
        location.href = redirect;
    }} catch (e) {{
        showMsg("Network error. Please try again.", true);
    }}
}}
</script>
</body>
</html>"""
    (output_dir / "login.html").write_text(html)


def generate_signup_page(output_dir):
    """Generate the sign up page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign Up — CollectorStream</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-primary: #0a0a0a;
    --bg-card: #151515;
    --border: #1f1f1f;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --danger: #ef4444;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}}
.top-bar {{ height: 3px; background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%); }}
.auth-wrapper {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
}}
.auth-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 40px;
    width: 100%;
    max-width: 420px;
}}
.logo {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 8px;
    text-decoration: none;
    color: var(--text-primary);
}}
.logo svg {{ width: 28px; height: 28px; color: var(--accent); }}
.logo span:last-child {{ color: var(--accent); }}
.auth-title {{
    font-size: 24px;
    font-weight: 600;
    text-align: center;
    margin: 24px 0 8px;
}}
.auth-subtitle {{
    text-align: center;
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: 32px;
}}
.auth-subtitle a {{ color: var(--accent); text-decoration: none; }}
.auth-subtitle a:hover {{ text-decoration: underline; }}
.form-group {{
    margin-bottom: 20px;
}}
.form-group label {{
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
}}
.form-group input {{
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s;
}}
.form-group input:focus {{
    border-color: var(--accent);
    outline: none;
}}
.form-group input::placeholder {{ color: var(--text-muted); }}
.form-hint {{
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 6px;
}}
.btn {{
    width: 100%;
    padding: 14px;
    font-size: 15px;
    font-weight: 600;
    color: #000;
    background: var(--accent);
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    margin-top: 8px;
}}
.btn:hover {{ background: var(--accent-dark); }}
.btn:disabled {{ background: var(--text-muted); cursor: not-allowed; }}
.msg {{
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    display: none;
}}
.msg.visible {{ display: block; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent); color: var(--accent); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
.features {{
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
}}
.features-title {{
    font-size: 13px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
}}
.feature-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 8px;
}}
.feature-item svg {{ width: 16px; height: 16px; color: var(--accent); flex-shrink: 0; }}
.back-link {{
    display: block;
    text-align: center;
    margin-top: 24px;
    color: var(--text-muted);
    font-size: 14px;
    text-decoration: none;
}}
.back-link:hover {{ color: var(--text-primary); }}
</style>
</head>
<body>
<div class="top-bar"></div>
<div class="auth-wrapper">
<div class="auth-card">
    <a href="/" class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Collector</span><span>Stream</span>
    </a>

    <h1 class="auth-title">Create your account</h1>
    <p class="auth-subtitle">Already have an account? <a href="login.html">Sign in</a></p>

    <div id="msg" class="msg"></div>

    <form onsubmit="register(event)">
        <div class="form-group">
            <label>Email address</label>
            <input type="email" id="email" placeholder="you@example.com" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" id="password" placeholder="Create a password" required minlength="8">
            <p class="form-hint">Must be at least 8 characters</p>
        </div>
        <div class="form-group">
            <label>Confirm password</label>
            <input type="password" id="confirm" placeholder="Confirm your password" required>
        </div>
        <button type="submit" class="btn">Create Free Account</button>
    </form>

    <div class="features">
        <div class="features-title">What you get — free forever</div>
        <div class="feature-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Track your card portfolio value
        </div>
        <div class="feature-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Daily buy/sell signals
        </div>
        <div class="feature-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Save favorite prospects to watchlist
        </div>
    </div>

    <a href="/" class="back-link">← Back to home</a>
</div>
</div>

<script>
const API = "{API_BASE}";

// Check if already logged in
if (localStorage.getItem("token")) {{
    location.href = "/portfolio.html";
}}

function showMsg(text, isError) {{
    const el = document.getElementById("msg");
    el.className = "msg visible " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
}}

async function register(e) {{
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirm").value;

    if (password !== confirm) {{ showMsg("Passwords do not match", true); return; }}

    try {{
        const res = await fetch(API + "/auth/register", {{
            method: "POST",
            headers: {{"Content-Type": "application/json"}},
            body: JSON.stringify({{email, password}})
        }});
        const data = await res.json();
        if (!res.ok) {{ showMsg(data.error || "Registration failed", true); return; }}
        localStorage.setItem("token", data.token);
        localStorage.setItem("email", data.email);
        localStorage.setItem("role", data.role || "user");
        location.href = "/portfolio.html";
    }} catch (e) {{
        showMsg("Network error. Please try again.", true);
    }}
}}
</script>
</body>
</html>"""
    (output_dir / "signup.html").write_text(html)


def generate_profile_page(output_dir):
    """Generate the user profile page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile — CollectorStream</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-primary: #0a0a0a;
    --bg-secondary: #111111;
    --bg-card: #151515;
    --border: #1f1f1f;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --danger: #ef4444;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}}
.top-bar {{ height: 3px; background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%); }}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
}}
.logo {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
}}
.logo svg {{ width: 20px; height: 20px; color: var(--accent); }}
.logo span:last-child {{ color: var(--accent); }}
.header-actions {{ display: flex; align-items: center; gap: 16px; }}
.btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
}}
.btn-primary {{ background: var(--accent); color: #000; }}
.btn-primary:hover {{ background: var(--accent-dark); }}
.btn-outline {{ background: transparent; color: var(--text-secondary); border: 1px solid var(--border); }}
.btn-outline:hover {{ border-color: var(--accent); color: var(--accent); }}
.btn-danger {{ background: rgba(239, 68, 68, 0.1); color: var(--danger); border: 1px solid var(--danger); }}
.btn-danger:hover {{ background: var(--danger); color: #fff; }}
.container {{
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 32px;
}}
.page-title {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
}}
.page-subtitle {{
    color: var(--text-secondary);
    font-size: 15px;
    margin-bottom: 32px;
}}
.card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}}
.card-title {{
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
}}
.form-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 16px;
}}
.form-group {{
    margin-bottom: 16px;
}}
.form-group.full {{
    grid-column: 1 / -1;
}}
.form-group label {{
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
}}
.form-group input, .form-group select, .form-group textarea {{
    width: 100%;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    color: var(--text-primary);
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.2s;
}}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {{
    border-color: var(--accent);
    outline: none;
}}
.form-group input::placeholder {{ color: var(--text-muted); }}
.form-group input:disabled {{
    background: var(--bg-secondary);
    color: var(--text-muted);
    cursor: not-allowed;
}}
.msg {{
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    display: none;
}}
.msg.visible {{ display: block; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent); color: var(--accent); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
.admin-section {{
    display: none;
    margin-top: 32px;
    padding-top: 32px;
    border-top: 1px solid var(--border);
}}
.admin-section.visible {{ display: block; }}
.admin-section h2 {{
    font-size: 20px;
    font-weight: 600;
    color: var(--danger);
    margin-bottom: 16px;
}}
.user-table {{
    width: 100%;
    border-collapse: collapse;
}}
.user-table th {{
    text-align: left;
    padding: 12px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
}}
.user-table td {{
    padding: 12px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
}}
.role-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}
.role-admin {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
.role-user {{ background: var(--bg-secondary); color: var(--text-muted); }}
.profile-pic-section {{
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
}}
.profile-pic-preview {{
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: var(--bg-secondary);
    border: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
}}
.profile-pic-preview img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
}}
.profile-pic-preview svg {{
    width: 40px;
    height: 40px;
    color: var(--text-muted);
}}
.profile-pic-actions {{
    display: flex;
    flex-direction: column;
    gap: 8px;
}}
.profile-pic-actions h4 {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
}}
.profile-pic-actions p {{
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 8px;
}}
.file-input-wrapper {{
    position: relative;
    overflow: hidden;
    display: inline-block;
}}
.file-input-wrapper input[type="file"] {{
    position: absolute;
    left: 0;
    top: 0;
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
}}
.btn-sm {{
    padding: 6px 14px;
    font-size: 13px;
}}
</style>
</head>
<body>
<div class="top-bar"></div>
<header class="header">
    <a href="/" class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Collector</span><span>Stream</span>
    </a>
    <div class="header-actions">
        <a href="/portfolio.html" class="btn btn-outline">Portfolio</a>
        <button onclick="logout()" class="btn btn-danger">Sign Out</button>
    </div>
</header>

<div class="container">
    <h1 class="page-title">Account Settings</h1>
    <p class="page-subtitle">Manage your profile and preferences</p>

    <div id="profileMsg" class="msg"></div>

    <!-- Profile Picture -->
    <div class="card">
        <h3 class="card-title">Profile Picture</h3>
        <div class="profile-pic-section">
            <div class="profile-pic-preview" id="profilePicPreview">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" id="defaultPicIcon">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                </svg>
            </div>
            <div class="profile-pic-actions">
                <h4>Upload a new photo</h4>
                <p>JPG, PNG or GIF. Max 2MB.</p>
                <div style="display: flex; gap: 8px;">
                    <div class="file-input-wrapper">
                        <button type="button" class="btn btn-outline btn-sm">Choose File</button>
                        <input type="file" id="profilePicInput" accept="image/jpeg,image/png,image/gif" onchange="handleProfilePic(this)">
                    </div>
                    <button type="button" class="btn btn-outline btn-sm" onclick="removeProfilePic()" id="removePicBtn" style="display:none;">Remove</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Profile Info -->
    <div class="card">
        <h3 class="card-title">Profile Information</h3>
        <form onsubmit="saveProfile(event)">
            <div class="form-group">
                <label>Email address</label>
                <input type="email" id="email" disabled>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>First name</label>
                    <input type="text" id="firstName" placeholder="Enter first name">
                </div>
                <div class="form-group">
                    <label>Last name</label>
                    <input type="text" id="lastName" placeholder="Enter last name">
                </div>
            </div>
            <div class="form-group">
                <label>Display name</label>
                <input type="text" id="displayName" placeholder="How should we call you?">
            </div>
            <button type="submit" class="btn btn-primary">Save Changes</button>
        </form>
    </div>

    <!-- Change Password -->
    <div class="card">
        <h3 class="card-title">Change Password</h3>
        <div id="passwordMsg" class="msg"></div>
        <form onsubmit="changePassword(event)">
            <div class="form-group">
                <label>Current password</label>
                <input type="password" id="currentPassword" placeholder="Enter current password" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>New password</label>
                    <input type="password" id="newPassword" placeholder="Enter new password" required minlength="8">
                </div>
                <div class="form-group">
                    <label>Confirm new password</label>
                    <input type="password" id="confirmPassword" placeholder="Confirm new password" required>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Update Password</button>
        </form>
    </div>

    <!-- Admin Section -->
    <div id="adminSection" class="admin-section">
        <h2>Admin Panel</h2>

        <div class="card">
            <h3 class="card-title">User Management</h3>
            <table class="user-table">
                <thead>
                    <tr>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="userTableBody">
                    <tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Loading users...</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3 class="card-title">Quick Actions</h3>
            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <a href="/private/" class="btn btn-outline">Pipeline Dashboard</a>
                <a href="/admin/users.html" class="btn btn-outline">Full User Admin</a>
            </div>
        </div>
    </div>
</div>

<script>
const API = "{API_BASE}";

// Check auth
const token = localStorage.getItem("token");
const email = localStorage.getItem("email");
const role = localStorage.getItem("role");

if (!token) {{
    location.href = "/login.html?redirect=/profile.html";
}}

// Populate email
document.getElementById("email").value = email || "";

// Show admin section if admin
if (role === "admin") {{
    document.getElementById("adminSection").classList.add("visible");
    loadUsers();
}}

function showMsg(id, text, isError) {{
    const el = document.getElementById(id);
    el.className = "msg visible " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
    setTimeout(() => el.classList.remove("visible"), 5000);
}}

async function saveProfile(e) {{
    e.preventDefault();
    const firstName = document.getElementById("firstName").value;
    const lastName = document.getElementById("lastName").value;
    const displayName = document.getElementById("displayName").value;

    // TODO: Implement profile save API
    showMsg("profileMsg", "Profile saved successfully!", false);
}}

async function changePassword(e) {{
    e.preventDefault();
    const currentPassword = document.getElementById("currentPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    if (newPassword !== confirmPassword) {{
        showMsg("passwordMsg", "New passwords do not match", true);
        return;
    }}

    try {{
        const res = await fetch(API + "/auth/change-password", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            }},
            body: JSON.stringify({{
                current_password: currentPassword,
                new_password: newPassword
            }})
        }});
        const data = await res.json();
        if (!res.ok) {{
            showMsg("passwordMsg", data.error || "Failed to change password", true);
            return;
        }}
        showMsg("passwordMsg", "Password changed successfully!", false);
        document.getElementById("currentPassword").value = "";
        document.getElementById("newPassword").value = "";
        document.getElementById("confirmPassword").value = "";
    }} catch (e) {{
        showMsg("passwordMsg", "Network error. Please try again.", true);
    }}
}}

async function loadUsers() {{
    try {{
        const res = await fetch(API + "/admin/users", {{
            headers: {{ "Authorization": "Bearer " + token }}
        }});
        if (!res.ok) return;
        const users = await res.json();
        const tbody = document.getElementById("userTableBody");
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${{u.email}}</td>
                <td><span class="role-badge role-${{u.role}}">${{u.role}}</span></td>
                <td>${{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}}</td>
                <td>
                    ${{u.role !== 'admin' ? `<button onclick="deleteUser('${{u.email}}')" class="btn btn-danger" style="padding: 4px 12px; font-size: 12px;">Delete</button>` : ''}}
                </td>
            </tr>
        `).join("");
    }} catch (e) {{
        console.error("Failed to load users", e);
    }}
}}

async function deleteUser(userEmail) {{
    if (!confirm("Delete user " + userEmail + "?")) return;
    try {{
        const res = await fetch(API + "/admin/users/" + encodeURIComponent(userEmail), {{
            method: "DELETE",
            headers: {{ "Authorization": "Bearer " + token }}
        }});
        if (res.ok) loadUsers();
    }} catch (e) {{
        alert("Failed to delete user");
    }}
}}

// Profile Picture Functions
function loadProfilePic() {{
    const pic = localStorage.getItem("profilePic");
    if (pic) {{
        showProfilePic(pic);
    }}
}}

function showProfilePic(dataUrl) {{
    const preview = document.getElementById("profilePicPreview");
    const icon = document.getElementById("defaultPicIcon");
    const removeBtn = document.getElementById("removePicBtn");

    // Remove existing image if any
    const existingImg = preview.querySelector("img");
    if (existingImg) existingImg.remove();

    // Create and add new image
    const img = document.createElement("img");
    img.src = dataUrl;
    img.alt = "Profile";
    preview.appendChild(img);

    // Hide default icon, show remove button
    if (icon) icon.style.display = "none";
    if (removeBtn) removeBtn.style.display = "inline-block";
}}

function handleProfilePic(input) {{
    const file = input.files[0];
    if (!file) return;

    // Validate file size (2MB max)
    if (file.size > 2 * 1024 * 1024) {{
        showMsg("profileMsg", "Image must be less than 2MB", true);
        input.value = "";
        return;
    }}

    // Validate file type
    if (!file.type.match(/^image\/(jpeg|png|gif)$/)) {{
        showMsg("profileMsg", "Please upload a JPG, PNG, or GIF image", true);
        input.value = "";
        return;
    }}

    const reader = new FileReader();
    reader.onload = function(e) {{
        const dataUrl = e.target.result;

        // Resize image to reduce storage size
        resizeImage(dataUrl, 200, 200, function(resizedDataUrl) {{
            localStorage.setItem("profilePic", resizedDataUrl);
            showProfilePic(resizedDataUrl);
            showMsg("profileMsg", "Profile picture updated!", false);
        }});
    }};
    reader.readAsDataURL(file);
}}

function resizeImage(dataUrl, maxWidth, maxHeight, callback) {{
    const img = new Image();
    img.onload = function() {{
        let width = img.width;
        let height = img.height;

        // Calculate new dimensions
        if (width > height) {{
            if (width > maxWidth) {{
                height = height * maxWidth / width;
                width = maxWidth;
            }}
        }} else {{
            if (height > maxHeight) {{
                width = width * maxHeight / height;
                height = maxHeight;
            }}
        }}

        // Create canvas and resize
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);

        callback(canvas.toDataURL("image/jpeg", 0.8));
    }};
    img.src = dataUrl;
}}

function removeProfilePic() {{
    localStorage.removeItem("profilePic");

    const preview = document.getElementById("profilePicPreview");
    const icon = document.getElementById("defaultPicIcon");
    const removeBtn = document.getElementById("removePicBtn");

    // Remove image
    const img = preview.querySelector("img");
    if (img) img.remove();

    // Show default icon, hide remove button
    if (icon) icon.style.display = "block";
    if (removeBtn) removeBtn.style.display = "none";

    showMsg("profileMsg", "Profile picture removed", false);
}}

// Load profile pic on page load
loadProfilePic();

function logout() {{
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    localStorage.removeItem("profilePic");
    location.href = "/";
}}
</script>
</body>
</html>"""
    (output_dir / "profile.html").write_text(html)


def generate_portfolio_page(output_dir):
    """Generate the portfolio management page with JWT auth (client-side rendered)."""
    import json
    from db.models import get_all_player_names

    player_names = get_all_player_names()
    player_names_js = json.dumps(player_names)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio — CollectorStream</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
    --bg-primary: #0a0a0a;
    --bg-secondary: #111111;
    --bg-card: #151515;
    --border: #1f1f1f;
    --accent: #10b981;
    --accent-dark: #059669;
    --text-primary: #ffffff;
    --text-secondary: #9ca3af;
    --text-muted: #6b7280;
    --success: #10b981;
    --danger: #ef4444;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}}
.top-bar {{ height: 3px; background: linear-gradient(90deg, var(--accent) 0%, var(--accent-dark) 100%); }}
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
}}
.logo {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
    text-decoration: none;
}}
.logo svg {{ width: 20px; height: 20px; color: var(--accent); }}
.logo span:last-child {{ color: var(--accent); }}
.header-nav {{ display: flex; gap: 8px; }}
.header-nav a {{
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.2s;
}}
.header-nav a:hover {{ color: var(--text-primary); background: var(--bg-card); }}
.header-nav a.active {{ color: var(--accent); background: rgba(16, 185, 129, 0.1); }}
.header-actions {{ display: flex; align-items: center; gap: 12px; }}
.profile-btn {{
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
}}
.profile-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
.profile-btn img {{ width: 100%; height: 100%; object-fit: cover; }}
.profile-btn svg {{ flex-shrink: 0; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 32px; }}
h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); }}
h2 {{ font-size: 20px; font-weight: 600; margin: 32px 0 16px; color: var(--text-primary); }}
.subtitle {{ color: var(--text-secondary); font-size: 15px; margin-bottom: 24px; }}
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
.stat-card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
.stat-value {{ font-size: 28px; font-weight: 700; color: var(--accent); }}
.stat-label {{ font-size: 13px; color: var(--text-muted); margin-top: 4px; }}
.form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
.form-group {{ display: flex; flex-direction: column; }}
.form-group label {{ font-size: 12px; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
.form-group input, .form-group select, .form-group textarea {{
    background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary);
    padding: 10px 14px; border-radius: 8px; font-size: 14px;
}}
.form-group input:focus, .form-group select:focus {{ border-color: var(--accent); outline: none; }}
.form-group.full {{ grid-column: 1 / -1; }}
.checkbox-group {{ display: flex; gap: 20px; align-items: center; grid-column: 1 / -1; padding: 8px 0; }}
.checkbox-group label {{ display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-secondary); cursor: pointer; }}
.checkbox-group input[type="checkbox"] {{ width: 16px; height: 16px; accent-color: var(--accent); }}
.numbered-fields {{ display: none; grid-template-columns: 1fr 1fr; gap: 12px; grid-column: 1 / -1; }}
.numbered-fields.visible {{ display: grid; }}
.radio-group {{ display: flex; gap: 20px; }}
.radio-group label {{ display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-secondary); cursor: pointer; }}
.radio-group input[type="radio"] {{ width: 16px; height: 16px; accent-color: var(--accent); }}
.graded-fields {{ display: none; grid-template-columns: 1fr 1fr; gap: 12px; grid-column: 1 / -1; }}
.graded-fields.visible {{ display: grid; }}
.graded-fields .checkbox-group {{ grid-column: 1 / -1; }}
.raw-fields {{ display: grid; grid-template-columns: 1fr; gap: 12px; grid-column: 1 / -1; }}
.raw-fields.hidden {{ display: none; }}
.btn {{ display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; font-size: 14px; font-weight: 600; color: #000; background: var(--accent); border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s; }}
.btn:hover {{ background: var(--accent-dark); }}
.btn:disabled {{ background: var(--text-muted); cursor: not-allowed; }}
.btn-sm {{ padding: 6px 12px; font-size: 12px; background: var(--bg-card); color: var(--text-secondary); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; }}
.btn-sm:hover {{ border-color: var(--accent); color: var(--accent); }}
.btn-del {{ border-color: var(--danger); color: var(--danger); }}
.btn-del:hover {{ background: var(--danger); color: #fff; }}
.btn-sold {{ border-color: #f59e0b; color: #f59e0b; margin-right: 6px; }}
.btn-sold:hover {{ background: #f59e0b; color: #000; }}
.badge-sell {{ background: var(--danger); color: #fff; }}
.badge-sold {{ background: #f59e0b; color: #000; }}
.row-sold {{ opacity: 0.7; background: rgba(245, 158, 11, 0.05); }}
.row-sold td:not(:last-child) {{ text-decoration: line-through; text-decoration-color: var(--text-muted); }}
.modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); align-items: center; justify-content: center; z-index: 1000; }}
.modal.visible {{ display: flex; }}
.modal-content {{ background: var(--bg-card); padding: 24px; border-radius: 12px; max-width: 400px; width: 90%; border: 1px solid var(--border); }}
.modal-content h3 {{ margin-bottom: 16px; color: var(--text-primary); }}
.modal-content .form-group {{ margin-bottom: 16px; }}
.modal-buttons {{ display: flex; gap: 12px; margin-top: 20px; }}
.collapsible {{ cursor: pointer; user-select: none; }}
.collapsible::after {{ content: " +"; color: var(--accent); }}
.collapsible.open::after {{ content: " −"; }}
.form-container {{ display: none; margin-top: 15px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }}
.form-container.visible {{ display: block; }}
.msg {{ padding: 12px 16px; border-radius: 8px; margin: 10px 0; font-size: 14px; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--accent); color: var(--accent); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
.loading {{ text-align: center; padding: 40px; color: var(--text-muted); }}
.sort-bar {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 15px; align-items: center; }}
.sort-bar span {{ color: var(--text-muted); font-size: 13px; margin-right: 5px; }}
.sort-btn {{ padding: 6px 12px; font-size: 12px; background: var(--bg-card); border: 1px solid var(--border); color: var(--text-secondary); border-radius: 6px; cursor: pointer; transition: all 0.2s; }}
.sort-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
.sort-btn.active {{ background: var(--accent); color: #000; border-color: var(--accent); }}
.sort-btn.asc::after {{ content: " ▲"; font-size: 10px; }}
.sort-btn.desc::after {{ content: " ▼"; font-size: 10px; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; padding: 12px; font-size: 12px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; background: var(--bg-secondary); border-bottom: 1px solid var(--border); }}
td {{ padding: 12px; border-bottom: 1px solid var(--border); font-size: 14px; }}
tr:hover {{ background: rgba(16, 185, 129, 0.02); }}
.data-table-container {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
</style>
</head>
<body>
<div class="top-bar"></div>
<header class="header">
    <a href="/" class="logo">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        <span>Collector</span><span>Stream</span>
    </a>
    <nav class="header-nav">
        <a href="/">Home</a>
        <a href="players-2026.html">2026 Prospects</a>
        <a href="buy-signals.html">Buy Signals</a>
        <a href="watchlist.html">Watchlist</a>
        <a href="portfolio.html" class="active">Portfolio</a>
    </nav>
    <div class="header-actions">
        <a href="profile.html" class="profile-btn" id="headerProfileBtn" title="Account settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18" id="headerProfileIcon">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
            </svg>
        </a>
    </div>
</header>
<script>
// Load profile picture in header
(function() {{
    const pic = localStorage.getItem("profilePic");
    if (pic) {{
        const btn = document.getElementById("headerProfileBtn");
        const icon = document.getElementById("headerProfileIcon");
        if (btn && icon) {{
            const img = document.createElement("img");
            img.src = pic;
            img.alt = "Profile";
            icon.style.display = "none";
            btn.appendChild(img);
        }}
    }}
}})();
</script>

<div class="container">

<h1>Card Portfolio</h1>
<p class="subtitle">Track your personal card investments with buy/sell signals</p>

<div class="stats-grid" id="statsGrid">
  <div class="stat-card"><div class="stat-value" id="statCards">0</div><div class="stat-label">Cards Owned</div></div>
  <div class="stat-card"><div class="stat-value" id="statInvested">$0.00</div><div class="stat-label">Total Invested</div></div>
  <div class="stat-card"><div class="stat-value" id="statCurrent">$0.00</div><div class="stat-label">Current Value</div></div>
  <div class="stat-card"><div class="stat-value" id="statGainLoss" style="color:#00c853">$+0.00</div><div class="stat-label" id="statPct">Unrealized (+0.0%)</div></div>
  <div class="stat-card"><div class="stat-value" id="statSold">0</div><div class="stat-label">Cards Sold</div></div>
  <div class="stat-card"><div class="stat-value" id="statRealized" style="color:#f59e0b">$0.00</div><div class="stat-label">Realized Profit</div></div>
</div>

<h2 class="collapsible" onclick="toggleForm()">Add Card</h2>
<div class="form-container" id="formContainer">
<div id="formMsg"></div>
<div class="form-grid">
  <div class="form-group">
    <label>Player Name *</label>
    <input type="text" id="player_name" list="playerList" placeholder="e.g. JuJu Watkins">
    <datalist id="playerList"></datalist>
  </div>
  <div class="form-group"><label>Card Year *</label><input type="number" id="card_year" value="2024" min="1900" max="2100"></div>
  <div class="form-group">
    <label>Manufacturer *</label>
    <select id="manufacturer">
      <option value="">Select...</option>
      <option>Panini</option><option>Topps</option><option>Leaf</option>
      <option>Donruss</option><option>Bowman</option><option>Upper Deck</option>
      <option>Hoops</option><option>Fleer</option><option>Sage</option>
      <option>Press Pass</option><option>SP Authentic</option>
      <option>Immaculate</option><option>National Treasures</option><option>Other</option>
    </select>
  </div>
  <div class="form-group"><label>Set Name *</label><input type="text" id="set_name" placeholder="e.g. Prizm, Contenders"></div>
  <div class="form-group"><label>Card Number</label><input type="text" id="card_number" placeholder="e.g. 125, RC-1"></div>
  <div class="form-group"><label>Parallel / Variant</label><input type="text" id="parallel" placeholder="e.g. Silver, Pink Shimmer" value="Base"></div>
  <div class="checkbox-group">
    <label><input type="checkbox" id="is_numbered" onchange="toggleNumbered()"> Numbered Card</label>
    <label><input type="checkbox" id="is_autograph"> Autograph</label>
    <label><input type="checkbox" id="is_rookie"> Rookie Card</label>
  </div>
  <div class="numbered-fields" id="numberedFields">
    <div class="form-group"><label>Numbered To (e.g. 100 for /100)</label><input type="number" id="numbered_to" placeholder="100"></div>
    <div class="form-group"><label>Serial Number (e.g. 3 for 3/100)</label><input type="number" id="serial_number" placeholder="3"></div>
  </div>
  <div class="form-group full">
    <label>Card Condition</label>
    <div class="radio-group">
      <label><input type="radio" name="condition_type" value="raw" checked onchange="toggleConditionType()"> Raw (Ungraded)</label>
      <label><input type="radio" name="condition_type" value="graded" onchange="toggleConditionType()"> Graded (Slabbed)</label>
    </div>
  </div>
  <div class="graded-fields" id="gradedFields">
    <div class="form-group">
      <label>Grading Company</label>
      <select id="grading_company">
        <option value="PSA">PSA</option>
        <option value="BGS">BGS (Beckett)</option>
        <option value="SGC">SGC</option>
        <option value="CGC">CGC</option>
        <option value="CSG">CSG</option>
        <option value="HGA">HGA</option>
        <option value="Other">Other</option>
      </select>
    </div>
    <div class="form-group">
      <label>Grade</label>
      <select id="grade_number">
        <option value="10">10 (Gem Mint)</option>
        <option value="9.5">9.5</option>
        <option value="9">9 (Mint)</option>
        <option value="8.5">8.5</option>
        <option value="8">8 (NM-MT)</option>
        <option value="7.5">7.5</option>
        <option value="7">7 (NM)</option>
        <option value="6.5">6.5</option>
        <option value="6">6 (EX-MT)</option>
        <option value="5">5 (EX)</option>
        <option value="4">4 (VG-EX)</option>
        <option value="3">3 (VG)</option>
        <option value="2">2 (Good)</option>
        <option value="1.5">1.5</option>
        <option value="1">1 (Poor)</option>
        <option value="A">Authentic (A)</option>
      </select>
    </div>
    <div class="checkbox-group">
      <label><input type="checkbox" id="auto_authenticated"> Auto Authenticated by Grading Company</label>
    </div>
  </div>
  <div class="raw-fields" id="rawFields">
    <div class="form-group">
      <label>Estimated Condition</label>
      <select id="raw_condition">
        <option value="Mint">Mint</option>
        <option value="Near Mint" selected>Near Mint</option>
        <option value="Excellent">Excellent</option>
        <option value="Very Good">Very Good</option>
        <option value="Good">Good</option>
        <option value="Fair">Fair</option>
        <option value="Poor">Poor</option>
      </select>
    </div>
  </div>
  <div class="form-group"><label>Purchase Price</label><input type="number" id="purchase_price" step="0.01" placeholder="Leave blank for Card Ladder avg"></div>
  <div class="form-group"><label>Purchase Date</label><input type="date" id="purchase_date"></div>
  <div class="form-group full"><label>Notes</label><textarea id="notes" rows="2" placeholder="Optional notes"></textarea></div>
</div>
<button class="btn" id="addBtn" onclick="addCard()">Add Card</button>
</div>

<h2>Holdings</h2>
<div class="sort-bar">
  <span>Sort by:</span>
  <button class="sort-btn active desc" onclick="sortCards('player_name')">Player</button>
  <button class="sort-btn" onclick="sortCards('manufacturer')">Manufacturer</button>
  <button class="sort-btn" onclick="sortCards('set_name')">Set</button>
  <button class="sort-btn" onclick="sortCards('purchase_price')">Purchased</button>
  <button class="sort-btn" onclick="sortCards('current_price')">Current</button>
  <button class="sort-btn" onclick="sortCards('gain_loss')">Gain/Loss</button>
  <button class="sort-btn" onclick="sortCards('signal')">Signal</button>
</div>
<div id="cardsTable"><p class="loading">Loading portfolio...</p></div>

<!-- Mark as Sold Modal -->
<div class="modal" id="soldModal">
  <div class="modal-content">
    <h3>Mark Card as Sold</h3>
    <p id="soldCardName" style="color:var(--text-secondary);margin-bottom:16px;"></p>
    <div class="form-group">
      <label>Sale Price</label>
      <input type="number" id="salePrice" step="0.01" placeholder="Enter sale price">
    </div>
    <div class="form-group">
      <label>Date Sold</label>
      <input type="date" id="saleDate">
    </div>
    <div class="modal-buttons">
      <button class="btn" onclick="submitSold()">Mark as Sold</button>
      <button class="btn-sm" onclick="closeSoldModal()">Cancel</button>
    </div>
  </div>
</div>

<script>
const API = "{API_BASE}";
const PLAYERS = {player_names_js};
let allCards = [];
let currentSort = {{ field: 'player_name', dir: 'asc' }};

// Auth guard
const token = localStorage.getItem("token");
if (!token) {{ location.href = "/login.html?redirect=/portfolio.html"; }}

// Verify token
fetch(API + "/auth/me", {{headers: {{"Authorization": "Bearer " + token}}}})
.then(r => {{
    if (!r.ok) {{ localStorage.clear(); location.href = "/login.html?redirect=/portfolio.html"; }}
    return r.json();
}})
.then(data => {{
    document.getElementById("userEmail").textContent = data.email;
    document.getElementById("userRole").textContent = data.role;
    loadPortfolio();
}});

function logout() {{
    localStorage.clear();
    location.href = "/login.html";
}}

// Populate player autocomplete
const dl = document.getElementById("playerList");
PLAYERS.forEach(p => {{ const o = document.createElement("option"); o.value = p; dl.appendChild(o); }});

function toggleForm() {{
    document.querySelector(".collapsible").classList.toggle("open");
    document.getElementById("formContainer").classList.toggle("visible");
}}

function toggleNumbered() {{
    document.getElementById("numberedFields").classList.toggle("visible", document.getElementById("is_numbered").checked);
}}

function toggleConditionType() {{
    const isGraded = document.querySelector('input[name="condition_type"]:checked').value === 'graded';
    document.getElementById("gradedFields").classList.toggle("visible", isGraded);
    document.getElementById("rawFields").classList.toggle("hidden", isGraded);
}}

function getGradeValue() {{
    const isGraded = document.querySelector('input[name="condition_type"]:checked').value === 'graded';
    if (isGraded) {{
        const company = document.getElementById("grading_company").value;
        const grade = document.getElementById("grade_number").value;
        const autoAuth = document.getElementById("auto_authenticated").checked;
        let result = company + " " + grade;
        if (autoAuth) result += " Auto";
        return result;
    }} else {{
        return "Raw - " + document.getElementById("raw_condition").value;
    }}
}}

function showMsg(text, isError) {{
    const el = document.getElementById("formMsg");
    el.className = "msg " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
    setTimeout(() => el.textContent = "", 5000);
}}

async function loadPortfolio() {{
    try {{
        const res = await fetch(API + "/portfolio", {{
            headers: {{"Authorization": "Bearer " + token}}
        }});
        if (!res.ok) throw new Error("Failed to load portfolio");
        const data = await res.json();
        renderStats(data);
        allCards = data.cards || [];
        sortCards(currentSort.field, true);
    }} catch (e) {{
        document.getElementById("cardsTable").innerHTML = '<p class="empty-state">Error loading portfolio: ' + e.message + '</p>';
    }}
}}

function sortCards(field, skipToggle) {{
    // Update sort direction
    if (!skipToggle && currentSort.field === field) {{
        currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
    }} else if (!skipToggle) {{
        currentSort.field = field;
        currentSort.dir = 'asc';
    }}

    // Update button states
    document.querySelectorAll('.sort-btn').forEach(btn => {{
        btn.classList.remove('active', 'asc', 'desc');
    }});
    const activeBtn = document.querySelector(`.sort-btn[onclick="sortCards('${{field}}')"]`);
    if (activeBtn) {{
        activeBtn.classList.add('active', currentSort.dir);
    }}

    // Sort cards
    const sorted = [...allCards].sort((a, b) => {{
        let valA, valB;
        if (field === 'current_price') {{
            valA = (a.trends && a.trends.current_price) || 0;
            valB = (b.trends && b.trends.current_price) || 0;
        }} else if (field === 'gain_loss') {{
            valA = (a.trends && a.trends.gain_loss) || 0;
            valB = (b.trends && b.trends.gain_loss) || 0;
        }} else if (field === 'signal') {{
            valA = (a.trends && a.trends.signal) || 'HOLD';
            valB = (b.trends && b.trends.signal) || 'HOLD';
        }} else {{
            valA = a[field] || '';
            valB = b[field] || '';
        }}

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();

        let cmp = 0;
        if (valA < valB) cmp = -1;
        else if (valA > valB) cmp = 1;

        return currentSort.dir === 'asc' ? cmp : -cmp;
    }});

    renderCards(sorted);
}}

function renderStats(data) {{
    // Calculate stats from cards data
    const cards = data.cards || [];
    const activeCards = cards.filter(c => !c.sold_date && !c.sold_price);
    const soldCards = cards.filter(c => c.sold_date || c.sold_price);

    document.getElementById("statCards").textContent = activeCards.length;
    document.getElementById("statInvested").textContent = "$" + (data.total_invested || 0).toFixed(2);
    document.getElementById("statCurrent").textContent = "$" + (data.total_current || 0).toFixed(2);

    const gl = data.unrealized_gain_loss || 0;
    document.getElementById("statGainLoss").textContent = "$" + (gl >= 0 ? "+" : "") + gl.toFixed(2);
    document.getElementById("statGainLoss").style.color = gl >= 0 ? "#00c853" : "#ff1744";
    document.getElementById("statPct").textContent = "Unrealized (" + (gl >= 0 ? "+" : "") + (data.unrealized_pct || 0).toFixed(1) + "%)";

    // Calculate realized gains from sold cards
    document.getElementById("statSold").textContent = soldCards.length;
    let realizedProfit = 0;
    soldCards.forEach(c => {{
        if (c.sold_price && c.purchase_price) {{
            realizedProfit += c.sold_price - c.purchase_price;
        }}
    }});
    document.getElementById("statRealized").textContent = "$" + (realizedProfit >= 0 ? "+" : "") + realizedProfit.toFixed(2);
    document.getElementById("statRealized").style.color = realizedProfit >= 0 ? "#10b981" : "#ef4444";
}}

function renderCards(cards) {{
    if (!cards.length) {{
        document.getElementById("cardsTable").innerHTML = "<p class='empty-state'>No cards yet. Click 'Add Card' above to get started.</p>";
        return;
    }}
    let html = '<table><tr><th>Player</th><th>Card</th><th>Purchased</th><th>Current/Sold</th><th>Gain/Loss</th><th>Status</th><th>Actions</th></tr>';
    cards.forEach(c => {{
        const desc = c.description || "";
        const purchase = c.purchase_price ? "$" + c.purchase_price.toFixed(2) : "-";
        const t = c.trends || {{}};
        const isSold = c.sold_date || c.sold_price;
        const rowClass = isSold ? ' class="row-sold"' : '';

        let priceHtml = "-";
        let glHtml = "-";
        let statusHtml = "";

        if (isSold) {{
            priceHtml = c.sold_price ? "$" + c.sold_price.toFixed(2) : "-";
            if (c.sold_price && c.purchase_price) {{
                const gl = c.sold_price - c.purchase_price;
                const pct = (gl / c.purchase_price) * 100;
                const cls = gl >= 0 ? "rising" : "falling";
                glHtml = '<span class="' + cls + '">$' + (gl >= 0 ? "+" : "") + gl.toFixed(2) + ' (' + (pct >= 0 ? "+" : "") + pct.toFixed(1) + '%)</span>';
            }}
            const soldDate = c.sold_date ? new Date(c.sold_date).toLocaleDateString() : "";
            statusHtml = '<span class="badge badge-sold">SOLD</span>' + (soldDate ? '<br><small style="color:var(--text-muted)">' + soldDate + '</small>' : '');
        }} else {{
            priceHtml = t.current_price ? "$" + t.current_price.toFixed(2) : "-";
            if (t.gain_loss != null) {{
                const gl = t.gain_loss;
                const pct = t.gain_loss_pct || 0;
                const cls = gl >= 0 ? "rising" : "falling";
                glHtml = '<span class="' + cls + '">$' + (gl >= 0 ? "+" : "") + gl.toFixed(2) + ' (' + (pct >= 0 ? "+" : "") + pct.toFixed(1) + '%)</span>';
            }}
            const sig = t.signal || "HOLD";
            const sigCls = sig === "SELL" ? "badge-sell" : "badge-rising";
            statusHtml = '<span class="badge ' + sigCls + '">' + sig + '</span>';
        }}

        let actionsHtml = '';
        if (!isSold) {{
            actionsHtml = '<button class="btn-sm btn-sold" onclick="openSoldModal(' + c.id + ', \\'' + (c.player_name || "").replace(/'/g, "\\\\'") + ' - ' + desc.replace(/'/g, "\\\\'") + '\\')">Sold</button>';
        }}
        actionsHtml += '<button class="btn-sm btn-del" onclick="deleteCard(' + c.id + ')">Delete</button>';

        html += '<tr' + rowClass + '><td class="player-name">' + (c.player_name || "") + '</td><td>' + desc +
                '</td><td class="avg-rank">' + purchase + '</td><td class="avg-rank">' + priceHtml +
                '</td><td>' + glHtml + '</td><td>' + statusHtml +
                '</td><td>' + actionsHtml + '</td></tr>';
    }});
    html += '</table>';
    document.getElementById("cardsTable").innerHTML = html;
}}

async function addCard() {{
    const btn = document.getElementById("addBtn");
    btn.disabled = true; btn.textContent = "Submitting...";

    const data = {{
        player_name: document.getElementById("player_name").value,
        card_year: parseInt(document.getElementById("card_year").value),
        manufacturer: document.getElementById("manufacturer").value,
        set_name: document.getElementById("set_name").value,
        card_number: document.getElementById("card_number").value,
        parallel: document.getElementById("parallel").value || "Base",
        is_numbered: document.getElementById("is_numbered").checked ? 1 : 0,
        numbered_to: parseInt(document.getElementById("numbered_to").value) || null,
        serial_number: parseInt(document.getElementById("serial_number").value) || null,
        is_autograph: document.getElementById("is_autograph").checked ? 1 : 0,
        is_rookie: document.getElementById("is_rookie").checked ? 1 : 0,
        grade: getGradeValue(),
        purchase_price: parseFloat(document.getElementById("purchase_price").value) || null,
        purchase_date: document.getElementById("purchase_date").value || null,
        notes: document.getElementById("notes").value || null,
    }};

    try {{
        const res = await fetch(API + "/portfolio", {{
            method: "POST",
            headers: {{"Content-Type": "application/json", "Authorization": "Bearer " + token}},
            body: JSON.stringify({{action: "add_card", data: data}})
        }});
        const resp = await res.json();
        btn.disabled = false; btn.textContent = "Add Card";
        if (resp.error) showMsg("Error: " + resp.error, true);
        else {{
            showMsg("Card submitted! It will appear after the next pipeline run.", false);
            document.getElementById("player_name").value = "";
            document.getElementById("set_name").value = "";
            document.getElementById("card_number").value = "";
            document.getElementById("notes").value = "";
        }}
    }} catch (e) {{
        btn.disabled = false; btn.textContent = "Add Card";
        showMsg("Network error: " + e.message, true);
    }}
}}

async function deleteCard(cardId) {{
    if (!confirm("Delete this card from your portfolio?")) return;
    try {{
        const res = await fetch(API + "/portfolio", {{
            method: "POST",
            headers: {{"Content-Type": "application/json", "Authorization": "Bearer " + token}},
            body: JSON.stringify({{action: "delete_card", card_id: cardId}})
        }});
        const resp = await res.json();
        if (resp.error) alert("Error: " + resp.error);
        else loadPortfolio();
    }} catch (e) {{ alert("Network error: " + e.message); }}
}}

// Mark as Sold functionality
let soldCardId = null;

function openSoldModal(cardId, cardName) {{
    soldCardId = cardId;
    document.getElementById("soldCardName").textContent = cardName;
    document.getElementById("salePrice").value = "";
    document.getElementById("saleDate").value = new Date().toISOString().split("T")[0];
    document.getElementById("soldModal").classList.add("visible");
}}

function closeSoldModal() {{
    document.getElementById("soldModal").classList.remove("visible");
    soldCardId = null;
}}

async function submitSold() {{
    if (!soldCardId) return;

    const salePrice = parseFloat(document.getElementById("salePrice").value);
    const saleDate = document.getElementById("saleDate").value;

    if (!salePrice || salePrice <= 0) {{
        alert("Please enter a valid sale price");
        return;
    }}

    try {{
        const res = await fetch(API + "/portfolio", {{
            method: "POST",
            headers: {{"Content-Type": "application/json", "Authorization": "Bearer " + token}},
            body: JSON.stringify({{
                action: "mark_sold",
                card_id: soldCardId,
                sold_price: salePrice,
                sold_date: saleDate
            }})
        }});
        const resp = await res.json();
        if (resp.error) {{
            alert("Error: " + resp.error);
        }} else {{
            closeSoldModal();
            loadPortfolio();
        }}
    }} catch (e) {{
        alert("Network error: " + e.message);
    }}
}}

// Close modal when clicking outside
document.getElementById("soldModal").addEventListener("click", function(e) {{
    if (e.target === this) closeSoldModal();
}});

// Set default purchase date to today
document.getElementById("purchase_date").value = new Date().toISOString().split("T")[0];
</script>
</body>
</html>"""
    (output_dir / "portfolio.html").write_text(html)


def generate_admin_users_page(output_dir):
    """Generate the admin user management page."""
    admin_dir = output_dir / "admin"
    admin_dir.mkdir(parents=True, exist_ok=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>User Management — CollectorStream</title>
<style>{CSS}
.user-table td {{ vertical-align: middle; }}
.user-table select {{ background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary);
    padding: 6px 10px; border-radius: 4px; }}
.btn {{ display: inline-block; padding: 8px 16px; font-size: 14px; font-weight: bold; color: #000;
    background: var(--accent); border: none; border-radius: 6px; cursor: pointer; }}
.btn:hover {{ background: var(--accent-dark); }}
.btn-sm {{ padding: 4px 10px; font-size: 12px; background: var(--bg-secondary); color: var(--text-secondary);
    border: 1px solid var(--border); border-radius: 4px; cursor: pointer; }}
.btn-sm:hover {{ background: var(--bg-card); border-color: var(--accent); color: var(--accent); }}
.msg {{ padding: 10px 16px; border-radius: 6px; margin: 15px 0; font-size: 14px; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
.modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.8); align-items: center; justify-content: center; }}
.modal.visible {{ display: flex; }}
.modal-content {{ background: var(--bg-card); padding: 25px; border-radius: 10px; max-width: 400px; width: 90%; border: 1px solid var(--border); }}
.modal-content h3 {{ margin-bottom: 15px; color: var(--accent); }}
.modal-content input {{ width: 100%; padding: 10px; margin: 10px 0;
    background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; }}
.modal-buttons {{ display: flex; gap: 10px; margin-top: 15px; }}
</style>
</head>
<body>
<div class="container">
<div class="nav">
  <a href="/">Dashboard</a>
  <a href="/portfolio.html">Portfolio</a>
  <a href="/private/">Admin</a>
  <a href="/admin/users.html" class="active">Users</a>
  <a href="#" onclick="logout()">Logout</a>
</div>

<h1>User Management</h1>
<p class="subtitle">Manage registered users and their roles</p>

<div id="msg"></div>

<table class="user-table" id="usersTable">
  <tr><th>Email</th><th>Role</th><th>Registered</th><th>Actions</th></tr>
</table>

<div class="modal" id="passwordModal">
  <div class="modal-content">
    <h3>Reset Password</h3>
    <p id="modalEmail"></p>
    <input type="password" id="newPassword" placeholder="New password (8+ characters)">
    <div class="modal-buttons">
      <button class="btn" onclick="submitPassword()">Save</button>
      <button class="btn-sm" onclick="closeModal()">Cancel</button>
    </div>
  </div>
</div>

<script>
const API = "{API_BASE}";
const token = localStorage.getItem("token");
const role = localStorage.getItem("role");

// Auth guard - must be admin
if (!token || role !== "admin") {{
    location.href = "/login.html?redirect=/admin/users.html";
}}

function logout() {{ localStorage.clear(); location.href = "/login.html"; }}

function showMsg(text, isError) {{
    const el = document.getElementById("msg");
    el.className = "msg " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
    setTimeout(() => el.textContent = "", 5000);
}}

async function loadUsers() {{
    try {{
        const res = await fetch(API + "/auth/users", {{
            headers: {{"Authorization": "Bearer " + token}}
        }});
        if (res.status === 403) {{
            alert("Admin access required");
            location.href = "/portfolio.html";
            return;
        }}
        const data = await res.json();
        renderUsers(data.users || []);
    }} catch (e) {{
        showMsg("Error loading users: " + e.message, true);
    }}
}}

function renderUsers(users) {{
    const table = document.getElementById("usersTable");
    table.innerHTML = '<tr><th>Email</th><th>Role</th><th>Registered</th><th>Actions</th></tr>';
    users.forEach(u => {{
        const row = document.createElement("tr");
        row.innerHTML = '<td>' + u.email + '</td>' +
            '<td><select onchange="changeRole(\\'' + u.email + '\\', this.value)">' +
            '<option value="user"' + (u.role === "user" ? " selected" : "") + '>User</option>' +
            '<option value="admin"' + (u.role === "admin" ? " selected" : "") + '>Admin</option></select></td>' +
            '<td>' + (u.created_at ? new Date(u.created_at).toLocaleDateString() : "-") + '</td>' +
            '<td><button class="btn-sm" onclick="showPasswordModal(\\'' + u.email + '\\')">Reset Password</button></td>';
        table.appendChild(row);
    }});
}}

async function changeRole(email, newRole) {{
    try {{
        const res = await fetch(API + "/auth/users", {{
            method: "POST",
            headers: {{"Content-Type": "application/json", "Authorization": "Bearer " + token}},
            body: JSON.stringify({{email, role: newRole}})
        }});
        const data = await res.json();
        if (res.ok) showMsg("Role updated for " + email, false);
        else showMsg(data.error || "Update failed", true);
    }} catch (e) {{
        showMsg("Error: " + e.message, true);
    }}
}}

let targetEmail = "";
function showPasswordModal(email) {{
    targetEmail = email;
    document.getElementById("modalEmail").textContent = email;
    document.getElementById("newPassword").value = "";
    document.getElementById("passwordModal").classList.add("visible");
}}

function closeModal() {{
    document.getElementById("passwordModal").classList.remove("visible");
}}

async function submitPassword() {{
    const password = document.getElementById("newPassword").value;
    if (password.length < 8) {{ alert("Password must be 8+ characters"); return; }}
    try {{
        const res = await fetch(API + "/auth/users", {{
            method: "POST",
            headers: {{"Content-Type": "application/json", "Authorization": "Bearer " + token}},
            body: JSON.stringify({{email: targetEmail, password: password}})
        }});
        const data = await res.json();
        closeModal();
        if (res.ok) showMsg("Password reset for " + targetEmail, false);
        else showMsg(data.error || "Reset failed", true);
    }} catch (e) {{
        showMsg("Error: " + e.message, true);
    }}
}}

loadUsers();
</script>
</body>
</html>"""
    (admin_dir / "users.html").write_text(html)


def generate_portfolio_dashboard(output_dir):
    """Generate the portfolio management page with card entry form and table."""
    from db.models import get_portfolio_cards, get_all_player_names
    from analysis.portfolio_tracker import calculate_trends, get_portfolio_summary
    from analysis.fingerprint import card_description

    private_dir = output_dir / "private"
    private_dir.mkdir(parents=True, exist_ok=True)

    # Get data
    summary = get_portfolio_summary()
    player_names = get_all_player_names()
    player_names_js = str(player_names).replace("'", '"')

    # Build portfolio table rows
    cards_html = ""
    for c in summary.get("cards", []):
        desc = html_escape(c.get("description", ""))
        player = html_escape(c.get("player_name", ""))
        purchase = f"${c['purchase_price']:.2f}" if c.get("purchase_price") else "-"
        trends = c.get("trends", {})
        current = f"${trends['current_price']:.2f}" if trends.get("current_price") else "-"
        signal = trends.get("signal", "HOLD")
        reason = html_escape(trends.get("signal_reason", ""))
        momentum = trends.get("momentum", "")

        gl_html = "-"
        if trends.get("gain_loss") is not None:
            gl = trends["gain_loss"]
            gl_pct = trends.get("gain_loss_pct", 0)
            gl_cls = "rising" if gl >= 0 else "falling"
            gl_html = f'<span class="{gl_cls}">${gl:+.2f} ({gl_pct:+.1f}%)</span>'

        sig_cls = "badge-rising" if signal == "HOLD" else "badge-new" if signal == "SELL" else ""
        if signal == "SELL":
            sig_cls = "badge-sell"

        cards_html += f"""<tr>
  <td class="player-name">{player}</td>
  <td>{desc}</td>
  <td class="avg-rank">{purchase}</td>
  <td class="avg-rank">{current}</td>
  <td>{gl_html}</td>
  <td><span class="badge {sig_cls}" title="{reason}">{signal}</span></td>
  <td><button class="btn-sm btn-del" onclick="deleteCard({c['id']})">Delete</button></td>
</tr>\n"""

    total_invested = summary.get("total_invested", 0)
    total_current = summary.get("total_current", 0)
    gl_total = summary.get("unrealized_gain_loss", 0)
    gl_pct = summary.get("unrealized_pct", 0)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio — CollectorStream</title>
<style>{CSS}
.form-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
.form-group {{ display: flex; flex-direction: column; }}
.form-group label {{ font-size: 12px; color: var(--text-muted); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
.form-group input, .form-group select, .form-group textarea {{
    background: var(--bg-card); border: 1px solid var(--border); color: var(--text-primary);
    padding: 8px 12px; border-radius: 6px; font-size: 14px;
}}
.form-group input:focus, .form-group select:focus {{ border-color: var(--accent); outline: none; }}
.form-group.full {{ grid-column: 1 / -1; }}
.checkbox-group {{ display: flex; gap: 20px; align-items: center; grid-column: 1 / -1; padding: 8px 0; }}
.checkbox-group label {{ display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-secondary); cursor: pointer; }}
.checkbox-group input[type="checkbox"] {{ width: 16px; height: 16px; accent-color: var(--accent); }}
.numbered-fields {{ display: none; grid-template-columns: 1fr 1fr; gap: 12px; grid-column: 1 / -1; }}
.numbered-fields.visible {{ display: grid; }}
.radio-group {{ display: flex; gap: 20px; }}
.radio-group label {{ display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-secondary); cursor: pointer; }}
.radio-group input[type="radio"] {{ width: 16px; height: 16px; accent-color: var(--accent); }}
.graded-fields {{ display: none; grid-template-columns: 1fr 1fr; gap: 12px; grid-column: 1 / -1; }}
.graded-fields.visible {{ display: grid; }}
.graded-fields .checkbox-group {{ grid-column: 1 / -1; }}
.raw-fields {{ display: grid; grid-template-columns: 1fr; gap: 12px; grid-column: 1 / -1; }}
.raw-fields.hidden {{ display: none; }}
.btn {{ display: inline-block; padding: 12px 28px; font-size: 16px; font-weight: bold; color: #000; background: var(--accent); border: none; border-radius: 8px; cursor: pointer; }}
.btn:hover {{ background: var(--accent-dark); }}
.btn:disabled {{ background: var(--text-muted); cursor: not-allowed; }}
.btn-sm {{ padding: 4px 12px; font-size: 12px; background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid var(--border); border-radius: 4px; cursor: pointer; }}
.btn-sm:hover {{ background: var(--bg-card); border-color: var(--accent); color: var(--accent); }}
.btn-del {{ border-color: var(--danger); color: var(--danger); }}
.btn-del:hover {{ background: var(--danger); color: #fff; }}
.badge-sell {{ background: var(--danger); color: #fff; }}
.collapsible {{ cursor: pointer; user-select: none; }}
.collapsible::after {{ content: " +"; color: var(--accent); }}
.collapsible.open::after {{ content: " −"; }}
.form-container {{ display: none; margin-top: 15px; }}
.form-container.visible {{ display: block; }}
.msg {{ padding: 10px 16px; border-radius: 6px; margin: 10px 0; font-size: 14px; }}
.msg-success {{ background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); }}
.msg-error {{ background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }}
</style>
</head>
<body>
<div class="container">
<div class="nav">
  <a href="/">Dashboard</a>
  <a href="/card-values.html">Card Values</a>
  <a href="/watchlist.html">Watchlist</a>
  <a href="/private/">Admin</a>
  <a href="/private/portfolio.html" class="active">Portfolio</a>
</div>

<h1>Card Portfolio</h1>
<p class="subtitle">Track your personal card investments with buy/sell signals</p>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value">{summary.get('total_cards', 0)}</div>
    <div class="stat-label">Cards Owned</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">${total_invested:.2f}</div>
    <div class="stat-label">Total Invested</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">${total_current:.2f}</div>
    <div class="stat-label">Current Value</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" style="color:{'#00c853' if gl_total >= 0 else '#ff1744'}">${gl_total:+.2f}</div>
    <div class="stat-label">Unrealized ({gl_pct:+.1f}%)</div>
  </div>
</div>

<h2 class="collapsible" onclick="toggleForm()">Add Card</h2>
<div class="form-container" id="formContainer">
<div id="formMsg"></div>
<div class="form-grid">
  <div class="form-group">
    <label>Player Name *</label>
    <input type="text" id="player_name" list="playerList" placeholder="e.g. JuJu Watkins">
    <datalist id="playerList"></datalist>
  </div>
  <div class="form-group">
    <label>Card Year *</label>
    <input type="number" id="card_year" value="2024" min="1900" max="2100">
  </div>
  <div class="form-group">
    <label>Manufacturer *</label>
    <select id="manufacturer">
      <option value="">Select...</option>
      <option>Panini</option><option>Topps</option><option>Leaf</option>
      <option>Donruss</option><option>Bowman</option><option>Upper Deck</option>
      <option>Hoops</option><option>Fleer</option><option>Sage</option>
      <option>Press Pass</option><option>SP Authentic</option>
      <option>Immaculate</option><option>National Treasures</option>
      <option>Other</option>
    </select>
  </div>
  <div class="form-group">
    <label>Set Name *</label>
    <input type="text" id="set_name" placeholder="e.g. Prizm, Contenders">
  </div>
  <div class="form-group">
    <label>Card Number</label>
    <input type="text" id="card_number" placeholder="e.g. 125, RC-1">
  </div>
  <div class="form-group">
    <label>Parallel / Variant</label>
    <input type="text" id="parallel" placeholder="e.g. Silver, Pink Shimmer" value="Base">
  </div>
  <div class="checkbox-group">
    <label><input type="checkbox" id="is_numbered" onchange="toggleNumbered()"> Numbered Card</label>
    <label><input type="checkbox" id="is_autograph"> Autograph</label>
    <label><input type="checkbox" id="is_rookie"> Rookie Card</label>
  </div>
  <div class="numbered-fields" id="numberedFields">
    <div class="form-group">
      <label>Numbered To (e.g. 100 for /100)</label>
      <input type="number" id="numbered_to" placeholder="100">
    </div>
    <div class="form-group">
      <label>Serial Number (e.g. 3 for 3/100)</label>
      <input type="number" id="serial_number" placeholder="3">
    </div>
  </div>
  <div class="form-group">
    <label>Grade</label>
    <select id="grade">
      <option value="Raw">Raw (ungraded)</option>
      <option>PSA 10</option><option>PSA 9</option><option>PSA 8</option>
      <option>PSA 7</option><option>PSA 6</option>
      <option>BGS 10</option><option>BGS 9.5</option><option>BGS 9</option>
      <option>BGS 8.5</option><option>BGS 8</option>
      <option>SGC 10</option><option>SGC 9.5</option><option>SGC 9</option>
      <option>Other</option>
    </select>
  </div>
  <div class="form-group">
    <label>Purchase Price</label>
    <input type="number" id="purchase_price" step="0.01" placeholder="Leave blank for Card Ladder avg">
  </div>
  <div class="form-group">
    <label>Purchase Date</label>
    <input type="date" id="purchase_date">
  </div>
  <div class="form-group full">
    <label>Notes</label>
    <textarea id="notes" rows="2" placeholder="Optional notes"></textarea>
  </div>
</div>
<button class="btn" id="addBtn" onclick="addCard()">Add Card</button>
</div>

<h2>Holdings</h2>
{"<p class='empty-state'>No cards yet. Click 'Add Card' above to get started.</p>" if not cards_html else f'''<table>
<tr>
  <th>Player</th><th>Card</th><th>Purchased</th><th>Current</th>
  <th>Gain/Loss</th><th>Signal</th><th></th>
</tr>
{cards_html}</table>'''}

<script>
const API = "{PORTFOLIO_API}";
const API_KEY = "{PORTFOLIO_API_KEY}";
const PLAYERS = {player_names_js};

// Populate player autocomplete
const dl = document.getElementById("playerList");
PLAYERS.forEach(p => {{ const o = document.createElement("option"); o.value = p; dl.appendChild(o); }});

function toggleForm() {{
    const h = document.querySelector(".collapsible");
    const c = document.getElementById("formContainer");
    h.classList.toggle("open");
    c.classList.toggle("visible");
}}

function toggleNumbered() {{
    const nf = document.getElementById("numberedFields");
    nf.classList.toggle("visible", document.getElementById("is_numbered").checked);
}}

function showMsg(text, isError) {{
    const el = document.getElementById("formMsg");
    el.className = "msg " + (isError ? "msg-error" : "msg-success");
    el.textContent = text;
    setTimeout(() => el.textContent = "", 5000);
}}

function addCard() {{
    const btn = document.getElementById("addBtn");
    btn.disabled = true;
    btn.textContent = "Submitting...";

    const data = {{
        player_name: document.getElementById("player_name").value,
        card_year: parseInt(document.getElementById("card_year").value),
        manufacturer: document.getElementById("manufacturer").value,
        set_name: document.getElementById("set_name").value,
        card_number: document.getElementById("card_number").value,
        parallel: document.getElementById("parallel").value || "Base",
        is_numbered: document.getElementById("is_numbered").checked ? 1 : 0,
        numbered_to: parseInt(document.getElementById("numbered_to").value) || null,
        serial_number: parseInt(document.getElementById("serial_number").value) || null,
        is_autograph: document.getElementById("is_autograph").checked ? 1 : 0,
        is_rookie: document.getElementById("is_rookie").checked ? 1 : 0,
        grade: getGradeValue(),
        purchase_price: parseFloat(document.getElementById("purchase_price").value) || null,
        purchase_date: document.getElementById("purchase_date").value || null,
        notes: document.getElementById("notes").value || null,
    }};

    fetch(API, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json", "x-api-key": API_KEY }},
        body: JSON.stringify({{ action: "add_card", data: data }})
    }})
    .then(r => r.json())
    .then(resp => {{
        btn.disabled = false;
        btn.textContent = "Add Card";
        if (resp.error) {{
            showMsg("Error: " + resp.error, true);
        }} else {{
            showMsg("Card submitted! It will appear after the next pipeline run.", false);
            // Clear form
            document.getElementById("player_name").value = "";
            document.getElementById("set_name").value = "";
            document.getElementById("card_number").value = "";
            document.getElementById("notes").value = "";
        }}
    }})
    .catch(err => {{
        btn.disabled = false;
        btn.textContent = "Add Card";
        showMsg("Network error: " + err.message, true);
    }});
}}

function deleteCard(cardId) {{
    if (!confirm("Delete this card from your portfolio?")) return;
    fetch(API, {{
        method: "POST",
        headers: {{ "Content-Type": "application/json", "x-api-key": API_KEY }},
        body: JSON.stringify({{ action: "delete_card", card_id: cardId }})
    }})
    .then(r => r.json())
    .then(resp => {{
        if (resp.error) alert("Error: " + resp.error);
        else location.reload();
    }})
    .catch(err => alert("Network error: " + err.message));
}}

// Set default purchase date to today
document.getElementById("purchase_date").value = new Date().toISOString().split("T")[0];
</script>

<p class="timestamp">Report generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
</div>
</body>
</html>"""

    (private_dir / "portfolio.html").write_text(html)


def generate_all(output_dir=None, sports=None):
    """Generate all HTML reports.

    Args:
        output_dir: Directory to write files (default: ~/Desktop/WNBA-Scout)
        sports: List of sports to generate (default: ["wnba"]). Use ["wnba", "nba"] for multi-sport.
    """
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Default to WNBA only for backward compatibility
    if sports is None:
        sports = ["wnba"]

    print(f"Generating reports to {output_dir}/")

    # Generate new Lovable-style landing page
    generate_landing_page(output_dir)
    print("  index.html (landing page)")

    # Generate sport-specific pages
    for sport in sports:
        config = SPORTS_CONFIG.get(sport.lower())
        if not config:
            print(f"  [warning] Unknown sport: {sport}")
            continue

        sport_name = config["name"]
        prefix = config["prefix"]
        years = config["draft_years"]

        print(f"\n  --- {sport_name} ---")

        for year in years:
            if generate_board_page(year, output_dir, sport=sport):
                print(f"  {prefix}{year}-board.html")

        for year in years:
            if generate_player_dashboard(year, output_dir, sport=sport):
                print(f"  {prefix}players-{year}.html")

    # Legacy: also generate WNBA boards and dashboards if not in sports list
    # (This ensures backward compatibility)
    if "wnba" not in [s.lower() for s in sports]:
        for year in DRAFT_YEARS:
            if generate_board_page(year, output_dir):
                print(f"  {year}-board.html")

        for year in DRAFT_YEARS:
            if generate_player_dashboard(year, output_dir):
                print(f"  players-{year}.html")

    player_count = generate_all_player_pages(output_dir)
    print(f"  {player_count} player detail pages")

    generate_card_values_page(output_dir)
    print("  card-values.html")

    generate_watchlist_page(output_dir)
    print("  watchlist.html")

    generate_movers_page(output_dir)
    print("  movers.html")

    generate_signals_page(output_dir)
    print("  buy-signals.html")

    generate_private_dashboard(output_dir)
    print("  private/index.html")

    generate_login_page(output_dir)
    print("  login.html")

    generate_signup_page(output_dir)
    print("  signup.html")

    generate_profile_page(output_dir)
    print("  profile.html")

    generate_portfolio_page(output_dir)
    print("  portfolio.html")

    generate_admin_users_page(output_dir)
    print("  admin/users.html")

    print(f"\nDone! Open {output_dir / 'index.html'} in your browser.")
