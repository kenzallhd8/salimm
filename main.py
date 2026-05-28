import requests
import time
import csv
import os
from datetime import datetime

API_KEY = "39c88a98feed9dca7110b254a1e39ea5"

SPORTS_TO_SCAN = [
    "soccer_brazil_campeonato", "soccer_argentina_primera_div", "soccer_mexico_ligamx",
    "soccer_japan_j_league", "soccer_usa_mls", "soccer_england_efl_champ",
    "soccer_netherlands_eredivisie", "soccer_belgium_first_div",
    "soccer_portugal_primeira_liga", "soccer_turkey_super_league", "soccer_sweden_allsvenskan"
]

BOOKMAKERS = "pinnacle,stake,betonlineag,bovada,mybookieag,betus,bet365,draftkings,fanduel,williamhill,unibet"
LOG_FILE = "backtest_log.csv"

SYSTEM_HEADERS = ["Log Time", "Match", "Match Time", "Market", "Bet", "Bookie", "Fair", "Offered", "EV %",
                  "Kelly Rec (ILS)", "Status"]


def init_system_files():
    should_recreate = True
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as f:
                first_line = f.readline()
                if "Match Time" in first_line:
                    should_recreate = False
        except:
            pass

    if should_recreate:
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(SYSTEM_HEADERS)


def devig_3way(odds_dict):
    try:
        imp_h, imp_a, imp_d = 1 / odds_dict['Home'], 1 / odds_dict['Away'], 1 / odds_dict['Draw']
        margin = imp_h + imp_a + imp_d
        return {
            'Home': 1 / (imp_h / margin), 'Away': 1 / (imp_a / margin), 'Draw': 1 / (imp_d / margin),
            'Probs': {'Home': imp_h / margin, 'Away': imp_a / margin, 'Draw': imp_d / margin}
        }
    except:
        return None


def devig_2way(odds_dict):
    try:
        imp_o, imp_u = 1 / odds_dict['Over'], 1 / odds_dict['Under']
        margin = imp_o + imp_u
        return {
            'Over': 1 / (imp_o / margin), 'Under': 1 / (imp_u / margin),
            'Probs': {'Over': imp_o / margin, 'Under': imp_u / margin}
        }
    except:
        return None


def calculate_kelly(true_prob, offered_odds):
    b = offered_odds - 1
    return max(0, (((true_prob * b) - (1 - true_prob)) / b) / 4)


def log_bet(data):
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data['match'], data.get('match_time', 'N/A'), data.get('market', 'H2H'), data['bet'], data['bookie'],
            data['fair'], data['offered'], data['ev'], data['amount'],
            data.get('status', 'בהמתנה')
        ])


