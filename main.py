#!/usr/bin/env python3
"""Sports Card Scout — WNBA prospect tracker for card investors.

Usage:
    python main.py import                     Import spreadsheet data
    python main.py scrape [--source X] [--year Y]  Run scrapers
    python main.py board <year>               Show consensus big board
    python main.py movers [--year Y]          Show rising/falling players
    python main.py signals [--year Y]         Show card buy signals
    python main.py players [--year Y]         List all tracked players
    python main.py search <url>               Scrape a specific URL
"""

import os
import sys
import argparse
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

# Load .env file if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

from db.models import (
    init_db, get_players_by_draft_year, get_latest_rankings,
    get_all_players_with_rankings, upsert_player, add_ranking,
)
from analysis.movers import get_movers, get_consensus_board, card_buy_signals

console = Console()


def cmd_import(args):
    """Import players from the Excel spreadsheet."""
    from db.import_xlsx import import_spreadsheet
    init_db()
    xlsx_path = args.file or "/Users/toddwallace/Desktop/WNBA Prospects.xlsx"
    import_spreadsheet(xlsx_path)


def cmd_scrape(args):
    """Run scrapers against configured sources.

    Supports multi-sport scraping via --sport flag.
    Default is WNBA for backward compatibility.
    """
    from scrapers.sites import SCRAPERS_BY_SPORT, get_scraper

    init_db()
    config_path = Path(__file__).parent / "config" / "sources.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Get sport (default to wnba for backward compatibility)
    sport = (args.sport or "wnba").lower()
    sport_config = config.get(sport, {})

    if not sport_config:
        console.print(f"[red]No configuration found for sport: {sport}[/red]")
        console.print(f"Available sports: {', '.join(config.keys())}")
        return

    sources = sport_config.get("sources", {})
    if not sources:
        console.print(f"[yellow]No sources configured for {sport.upper()}[/yellow]")
        return

    if args.source:
        sources = {k: v for k, v in sources.items() if k == args.source}

    console.print(f"[bold]Scraping {sport.upper()} mock drafts...[/bold]")

    for source_key, source_config in sources.items():
        scraper_class = get_scraper(sport, source_key)
        if not scraper_class:
            console.print(f"[yellow]No scraper for {source_key} ({sport}), skipping[/yellow]")
            continue

        scraper = scraper_class()
        urls = source_config.get("urls", {})

        for year, url in urls.items():
            if url is None:
                continue  # URL not yet discovered
            year = int(year)
            if args.year and year != args.year:
                continue
            scraper.scrape(url, year)


def cmd_normalize(args):
    """Merge duplicate players with spelling variations."""
    from db.normalize import merge_duplicate_players
    init_db()
    merge_duplicate_players()


def cmd_cards(args):
    """Search eBay for autograph cards and track prices."""
    from analysis.card_prices import track_all_players, track_player_cards, get_best_buys
    from scrapers.ebay import EbayClient
    from db.models import get_latest_card_values

    init_db()

    if args.player:
        # Search specific player
        from db.models import get_connection
        conn = get_connection()
        row = conn.execute(
            "SELECT id, name, draft_year FROM players WHERE name LIKE ?",
            (f"%{args.player}%",),
        ).fetchone()
        conn.close()
        if not row:
            console.print(f"[red]Player '{args.player}' not found[/red]")
            return
        ebay = EbayClient()
        summary = track_player_cards(row["id"], row["name"], ebay)
        console.print(f"\n[bold]{row['name']}[/bold] ({row['draft_year']} Draft)")
        if summary["listing_count"] > 0:
            console.print(f"  Lowest BIN: [green]${summary['lowest_bin']:.2f}[/green]")
            console.print(f"  Average:    ${summary['avg_price']:.2f}")
            console.print(f"  Listings:   {summary['listing_count']}")
            console.print(f"  eBay: {summary['ebay_search_url']}")
            if summary.get("items"):
                console.print("\n  Cheapest listings:")
                for item in summary["items"][:5]:
                    console.print(f"    ${item['price']:.2f} — {item['title'][:70]}")
        else:
            console.print("  [yellow]No autograph cards found on eBay[/yellow]")
        return

    # Track all players
    track_all_players(draft_year=args.year)

    # Show best buys
    buys = get_best_buys(draft_year=args.year)
    if buys:
        table = Table(title="Best Buys — High Rank, Low Price")
        table.add_column("Player", style="cyan")
        table.add_column("Year", justify="right")
        table.add_column("Avg Rank", justify="right")
        table.add_column("Lowest Auto", justify="right", style="green")
        table.add_column("Listings", justify="right")
        for b in buys[:15]:
            rank = f"{b['avg_rank']:.0f}" if b["avg_rank"] else "?"
            table.add_row(
                b["name"], str(b["draft_year"]), rank,
                f"${b['lowest_bin']:.2f}",
                str(b["listing_count"]),
            )
        console.print(table)


