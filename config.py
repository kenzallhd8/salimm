# config.py

# --- API Settings (Pinnacle Baseline ONLY) ---
ODDS_API_KEY = "15d66654a6a32a5fadbb09672c1d146f"

# --- Web3 Endpoints (The Aggregator Targets) ---
# --- Web3 Endpoints ---
SX_API_URL = "https://api.sx.bet/markets/active"
# הכנה לפרוטוקולים נוספים שנוסיף בהמשך:
OVERTIME_NETWORK_ID = 10 # Optimism
SX_BET_API_URL = "https://api.sx.bet/sports"

# --- Telegram Settings ---
TELEGRAM_TOKEN = "הטוקן_שלך"
TELEGRAM_CHAT_ID = "הצאט_איידי_שלך"

# --- Leagues to Scan (Massive Coverage) ---
SPORTS_TO_SCAN = [
    # המפעלים האירופיים
    "soccer_uefa_champs_league", "soccer_uefa_europa_league", "soccer_uefa_europa_conference_league",
    # הליגות הבכירות באירופה
    "soccer_epl", "soccer_germany_bundesliga", "soccer_italy_serie_a",
    "soccer_spain_la_liga", "soccer_france_ligue_one",
    # ליגות משנה
    "soccer_efl_champ", "soccer_germany_bundesliga2", "soccer_italy_serie_b",
    "soccer_spain_segunda_division", "soccer_france_ligue_two",
    # ליגות מסביב לעולם (עבור שעות שונות)
    "soccer_usa_mls", "soccer_brazil_campeonato", "soccer_mexico_ligamx",
    "soccer_argentina_primera_division", "soccer_japan_j_league",
    "soccer_australia_aleague",
    # צפון ומרכז אירופה
    "soccer_norway_eliteserien", "soccer_sweden_allsvenskan", "soccer_denmark_superliga",
    "soccer_netherlands_eredivisie", "soccer_portugal_primeira_liga",
    "soccer_turkey_super_league", "soccer_belgium_first_div"
]

REGIONS = "eu"
MARKETS = "h2h"

# --- Traditional Bookmakers (Kept strictly for baseline) ---
BOOKMAKER_URLS = {
    "pinnacle": "https://www.pinnacle.com/"
}
