"""Site-specific scraper implementations.

Organized by sport with sport-aware scraper classes.
"""

from scrapers.base import BaseScraper


# ============================================================================
# WNBA Scrapers
# ============================================================================

class BleacherReportWNBAScraper(BaseScraper):
    SOURCE_NAME = "Bleacher Report"
    SPORT = "WNBA"


class ESPNWNBAScraper(BaseScraper):
    SOURCE_NAME = "ESPN"
    SPORT = "WNBA"


class HoopsHQScraper(BaseScraper):
    SOURCE_NAME = "Hoops HQ"
    SPORT = "WNBA"


class SwishAppealScraper(BaseScraper):
    SOURCE_NAME = "Swish Appeal"
    SPORT = "WNBA"


class WBasketballBlogScraper(BaseScraper):
    SOURCE_NAME = "WBasketball Blog"
    SPORT = "WNBA"


class AcrossTheTimelineScraper(BaseScraper):
    SOURCE_NAME = "Across The Timeline"
    SPORT = "WNBA"


class TankathonWNBAScraper(BaseScraper):
    SOURCE_NAME = "Tankathon"
    SPORT = "WNBA"


class PASSportsScraper(BaseScraper):
    SOURCE_NAME = "PAS-Sports"
    SPORT = "WNBA"


class YahooSportsWNBAScraper(BaseScraper):
    SOURCE_NAME = "Yahoo Sports"
    SPORT = "WNBA"


# ============================================================================
# NBA Scrapers
# ============================================================================

class ESPNNBAScraper(BaseScraper):
    SOURCE_NAME = "ESPN"
    SPORT = "NBA"


class NBADraftNetScraper(BaseScraper):
    SOURCE_NAME = "NBADraft.net"
    SPORT = "NBA"


class TankathonNBAScraper(BaseScraper):
    SOURCE_NAME = "Tankathon"
    SPORT = "NBA"


class BleacherReportNBAScraper(BaseScraper):
    SOURCE_NAME = "Bleacher Report"
    SPORT = "NBA"


class TheRingerNBAScraper(BaseScraper):
    SOURCE_NAME = "The Ringer"
    SPORT = "NBA"


class YahooSportsNBAScraper(BaseScraper):
    SOURCE_NAME = "Yahoo Sports"
    SPORT = "NBA"


class NBCSportsNBAScraper(BaseScraper):
    SOURCE_NAME = "NBC Sports"
    SPORT = "NBA"


class SportingNewsNBAScraper(BaseScraper):
    SOURCE_NAME = "Sporting News"
    SPORT = "NBA"


# ============================================================================
# NFL Scrapers
# ============================================================================

class ESPNNFLScraper(BaseScraper):
    SOURCE_NAME = "ESPN"
    SPORT = "NFL"


class NFLDotComScraper(BaseScraper):
    SOURCE_NAME = "NFL.com"
    SPORT = "NFL"


class TankathonNFLScraper(BaseScraper):
    SOURCE_NAME = "Tankathon"
    SPORT = "NFL"


class CBSSportsNFLScraper(BaseScraper):
    SOURCE_NAME = "CBS Sports"
    SPORT = "NFL"


class NFLMockDBScraper(BaseScraper):
    SOURCE_NAME = "NFL Mock Draft Database"
    SPORT = "NFL"


class PFFNFLScraper(BaseScraper):
    SOURCE_NAME = "Pro Football Focus"
    SPORT = "NFL"


class SportingNewsNFLScraper(BaseScraper):
    SOURCE_NAME = "Sporting News"
    SPORT = "NFL"


# ============================================================================
# MLB Scrapers
# ============================================================================

class MLBPipelineScraper(BaseScraper):
    SOURCE_NAME = "MLB Pipeline"
    SPORT = "MLB"


class BaseballAmericaScraper(BaseScraper):
    SOURCE_NAME = "Baseball America"
    SPORT = "MLB"


class FangraphsScraper(BaseScraper):
    SOURCE_NAME = "Fangraphs"
    SPORT = "MLB"


class ESPNMLBScraper(BaseScraper):
    SOURCE_NAME = "ESPN"
    SPORT = "MLB"