def cmd_search(args):
    """Scrape a specific URL using LLM parsing."""
    from scrapers.base import BaseScraper

    init_db()

    class AdHocScraper(BaseScraper):
        SOURCE_NAME = args.source_name or "Manual"

    scraper = AdHocScraper()
    results = scraper.scrape(args.url, args.year or 2026)

    if results:
        table = Table(title=f"Players found at {args.url}")
        table.add_column("Rank", justify="right")
        table.add_column("Name")
        table.add_column("School")
        table.add_column("Position")
        for p in results:
            table.add_row(
                str(p.get("rank", "?")),
                p.get("name", ""),
                p.get("school", ""),
                p.get("position", ""),
            )
        console.print(table)


def cmd_fetch(args):
    """Fetch and save raw HTML from a URL for debugging."""
    from scrapers.base import BaseScraper

    class Fetcher(BaseScraper):
        SOURCE_NAME = "debug"
        RATE_LIMIT_SECONDS = 2

    fetcher = Fetcher()
    if args.js:
        html = fetcher.fetch_with_playwright(args.url)
    else:
        html = fetcher.fetch_html(args.url)

    out_dir = Path(__file__).parent / "data" / "raw_html"
    out_dir.mkdir(parents=True, exist_ok=True)
    from urllib.parse import urlparse
    filename = urlparse(args.url).netloc.replace(".", "_") + ".html"
    out_path = out_dir / filename
    out_path.write_text(html)
    console.print(f"Saved {len(html):,} chars to {out_path}")


def cmd_board(args):
    """Show consensus big board for a draft year."""
    init_db()
    sport = (args.sport or "wnba").upper()
    board = get_consensus_board(args.year, sport=sport)

    table = Table(title=f"Consensus Board — {args.year} {sport} Draft")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Player", style="cyan")
    table.add_column("School")
    table.add_column("Pos")
    table.add_column("Avg Rank", justify="right")
    table.add_column("Sources", justify="right")
    table.add_column("Source Rankings")

    for i, p in enumerate(board, 1):
        avg = f"{p['avg_rank']:.1f}" if p["avg_rank"] else "-"
        table.add_row(
            str(i),
            p["name"],
            p.get("school") or "",
            p.get("position") or "",
            avg,
            str(p["num_sources"]) if p["num_sources"] else "0",
            p.get("source_ranks") or "",
        )
    console.print(table)


def cmd_movers(args):
    """Show players rising or falling in rankings."""
    init_db()
    sport = getattr(args, 'sport', None)
    movers = get_movers(draft_year=args.year, days_back=args.days or 30, sport=sport)

    if not movers:
        console.print("[yellow]No ranking changes found. Run scrapers at least twice to track movement.[/yellow]")
        return

    table = Table(title="Rising & Falling Prospects")
    table.add_column("Player", style="cyan")
    table.add_column("Year", justify="right")
    table.add_column("Source")
    table.add_column("Was", justify="right")
    table.add_column("Now", justify="right")
    table.add_column("Change", justify="right")

    for m in movers:
        change = m["rank_change"]
        style = "green" if change > 0 else "red" if change < 0 else ""
        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
        table.add_row(
            m["name"],
            str(m["draft_year"]),
            m["source"],
            str(m.get("previous_rank", "?")),
            str(m.get("current_rank", "?")),
            f"{arrow} {abs(change)}",
            style=style,
        )
    console.print(table)


