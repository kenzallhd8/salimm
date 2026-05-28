from thefuzz import fuzz
import datetime


def is_same_match(api_match, azuro_match, time_tolerance_hours=2, fuzz_threshold=80):
    """
    מקבלת שני מילונים של משחקים ממקורות שונים, ובודקת האם מדובר באותו משחק
    על בסיס זמן פתיחה והתאמת טקסט חכמה.
    """

    # 1. בדיקת זמנים (העוגן הקשיח)
    # מחשבים את ההפרש בשעות בין שני המשחקים
    time_diff = abs((api_match['start_time'] - azuro_match['start_time']).total_seconds())
    hours_diff = time_diff / 3600.0

    # אם ההפרש גדול מהסף שהגדרנו (למשל שעתיים) - זה בוודאות לא אותו משחק.
    # זה פותר את בעיית המשחקים בין אותן קבוצות בסיבובים שונים של העונה.
    if hours_diff > time_tolerance_hours:
        return False, 0

    # 2. התאמת שמות חכמה (Fuzzy Matching)
    # משתמשים ב-token_set_ratio כדי להתגבר על קיצורים כמו FC, Utd, Real וכו'
    home_score = fuzz.token_set_ratio(api_match['home_team'], azuro_match['home_team'])
    away_score = fuzz.token_set_ratio(api_match['away_team'], azuro_match['away_team'])

    # ממוצע ההתאמה של שתי הקבוצות
    avg_score = (home_score + away_score) / 2

    # 3. החלטה סופית
    if avg_score >= fuzz_threshold:
        return True, avg_score
    else:
        return False, avg_score


# ==========================================
# טסטים כדי לראות איך האלגוריתם חושב
# ==========================================
if __name__ == "__main__":
    # נתונים גולמיים ששאבנו מ-Pinnacle (Odds API)
    pinnacle_game = {
        'home_team': 'Manchester Utd',
        'away_team': 'Everton',
        'start_time': datetime.datetime(2026, 5, 10, 21, 0)
    }

    # תרחיש א': Azuro קוראים להם בשם המלא, עם FC, אבל באותו זמן
    azuro_game_correct = {
        'home_team': 'Manchester United',
        'away_team': 'Everton FC',
        'start_time': datetime.datetime(2026, 5, 10, 21, 0)
    }

    # תרחיש ב': מנצ'סטר סיטי משחקת באותה עיר ובאותה שעה בדיוק
    azuro_game_wrong = {
        'home_team': 'Manchester City',
        'away_team': 'Everton',
        'start_time': datetime.datetime(2026, 5, 10, 21, 0)
    }

    # תרחיש ג': מנצ'סטר יונייטד מול אברטון, אבל בגביע חודש לפני כן
    azuro_game_past = {
        'home_team': 'Manchester United',
        'away_team': 'Everton',
        'start_time': datetime.datetime(2026, 4, 10, 21, 0)
    }

    print("=== בדיקות מערכת: Smart Name Matching ===\n")

    res1, score1 = is_same_match(pinnacle_game, azuro_game_correct)
    print(f"תרחיש א' (שם מלא): {'✅ התאמה' if res1 else '❌ אין התאמה'} | ציון: {score1}%")

    res2, score2 = is_same_match(pinnacle_game, azuro_game_wrong)
    print(f"תרחיש ב' (הדרבי של סיטי): {'✅ התאמה' if res2 else '❌ אין התאמה'} | ציון: {score2}%")

    res3, score3 = is_same_match(pinnacle_game, azuro_game_past)
    print(f"תרחיש ג' (משחק מחודש שעבר): {'✅ התאמה' if res3 else '❌ אין התאמה'} | ציון: {score3}%")