class ProspectsLiveScraper(BaseScraper):
    SOURCE_NAME = "Prospects Live"
    SPORT = "MLB"


class MLBDotComScraper(BaseScraper):
    SOURCE_NAME = "MLB.com"
    SPORT = "MLB"


class BleacherNationMLBScraper(BaseScraper):
    SOURCE_NAME = "Bleacher Nation"
    SPORT = "MLB"


# ============================================================================
# NHL Scrapers
# ============================================================================

class TankathonNHLScraper(BaseScraper):
    SOURCE_NAME = "Tankathon"
    SPORT = "NHL"


class NHLDotComScraper(BaseScraper):
    SOURCE_NAME = "NHL.com"
    SPORT = "NHL"


class EliteProspectsNHLScraper(BaseScraper):
    SOURCE_NAME = "Elite Prospects"
    SPORT = "NHL"


class SmahtScoutingScraper(BaseScraper):
    SOURCE_NAME = "Smaht Scouting"
    SPORT = "NHL"


class TheAthleticNHLScraper(BaseScraper):
    SOURCE_NAME = "The Athletic"
    SPORT = "NHL"


# ============================================================================
# Sport-Organized Scraper Registry
# ============================================================================

# Map sport -> source_key -> scraper_class
SCRAPERS_BY_SPORT = {
    "wnba": {
        "bleacher_report": BleacherReportWNBAScraper,
        "espn": ESPNWNBAScraper,
        "hoops_hq": HoopsHQScraper,
        "swish_appeal": SwishAppealScraper,
        "wbasketball_blog": WBasketballBlogScraper,
        "across_the_timeline": AcrossTheTimelineScraper,
        "tankathon": TankathonWNBAScraper,
        "pas_sports": PASSportsScraper,
        "yahoo_sports": YahooSportsWNBAScraper,
    },
    "nba": {
        "espn": ESPNNBAScraper,
        "nbadraft_net": NBADraftNetScraper,
        "tankathon": TankathonNBAScraper,
        "bleacher_report": BleacherReportNBAScraper,
        "the_ringer": TheRingerNBAScraper,
        "yahoo_sports": YahooSportsNBAScraper,
        "nbc_sports": NBCSportsNBAScraper,
        "sporting_news": SportingNewsNBAScraper,
    },
    "nfl": {
        "espn": ESPNNFLScraper,
        "nfl_com": NFLDotComScraper,
        "tankathon": TankathonNFLScraper,
        "cbs_sports": CBSSportsNFLScraper,
        "nfl_mock_db": NFLMockDBScraper,
        "pff": PFFNFLScraper,
        "sporting_news": SportingNewsNFLScraper,
    },
    "mlb": {
        "mlb_pipeline": MLBPipelineScraper,
        "baseball_america": BaseballAmericaScraper,
        "prospects_live": ProspectsLiveScraper,
        "mlb_com": MLBDotComScraper,
        "bleacher_nation": BleacherNationMLBScraper,
    },
    "nhl": {
        "tankathon": TankathonNHLScraper,
        "nhl_com": NHLDotComScraper,
        "elite_prospects": EliteProspectsNHLScraper,
        "smaht_scouting": SmahtScoutingScraper,
        "the_athletic": TheAthleticNHLScraper,
    },
}


def get_scraper(sport: str, source_key: str):
    """Get a scraper class for a sport and source.

    Args:
        sport: Sport code (wnba, nba, nfl, etc.)
        source_key: Source key from config (e.g., 'espn', 'bleacher_report')

    Returns:
        Scraper class or None if not found
    """
    sport = sport.lower()
    sport_scrapers = SCRAPERS_BY_SPORT.get(sport, {})
    return sport_scrapers.get(source_key)


def get_scrapers_for_sport(sport: str):
    """Get all available scrapers for a sport.

    Args:
        sport: Sport code (wnba, nba, nfl, etc.)

    Returns:
        Dict mapping source_key to scraper class
    """
    return SCRAPERS_BY_SPORT.get(sport.lower(), {})


# Legacy compatibility - flat registry (deprecated, use SCRAPERS_BY_SPORT)
SCRAPERS = SCRAPERS_BY_SPORT.get("wnba", {})