def cmd_signals(args):
    """Show card buy/sell signals."""
    init_db()
    signals = card_buy_signals(draft_year=args.year)

    if not signals:
        console.print("[yellow]No signals detected yet. Need more scrape data.[/yellow]")
        return

    table = Table(title="Card Buy Signals")
    table.add_column("Signal", style="bold")
    table.add_column("Player", style="cyan")
    table.add_column("Year", justify="right")
    table.add_column("Detail")

    for s in signals:
        style = "green" if s["signal"] == "RISING" else "blue"
        table.add_row(
            s["signal"],
            s["name"],
            str(s["draft_year"]),
            s["detail"],
            style=style,
        )
    console.print(table)


def cmd_players(args):
    """List all tracked players."""
    init_db()
    years = [args.year] if args.year else [2026, 2027, 2028, 2029, 2030]

    for year in years:
        players = get_players_by_draft_year(year)
        if not players:
            continue

        table = Table(title=f"Draft Class {year}")
        table.add_column("#", justify="right")
        table.add_column("Name", style="cyan")
        table.add_column("School")
        table.add_column("Position")

        for i, p in enumerate(players, 1):
            table.add_row(
                str(i),
                p["name"],
                p.get("school") or "",
                p.get("position") or "",
            )
        console.print(table)
        console.print()


def cmd_watchlist(args):
    """Manage and search cards for watched players."""
    from db.models import (
        add_watchlist_player, remove_watchlist_player, get_watchlist,
        get_watchlist_with_prices, add_watchlist_price,
    )
    from scrapers.ebay import EbayClient

    init_db()

    if args.add:
        for name in args.add:
            wid = add_watchlist_player(name, sport=args.sport)
            console.print(f"[green]Added {name} to watchlist[/green]")
        return

    if args.remove:
        for name in args.remove:
            if remove_watchlist_player(name):
                console.print(f"[yellow]Removed {name} from watchlist[/yellow]")
            else:
                console.print(f"[red]{name} not found on watchlist[/red]")
        return

    if args.search:
        # Search eBay for all watchlist players
        watchlist = get_watchlist()
        if not watchlist:
            console.print("[yellow]Watchlist is empty. Add players with --add[/yellow]")
            return

        ebay = EbayClient()
        import time
        for w in watchlist:
            print(f"  Searching: {w['name']}...", end=" ", flush=True)
            try:
                summary = ebay.get_player_card_summary(w["name"])
                add_watchlist_price(
                    w["id"],
                    lowest_bin=summary["lowest_bin"],
                    avg_price=summary["avg_price"],
                    listing_count=summary["listing_count"],
                    ebay_search_url=summary["ebay_search_url"],
                )
                if summary["listing_count"] > 0:
                    print(f"${summary['lowest_bin']:.2f} lowest "
                          f"(${summary['avg_price']:.2f} avg, "
                          f"{summary['listing_count']} listings)")
                else:
                    print("no listings")
            except Exception as e:
                print(f"ERROR: {e}")
            time.sleep(1)
        return

    # Default: show watchlist
    data = get_watchlist_with_prices()
    if not data:
        console.print("[yellow]Watchlist is empty. Add players with:[/yellow]")
        console.print("  python main.py watchlist --add \"Player Name\"")
        return

    table = Table(title="Watchlist")
    table.add_column("Player", style="cyan")
    table.add_column("Sport", style="dim")
    table.add_column("Lowest Auto", justify="right", style="green")
    table.add_column("Avg Price", justify="right")
    table.add_column("Listings", justify="right")
    table.add_column("Last Checked")
    for d in data:
        lowest = f"${d['lowest_bin']:.2f}" if d.get("lowest_bin") else "-"
        avg = f"${d['avg_price']:.2f}" if d.get("avg_price") else "-"
        listings = str(d.get("listing_count") or 0) if d.get("listing_count") else "-"
        checked = d.get("recorded_date") or "never"
        table.add_row(d["name"], d.get("sport") or "", lowest, avg, listings, checked)
    console.print(table)