def scan_markets(budget=1000.0):
    init_system_files()

    # 1. טעינת כל ההימורים שכבר קיימים ביומן כדי למנוע כפילויות בלייב
    placed_keys = set()
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # דילוג על כותרות
                for row in reader:
                    if len(row) >= 5:
                        # מפתח ייחודי המורכב משם המשחק + סוג ההימור (למשל: Flamengo v Coritiba_Away)
                        placed_keys.add(f"{row[1].strip()}_{row[4].strip()}")
        except Exception as e:
            print(f"[X] שגיאה בקריאת משחקים קיימים מהיומן: {e}")

    print("[*] סורק ליגות ברקע...")
    best_bets = {}

    for sport in SPORTS_TO_SCAN:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {"apiKey": API_KEY, "regions": "eu,us,uk", "markets": "h2h,totals", "bookmakers": BOOKMAKERS}

        try:
            res = requests.get(url, params=params, timeout=12)
            if res.status_code != 200: continue
            matches = res.json()
            if not matches or isinstance(matches, dict): continue

            for match in matches:
                home, away = match['home_team'], match['away_team']
                short_match = f"{home[:12]} v {away[:12]}"
                bookies_h2h, bookies_totals = {}, {}

                commence_time_raw = match.get('commence_time', '')
                try:
                    dt = datetime.strptime(commence_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    match_time = dt.strftime("%d/%m %H:%M")
                except:
                    match_time = commence_time_raw

                for b in match.get('bookmakers', []):
                    name = b['key']
                    for m in b['markets']:
                        if m['key'] == 'h2h':
                            odds = {}
                            for o in m['outcomes']:
                                if o['name'] == home:
                                    odds['Home'] = o['price']
                                elif o['name'] == away:
                                    odds['Away'] = o['price']
                                elif o['name'] == 'Draw':
                                    odds['Draw'] = o['price']
                            if len(odds) == 3: bookies_h2h[name] = odds

                        elif m['key'] == 'totals':
                            odds = {'point': m['outcomes'][0].get('point')}
                            for o in m['outcomes']:
                                if o['name'] == 'Over':
                                    odds['Over'] = o['price']
                                elif o['name'] == 'Under':
                                    odds['Under'] = o['price']
                            if 'Over' in odds and 'Under' in odds and odds['point']:
                                bookies_totals[name] = odds

                # --- בדיקת שווקי H2H ---
                if 'pinnacle' in bookies_h2h:
                    fair_pin = devig_3way(bookies_h2h['pinnacle'])
                    if fair_pin:
                        for target, target_odds in bookies_h2h.items():
                            if target == 'pinnacle': continue
                            for side in ['Home', 'Draw', 'Away']:

                                # בדיקה: אם ההימור הזה כבר נמצא ביומן - דלג עליו מיד ולא תראה אותו שוב
                                if f"{short_match}_{side}" in placed_keys:
                                    continue

                                fair, offered = fair_pin[side], target_odds.get(side, 0)
                                if fair > 1 and offered > 1:
                                    edge = (offered / fair) - 1
                                    if 0.01 <= edge <= 0.08:
                                        kelly = calculate_kelly(fair_pin['Probs'][side], offered)
                                        ev_percent = round(edge * 100, 2)
                                        unique_key = f"{short_match}_{side}"

                                        if unique_key not in best_bets or best_bets[unique_key]['ev'] < ev_percent:
                                            best_bets[unique_key] = {
                                                "match": short_match, "match_time": match_time, "market": "H2H",
                                                "bet": side,
                                                "bookie": target[:8].upper(), "fair": round(fair, 2),
                                                "offered": offered, "ev": ev_percent,
                                                "amount": round(budget * kelly, 1)
                                            }

                # --- בדיקת שווקי Totals ---
                if 'pinnacle' in bookies_totals:
                    pin_totals = bookies_totals['pinnacle']
                    fair_pin = devig_2way(pin_totals)
                    if fair_pin:
                        for target, target_odds in bookies_totals.items():
                            if target == 'pinnacle': continue
                            if target_odds['point'] == pin_totals['point']:
                                for side in ['Over', 'Under']:
                                    bet_name = f"{side} {pin_totals['point']}"

                                    # בדיקה: אם הימור הטוטאל הזה כבר נמצא ביומן - דלג
                                    if f"{short_match}_{bet_name}" in placed_keys:
                                        continue

                                    fair, offered = fair_pin[side], target_odds.get(side, 0)
                                    if fair > 1 and offered > 1:
                                        edge = (offered / fair) - 1
                                        if 0.01 <= edge <= 0.08:
                                            kelly = calculate_kelly(fair_pin['Probs'][side], offered)
                                            ev_percent = round(edge * 100, 2)
                                            unique_key = f"{short_match}_{bet_name}"

                                            if unique_key not in best_bets or best_bets[unique_key]['ev'] < ev_percent:
                                                best_bets[unique_key] = {
                                                    "match": short_match, "match_time": match_time, "market": "Total",
                                                    "bet": bet_name,
                                                    "bookie": target[:8].upper(), "fair": round(fair, 2),
                                                    "offered": offered, "ev": ev_percent,
                                                    "amount": round(budget * kelly, 1)
                                                }

        except Exception:
            pass
        time.sleep(0.1)

    all_results = list(best_bets.values())
    all_results.sort(key=lambda x: x['ev'], reverse=True)
    return all_results