def cmd_cardladder(args):
    """Look up card prices on Card Ladder."""
    from scrapers.cardladder import search_cardladder, search_cardladder_batch

    if args.player:
        result = search_cardladder(args.player)
        print(f"\n{result['player_name']} — Card Ladder Sales")
        if result["num_sales"] == 0:
            print("  No recent sales found")
            return

        print(f"  Sales found: {result['num_sales']}")
        print(f"  Lowest:  ${result['lowest_sale']:.2f}")
        print(f"  Highest: ${result['highest_sale']:.2f}")
        print(f"  Average: ${result['avg_sale']:.2f}")
        print()

        table = Table(title="Recent Sales")
        table.add_column("Date", style="dim")
        table.add_column("Type")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Card")
        for s in result["recent_sales"][:15]:
            table.add_row(
                s.get("date_sold", "?"),
                s.get("sale_type", "?"),
                f"${s.get('price', 0):.2f}",
                s.get("title", "")[:70],
            )
        console.print(table)
        return

    if args.batch:
        from db.models import get_watchlist
        init_db()
        watchlist = get_watchlist()
        names = [w["name"] for w in watchlist]
        if not names:
            print("Watchlist is empty. Add players with: python main.py watchlist --add \"Name\"")
            return
        print(f"Searching Card Ladder for {len(names)} watchlist players...")
        results = search_cardladder_batch(names)
        print(f"\nDone: {sum(1 for r in results.values() if r.get('num_sales', 0) > 0)}/{len(names)} players had sales")
        return

    print("Usage: python main.py cardladder --player \"JuJu Watkins\"")
    print("       python main.py cardladder --batch")


def cmd_portfolio(args):
    """Manage personal card portfolio."""
    from db.models import (
        init_db, add_portfolio_card, delete_portfolio_card,
        get_portfolio_cards, get_portfolio_card,
    )
    from analysis.portfolio_tracker import (
        price_check_all, calculate_trends, get_portfolio_summary,
        export_portfolio_json,
    )
    from analysis.fingerprint import card_description

    init_db()

    if args.import_submissions:
        # Import pending submissions from S3
        import json
        import subprocess
        bucket = "collectorstream-site"
        prefix = "private/portfolio-submissions/"
        result = subprocess.run(
            ["aws", "s3", "ls", f"s3://{bucket}/{prefix}", "--profile", "fluxzi"],
            capture_output=True, text=True,
        )
        files = []
        for line in result.stdout.strip().splitlines():
            parts = line.strip().split()
            if parts:
                files.append(parts[-1])

        if not files:
            print("No pending submissions.")
            return

        print(f"Processing {len(files)} submission(s)...")
        for fname in files:
            key = f"{prefix}{fname}"
            dl = subprocess.run(
                ["aws", "s3", "cp", f"s3://{bucket}/{key}", "-", "--profile", "fluxzi"],
                capture_output=True, text=True,
            )
            try:
                submission = json.loads(dl.stdout)
                if submission.get("type") == "add_card":
                    data = submission["data"]
                    # user_email is included in data from Lambda
                    user_email = data.get("user_email", "todd@fluxzi.com")
                    card_id = add_portfolio_card(**data)
                    print(f"  Added: {data['player_name']} — {data.get('set_name', '')} (id={card_id}, user={user_email})")
                elif submission.get("type") == "delete_card":
                    card_id = submission["card_id"]
                    user_email = submission.get("user_email")
                    if delete_portfolio_card(card_id, user_email=user_email):
                        print(f"  Deleted card id={card_id}")
                    else:
                        print(f"  Skipped delete: card {card_id} not owned by {user_email}")
                # Remove processed file
                subprocess.run(
                    ["aws", "s3", "rm", f"s3://{bucket}/{key}", "--profile", "fluxzi"],
                    capture_output=True,
                )
            except Exception as e:
                print(f"  Error processing {fname}: {e}")
        return

    if args.price_check:
        price_check_all(use_cardladder=args.cardladder, delay=1.0)
        return

    if args.signals:
        cards = get_portfolio_cards(status="active")
        if not cards:
            console.print("[yellow]No active portfolio cards.[/yellow]")
            return
        table = Table(title="Portfolio Signals")
        table.add_column("Player", style="cyan")
        table.add_column("Card")
        table.add_column("Purchased", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("Gain/Loss", justify="right")
        table.add_column("Signal", style="bold")
        table.add_column("Reason")
        for card in cards:
            trends = calculate_trends(card["id"])
            desc = card_description(card)
            purchase = f"${card['purchase_price']:.2f}" if card.get("purchase_price") else "-"
            current = f"${trends['current_price']:.2f}" if trends.get("current_price") else "-"
            gl = ""
            if trends.get("gain_loss") is not None:
                gl_val = trends["gain_loss"]
                gl_pct = trends.get("gain_loss_pct", 0)
                gl = f"${gl_val:+.2f} ({gl_pct:+.1f}%)"
            sig = trends.get("signal", "HOLD")
            style = "green" if sig == "HOLD" else "red"
            table.add_row(
                card["player_name"], desc, purchase, current, gl,
                sig, trends.get("signal_reason", ""), style=style,
            )
        console.print(table)
        return

    if args.export:
        data = export_portfolio_json()
        import subprocess
        subprocess.run(
            ["aws", "s3", "cp", "-", "s3://collectorstream-site/private/portfolio-data.json",
             "--content-type", "application/json", "--profile", "fluxzi"],
            input=data, text=True, capture_output=True,
        )
        print("Portfolio data exported to S3.")
        return

    # Default: show summary
    summary = get_portfolio_summary()
    if summary["total_cards"] == 0:
        console.print("[yellow]No cards in portfolio. Add via web form or --import.[/yellow]")
        return

    console.print(f"\n[bold]Portfolio Summary[/bold]")
    console.print(f"  Cards: {summary['total_cards']}")
    console.print(f"  Invested: ${summary['total_invested']:.2f}")
    console.print(f"  Current:  ${summary['total_current']:.2f}")
    gl = summary['unrealized_gain_loss']
    color = "green" if gl >= 0 else "red"
    console.print(f"  Gain/Loss: [{color}]${gl:+.2f} ({summary['unrealized_pct']:+.1f}%)[/{color}]")

    table = Table(title="Active Cards")
    table.add_column("ID", justify="right", style="dim")
    table.add_column("Player", style="cyan")
    table.add_column("Card")
    table.add_column("Purchased", justify="right")
    table.add_column("Current", justify="right")
    table.add_column("Signal", style="bold")
    for c in summary["cards"]:
        purchase = f"${c['purchase_price']:.2f}" if c.get("purchase_price") else "-"
        trends = c.get("trends", {})
        current = f"${trends['current_price']:.2f}" if trends.get("current_price") else "-"
        sig = trends.get("signal", "HOLD")
        table.add_row(
            str(c["id"]), c["player_name"], c["description"],
            purchase, current, sig,
        )
    console.print(table)


def cmd_stats(args):
    """Scrape university stats for tracked players."""
    init_db()

    if args.detect:
        from scrapers.ncaa_stats import detect_hot_cold
        detect_hot_cold()
        return

    from scrapers.ncaa_stats import scrape_all_stats, scrape_player_stats
    if args.player:
        scrape_player_stats(args.player)
    else:
        scrape_all_stats()


def cmd_report(args):
    """Generate HTML reports to desktop folder."""
    from reports.generate import generate_all
    init_db()
    output = args.output or str(Path.home() / "Desktop" / "WNBA-Scout")

    # Determine which sports to generate
    if args.sport:
        if args.sport.lower() == "all":
            sports = ["wnba", "nba", "nfl", "mlb", "nhl"]
        else:
            sports = [args.sport.lower()]
    else:
        sports = ["wnba"]  # Default for backward compatibility

    generate_all(output, sports=sports)


def cmd_tiers(args):
    """Recalculate player tier ratings based on consensus rankings."""
    from analysis.tiers import recalculate_all_tiers
    init_db()

    year = args.year
    print(f"Recalculating tiers{' for ' + str(year) if year else ' for all years'}...")

    tier_counts, updated = recalculate_all_tiers(draft_year=year)

    print(f"\nTier Summary:")
    for tier in ['A', 'B', 'C', 'D']:
        print(f"  Tier {tier}: {tier_counts[tier]} players")
    print(f"  Unranked: {tier_counts['unranked']} players")

    if args.verbose and updated:
        print(f"\nTop players by tier:")
        for tier in ['A', 'B', 'C', 'D']:
            tier_players = [p for p in updated if p['tier'] == tier][:5]
            if tier_players:
                print(f"\n  Tier {tier}:")
                for p in tier_players:
                    print(f"    {p['name']} ({p['draft_year']}) - avg rank {p['avg_rank']}")


def cmd_photos(args):
    """Scrape player photos from university roster pages."""
    from scrapers.photos import scrape_all_photos, scrape_player_photo_by_name
    init_db()

    if args.player:
        scrape_player_photo_by_name(args.player)
    else:
        sport = getattr(args, 'sport', None)
        scrape_all_photos(draft_year=args.year, sport=sport)


def cmd_pop(args):
    """Look up PSA/BGS population data for graded cards."""
    from scrapers.psa_pop import lookup_player_pop, lookup_all_watchlist, get_pop_buy_signals, get_player_population
    init_db()

    if args.signals:
        # Show buy signals based on low pop + rising players
        signals = get_pop_buy_signals()
        if not signals:
            print("No buy signals found. Try running 'pop --watchlist' first to gather population data.")
            return

        table = Table(title="Population-Based Buy Signals")
        table.add_column("Player", style="cyan")
        table.add_column("Card", style="white")
        table.add_column("PSA 10", justify="right", style="green")
        table.add_column("Total", justify="right")
        table.add_column("Gem %", justify="right")
        table.add_column("Rank Δ", justify="right", style="yellow")
        table.add_column("Signal", style="bold")

        for s in signals[:20]:
            table.add_row(
                s["player_name"],
                (s.get("card_name") or "")[:40],
                str(s["psa_10_pop"]),
                str(s["total_graded"]),
                f"{s['gem_rate']}%",
                f"+{abs(s.get('rank_change', 0))}",
                s["signal_strength"],
            )
        console.print(table)

    elif args.watchlist:
        # Look up all watchlist players
        lookup_all_watchlist()

    elif args.player:
        # Look up specific player
        results = lookup_player_pop(args.player)
        if results:
            table = Table(title=f"Population Data: {args.player}")
            table.add_column("Card", style="white")
            table.add_column("Grader", style="cyan")
            table.add_column("PSA 10", justify="right", style="green")
            table.add_column("PSA 9", justify="right")
            table.add_column("Total", justify="right")
            table.add_column("Gem %", justify="right")

            for r in results:
                gem_rate = r.get("gem_rate") or 0
                table.add_row(
                    (r.get("card_name") or "")[:50],
                    r.get("grader", "PSA"),
                    str(r.get("grade_10", 0)),
                    str(r.get("grade_9", 0)),
                    str(r.get("total_graded", 0)),
                    f"{gem_rate:.1f}%",
                )
            console.print(table)
        else:
            # Check if we have cached data
            cached = get_player_population(args.player)
            if cached:
                print(f"Using cached data for {args.player}:")
                for c in cached:
                    print(f"  {c['card_name']}: PSA 10={c['grade_10']}, Total={c['total_graded']}")
            else:
                print(f"No population data found for {args.player}")
    else:
        print("Usage: pop --player 'Lauren Betts' or pop --watchlist or pop --signals")


def main():
    parser = argparse.ArgumentParser(description="Sports Card Scout — WNBA Prospect Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # import
    p_import = subparsers.add_parser("import", help="Import spreadsheet data")
    p_import.add_argument("--file", "-f", help="Path to XLSX file")

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Run scrapers")
    p_scrape.add_argument("--sport", help="Sport to scrape (wnba, nba, nfl, etc.). Default: wnba")
    p_scrape.add_argument("--source", "-s", help="Only scrape this source")
    p_scrape.add_argument("--year", "-y", type=int, help="Only scrape this draft year")

    # search (ad-hoc URL)
    p_search = subparsers.add_parser("search", help="Scrape a specific URL")
    p_search.add_argument("url", help="URL to scrape")
    p_search.add_argument("--year", "-y", type=int, default=2026)
    p_search.add_argument("--source-name", "-n", default="Manual")

    # board
    p_board = subparsers.add_parser("board", help="Show consensus big board")
    p_board.add_argument("year", type=int, help="Draft year")
    p_board.add_argument("--sport", help="Sport (wnba, nba, nfl, etc.). Default: wnba")

    # movers
    p_movers = subparsers.add_parser("movers", help="Show rising/falling players")
    p_movers.add_argument("--year", "-y", type=int)
    p_movers.add_argument("--days", "-d", type=int, default=30)
    p_movers.add_argument("--sport", help="Sport (wnba, nba, nfl, etc.)")

    # signals
    p_signals = subparsers.add_parser("signals", help="Show card buy signals")
    p_signals.add_argument("--year", "-y", type=int)

    # players
    p_players = subparsers.add_parser("players", help="List tracked players")
    p_players.add_argument("--year", "-y", type=int)

    # fetch (debug)
    p_fetch = subparsers.add_parser("fetch", help="Fetch and save raw HTML for debugging")
    p_fetch.add_argument("url", help="URL to fetch")
    p_fetch.add_argument("--js", action="store_true", help="Use Playwright for JS rendering")

    # normalize
    subparsers.add_parser("normalize", help="Merge duplicate players with spelling variations")

    # report
    p_report = subparsers.add_parser("report", help="Generate HTML reports to desktop")
    p_report.add_argument("--output", "-o", help="Output directory (default: ~/Desktop/WNBA-Scout)")
    p_report.add_argument("--sport", "-s", help="Sport to generate (wnba, nba, nfl) or 'all' for multi-sport")

    # watchlist
    p_watch = subparsers.add_parser("watchlist", help="Manage watched players")
    p_watch.add_argument("--add", "-a", nargs="+", help="Add player(s) to watchlist")
    p_watch.add_argument("--remove", "-r", nargs="+", help="Remove player(s) from watchlist")
    p_watch.add_argument("--search", action="store_true", help="Search eBay for all watchlist players")
    p_watch.add_argument("--sport", default=None, help="Sport tag (e.g. WNBA, MLB, NBA)")

    # cards
    p_cards = subparsers.add_parser("cards", help="Search eBay for autograph cards and track prices")
    p_cards.add_argument("--year", "-y", type=int, help="Only search this draft year")
    p_cards.add_argument("--player", "-p", help="Search specific player name")

    # cardladder
    p_cl = subparsers.add_parser("cardladder", help="Look up card prices on Card Ladder")
    p_cl.add_argument("--player", "-p", help="Search specific player name")
    p_cl.add_argument("--batch", action="store_true", help="Search all watchlist players")

    # portfolio
    p_port = subparsers.add_parser("portfolio", help="Manage personal card portfolio")
    p_port.add_argument("--import-submissions", action="store_true", help="Import pending submissions from S3")
    p_port.add_argument("--price-check", action="store_true", help="Run price lookup for all cards")
    p_port.add_argument("--cardladder", action="store_true", help="Also check Card Ladder (with --price-check)")
    p_port.add_argument("--signals", action="store_true", help="Show buy/sell signals")
    p_port.add_argument("--export", action="store_true", help="Export portfolio data to S3")

    # stats
    p_stats = subparsers.add_parser("stats", help="Scrape university stats for tracked players")
    p_stats.add_argument("--player", "-p", help="Scrape specific player name")
    p_stats.add_argument("--detect", action="store_true", help="Run hot/cold detection")

    # tiers
    p_tiers = subparsers.add_parser("tiers", help="Recalculate player tier ratings (A/B/C/D)")
    p_tiers.add_argument("--year", "-y", type=int, help="Only update this draft year")
    p_tiers.add_argument("--verbose", "-v", action="store_true", help="Show player details")

    # photos
    p_photos = subparsers.add_parser("photos", help="Scrape player photos from university rosters")
    p_photos.add_argument("--year", "-y", type=int, help="Only scrape this draft year")
    p_photos.add_argument("--player", "-p", help="Scrape specific player by name")
    p_photos.add_argument("--sport", "-s", help="Only scrape this sport (wnba, nba, nfl, mlb, nhl)")

    # pop (PSA population)
    p_pop = subparsers.add_parser("pop", help="Look up PSA/BGS population data for graded cards")
    p_pop.add_argument("--player", "-p", help="Look up specific player by name")
    p_pop.add_argument("--watchlist", "-w", action="store_true", help="Look up all watchlist players")
    p_pop.add_argument("--signals", action="store_true", help="Show buy signals based on low pop + rising players")
    p_pop.add_argument("--low-pop", type=int, default=50, help="Max PSA 10 pop for signals (default: 50)")

    args = parser.parse_args()

    commands = {
        "import": cmd_import,
        "scrape": cmd_scrape,
        "search": cmd_search,
        "board": cmd_board,
        "movers": cmd_movers,
        "signals": cmd_signals,
        "players": cmd_players,
        "fetch": cmd_fetch,
        "normalize": cmd_normalize,
        "report": cmd_report,
        "cards": cmd_cards,
        "watchlist": cmd_watchlist,
        "cardladder": cmd_cardladder,
        "portfolio": cmd_portfolio,
        "stats": cmd_stats,
        "tiers": cmd_tiers,
        "photos": cmd_photos,
        "pop": cmd_pop,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
