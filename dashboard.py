import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import csv
import webbrowser
from main import scan_markets, log_bet

BANKROLL_FILE = "bankroll.json"
LOG_FILE = "backtest_log.csv"

# הוספתי את כל הסוכנויות כדי שהלחיצה תשלח אותך ישירות לאתר
URL_MAP = {
    "FANDUEL": "https://sportsbook.fanduel.com/",
    "UNIBET": "https://www.unibet.com/",
    "BETONLIN": "https://www.betonline.ag/",
    "BOVADA": "https://www.bovada.lv/",
    "STAKE": "https://stake.com/sports",
    "BET365": "https://www.bet365.com/",
    "PINNACLE": "https://www.pinnacle.com/",
    "DRAFTKIN": "https://sportsbook.draftkings.com/",
    "WILLIAMH": "https://sports.williamhill.com/",
    "MYBOOKIE": "https://mybookie.ag/",
    "BETUS": "https://www.betus.com.pa/"
}


def load_bankroll_data():
    default_data = {
        "balance": 1000.0,
        "wins": 1,
        "losses": 4,
        "total_profit": 0.0,
        "total_loss": 0.0
    }
    if os.path.exists(BANKROLL_FILE):
        try:
            with open(BANKROLL_FILE, "r") as f:
                data = json.load(f)
                return {
                    "balance": data.get("balance", 1000.0),
                    "wins": data.get("wins", 1),
                    "losses": data.get("losses", 4),
                    "total_profit": data.get("total_profit", 0.0),
                    "total_loss": data.get("total_loss", 0.0)
                }
        except:
            pass
    return default_data


def save_bankroll_data(balance, wins, losses, total_profit, total_loss):
    data = {
        "balance": balance,
        "wins": wins,
        "losses": losses,
        "total_profit": total_profit,
        "total_loss": total_loss
    }
    with open(BANKROLL_FILE, "w") as f:
        json.dump(data, f)


def update_csv_status(match_name, new_status):
    if not os.path.exists(LOG_FILE): return

    updated_rows = []
    try:
        with open(LOG_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            updated_rows.append(headers)

            for row in reader:
                if len(row) > 10:
                    current_display_name = f"{row[1]} ({row[4]})"
                    if current_display_name == match_name and row[10].strip() == "בהמתנה":
                        row[10] = new_status
                updated_rows.append(row)

        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
    except Exception as e:
        print(f"[X] שגיאה בעדכון קובץ היומן: {e}")


class StrikerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Striker - Tactical UI V7")
        self.root.geometry("1150x650")
        self.root.configure(bg="#1a1b26")

        bankroll_data = load_bankroll_data()
        self.budget = bankroll_data["balance"]
        self.wins = bankroll_data["wins"]
        self.losses = bankroll_data["losses"]
        self.total_profit = bankroll_data["total_profit"]
        self.total_loss = bankroll_data["total_loss"]

        self.current_results = []
        # הזיכרון החכם החדש שימנע את הקריסות ביומן
        self.journal_map = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#24283b", foreground="#a9b1d6", fieldbackground="#24283b", rowheight=38,
                        borderwidth=0, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#16161e", foreground="#7aa2f7", font=("Arial", 11, "bold"),
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#3d59a1')])

        self.home_frame = tk.Frame(self.root, bg="#1a1b26")
        self.results_frame = tk.Frame(self.root, bg="#1a1b26")
        self.journal_frame = tk.Frame(self.root, bg="#1a1b26")

        self.build_home_screen()
        self.build_results_screen()
        self.build_journal_screen()

        self.show_home()

    def show_home(self):
        self.results_frame.pack_forget()
        self.journal_frame.pack_forget()
        self.home_frame.pack(fill=tk.BOTH, expand=True)
        self.budget_entry.delete(0, tk.END)
        self.budget_entry.insert(0, str(round(self.budget, 2)))
        self.update_home_stats()

    def show_results(self):
        self.home_frame.pack_forget()
        self.journal_frame.pack_forget()
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        self.update_budget_labels()

    def show_journal(self):
        self.home_frame.pack_forget()
        self.results_frame.pack_forget()
        self.journal_frame.pack(fill=tk.BOTH, expand=True)
        self.update_budget_labels()
        self.load_journal_data()

    def update_home_stats(self):
        stats_text = f"✅ ניצחונות: {self.wins}  |  ❌ הפסדים: {self.losses}    ||    💵 רווח נקי מצטבר: ₪{round(self.total_profit, 2)}  |  📉 הפסד מצטבר: ₪{round(self.total_loss, 2)}"
        self.lbl_home_stats.config(text=stats_text)

    def update_budget_labels(self):
        text = f"יתרה: ₪{round(self.budget, 2)} | נ: {self.wins} הפס: {self.losses} | רווח: ₪{round(self.total_profit, 2)} | הפסד: ₪{round(self.total_loss, 2)}"
        self.lbl_budget_display.config(text=text)
        self.lbl_journal_budget.config(text=text)

    def build_home_screen(self):
        tk.Label(self.home_frame, text="PROJECT STRIKER", font=("Arial", 38, "bold"), fg="#7aa2f7", bg="#1a1b26").pack(
            pady=(90, 10))

        self.lbl_home_stats = tk.Label(self.home_frame, text="", font=("Arial", 14), fg="#9ece6a", bg="#1a1b26")
        self.lbl_home_stats.pack(pady=(0, 20))

        input_frame = tk.Frame(self.home_frame, bg="#1a1b26")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text=":בנקרול כולל זמין (₪)", font=("Arial", 16), fg="#a9b1d6", bg="#1a1b26").pack(
            side=tk.RIGHT, padx=10)
        self.budget_entry = tk.Entry(input_frame, font=("Arial", 16, "bold"), width=12, justify="center", bg="#24283b",
                                     fg="#9ece6a", insertbackground="white")
        self.budget_entry.pack(side=tk.RIGHT)

        tk.Button(self.home_frame, text="🔍 סרוק שווקי לייב", font=("Arial", 14, "bold"), bg="#7aa2f7", fg="#1a1b26",
                  relief=tk.FLAT, command=self.start_scan, width=22, pady=12).pack(pady=(30, 15))

        tk.Button(self.home_frame, text="📖 צפה ביומן (סגירת תוצאות)", font=("Arial", 14, "bold"), bg="#bb9af7",
                  fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_journal, width=22, pady=12).pack(pady=10)

    def build_results_screen(self):
        top_bar = tk.Frame(self.results_frame, bg="#16161e", pady=15)
        top_bar.pack(fill=tk.X)

        tk.Button(top_bar, text="< חזור למסך הבית", font=("Arial", 11, "bold"), bg="#f7768e", fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_home).pack(side=tk.LEFT, padx=20)
        self.lbl_budget_display = tk.Label(top_bar, text="", font=("Arial", 12, "bold"), fg="#9ece6a", bg="#16161e")
        self.lbl_budget_display.pack(side=tk.RIGHT, padx=20)

        table_container = tk.Frame(self.results_frame, bg="#1a1b26", padx=30, pady=20)
        table_container.pack(fill=tk.BOTH, expand=True)

        columns = ("select", "match", "bet", "bookie", "target", "ev", "amount")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=10)

        self.tree.heading("select", text="V")
        self.tree.heading("match", text="🔗 שם המשחק (לחץ לפתיחה)")
        self.tree.heading("bet", text="הימור")
        self.tree.heading("bookie", text="סוכנות")
        self.tree.heading("target", text="יחס מטרה")
        self.tree.heading("ev", text="תוחלת (+EV)")
        self.tree.heading("amount", text="השקעה מומלצת (₪)")

        self.tree.column("select", anchor=tk.CENTER, width=40)
        self.tree.column("match", anchor=tk.W, width=280)
        self.tree.column("bet", anchor=tk.CENTER, width=150)
        self.tree.column("bookie", anchor=tk.CENTER, width=110)
        self.tree.column("target", anchor=tk.CENTER, width=100)
        self.tree.column("ev", anchor=tk.CENTER, width=110)
        self.tree.column("amount", anchor=tk.CENTER, width=140)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("checked", background="#1f2d24", foreground="#9ece6a")

        # הפתרון לתקיעות: מקשיב ללחיצה, אבל מפעיל את הקוד רק בחלק הבא של התהליך
        self.tree.bind("<Button-1>", self.on_results_click)

        action_frame = tk.Frame(self.results_frame, bg="#1a1b26", pady=15)
        action_frame.pack(fill=tk.X, padx=30)

        tk.Button(action_frame, text="🚀 אשר והימר על כל המסומנים", font=("Arial", 12, "bold"), bg="#9ece6a",
                  fg="#1a1b26",
                  relief=tk.FLAT, command=self.place_selected_bets, padx=20, pady=8).pack(side=tk.RIGHT)
        self.lbl_status = tk.Label(action_frame, text="לחץ על משחק לפתיחת האתר. לחץ בכל מקום אחר כדי לסמן V.",
                                   font=("Arial", 11, "italic"), fg="#7dcfff", bg="#1a1b26")
        self.lbl_status.pack(side=tk.LEFT)

    def build_journal_screen(self):
        top_bar = tk.Frame(self.journal_frame, bg="#16161e", pady=15)
        top_bar.pack(fill=tk.X)

        tk.Button(top_bar, text="< חזור למסך הבית", font=("Arial", 11, "bold"), bg="#f7768e", fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_home).pack(side=tk.LEFT, padx=20)
        self.lbl_journal_budget = tk.Label(top_bar, text="", font=("Arial", 12, "bold"), fg="#bb9af7", bg="#16161e")
        self.lbl_journal_budget.pack(side=tk.RIGHT, padx=20)

        table_container = tk.Frame(self.journal_frame, bg="#1a1b26", padx=30, pady=10)
        table_container.pack(fill=tk.BOTH, expand=True)

        # טבלה נקייה לחלוטין מנתונים נסתרים - מונע שגיאות 100%
        columns = ("match", "match_time", "stake", "odds", "potential_return")
        self.journal_tree = ttk.Treeview(table_container, columns=columns, show="headings", height=12)

        self.journal_tree.heading("match", text="משחק | קבוצה לבחירה")
        self.journal_tree.heading("match_time", text="📅 מועד המשחק")
        self.journal_tree.heading("stake", text="השקענו (₪)")
        self.journal_tree.heading("odds", text="יחס")
        self.journal_tree.heading("potential_return", text="החזר במקרה של זכייה (₪)")

        self.journal_tree.column("match", anchor=tk.W, width=350)
        self.journal_tree.column("match_time", anchor=tk.CENTER, width=120)
        self.journal_tree.column("stake", anchor=tk.CENTER, width=100)
        self.journal_tree.column("odds", anchor=tk.CENTER, width=80)
        self.journal_tree.column("potential_return", anchor=tk.CENTER, width=180)

        self.journal_tree.pack(fill=tk.BOTH, expand=True)

        self.journal_tree.bind("<Button-1>", self.on_journal_click)

        action_frame = tk.Frame(self.journal_frame, bg="#1a1b26", pady=15)
        action_frame.pack(fill=tk.X, padx=30)
        tk.Label(action_frame, text="💡 קליק על שורת הימור בטבלה יפתח חלון לדיווח תוצאה (ניצחון/הפסד).",
                 font=("Arial", 12),
                 fg="#a9b1d6", bg="#1a1b26").pack(side=tk.LEFT)

    def load_journal_data(self):
        for row in self.journal_tree.get_children():
            self.journal_tree.delete(row)

        self.journal_map.clear()  # איפוס הזיכרון החכם
        if not os.path.exists(LOG_FILE): return

        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)

                for row in reader:
                    if len(row) < 11: continue
                    if row[10].strip() != "בהמתנה": continue

                    full_match = row[1].strip()
                    bet_side = row[4].strip()

                    actual_team = bet_side
                    if " v " in full_match:
                        teams = full_match.split(" v ")
                        if bet_side == "Home":
                            actual_team = teams[0]
                        elif bet_side == "Away":
                            actual_team = teams[1]
                        elif bet_side == "Draw":
                            actual_team = "תיקו"

                    match_display = f"{full_match} | הימור: {actual_team}"
                    match_time = row[2]

                    try:
                        stake_val = float(row[9])
                        odds_val = float(row[7])
                        potential_return = round(stake_val * odds_val, 2)
                    except:
                        stake_val = 0.0
                        odds_val = 0.0
                        potential_return = 0.0

                    # שומרים את הנתונים בטבלה, ואת המזהה למחיקה שומרים בתוך המילון המובנה בקוד
                    item_id = self.journal_tree.insert("", tk.END,
                                                       values=(match_display, match_time, stake_val, odds_val,
                                                               potential_return))
                    original_key = f"{full_match} ({bet_side})"
                    self.journal_map[item_id] = original_key

        except Exception as e:
            print(f"[X] שגיאה בטעינת קובץ הלוג: {e}")

    # --- טיפול חכם ומבוטח בלחיצות ---
    def on_results_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item: return

        # מבקש מהמערכת לטפל בפעולה רק לאחר שהלחיצה שוחררה כדי למנוע התנגשויות
        self.root.after(50, lambda: self._process_results_click(item, column))

    def _process_results_click(self, item, column):
        values = list(self.tree.item(item, "values"))
        if not values: return

        if column == "#2":
            bookie_name = values[3]
            url = URL_MAP.get(bookie_name, f"https://www.google.com/search?q={bookie_name}+sportsbook")
            try:
                webbrowser.open(url)
            except:
                pass
        else:
            if values[0] == "☐":
                values[0] = "☑"
                self.tree.item(item, tags=("checked",))
            else:
                values[0] = "☐"
                self.tree.item(item, tags=())
            self.tree.item(item, values=values)

    def on_journal_click(self, event):
        item = self.journal_tree.identify_row(event.y)
        if not item: return

        # מבקש מהמערכת לעבור לפונקציית ההודעה רק בעוד מאית שנייה. פותר את פריז הקליק.
        self.root.after(50, lambda: self._process_journal_decision(item))

    def _process_journal_decision(self, item):
        if item not in self.journal_map: return

        values = self.journal_tree.item(item, "values")
        if not values: return

        display_name = values[0]
        original_key = self.journal_map[item]  # שליפה מובטחת של המפתח ללא קריסה

        try:
            stake_placed = float(values[2])
            payout = float(values[4])
        except:
            stake_placed = 0.0
            payout = 0.0

        answer = messagebox.askyesnocancel(
            "סגירת תוצאה - Project Striker",
            f"האם ההימור:\n{display_name}\n\nזכה והרוויח ₪{payout}?\n\n(כן = ניצחון | לא = הפסד | ביטול = חזור להתחלה)",
            icon='question',
            parent=self.root
        )

        if answer is True:
            net_profit = payout - stake_placed
            self.budget += payout
            self.wins += 1
            self.total_profit += net_profit

            save_bankroll_data(self.budget, self.wins, self.losses, self.total_profit, self.total_loss)
            self.update_budget_labels()
            update_csv_status(original_key, "ניצח")
            self.journal_tree.delete(item)
            del self.journal_map[item]
            messagebox.showinfo("קופה עודכנה", f"🔥 ניצחון נרשם! רווח נקי של ₪{round(net_profit, 2)} נוסף לקופה.",
                                parent=self.root)

        elif answer is False:
            self.losses += 1
            self.total_loss += stake_placed

            save_bankroll_data(self.budget, self.wins, self.losses, self.total_profit, self.total_loss)
            self.update_budget_labels()
            update_csv_status(original_key, "הפסיד")
            self.journal_tree.delete(item)
            del self.journal_map[item]
            messagebox.showinfo("קופה עודכנה", f"❌ הפסד נרשם. הפסדנו ₪{stake_placed}.", parent=self.root)

    def place_selected_bets(self):
        to_delete = []
        total_stake = 0.0

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == "☑":
                to_delete.append(item)
                total_stake += float(values[6])

        if not to_delete:
            messagebox.showwarning("שים לב", "נא לסמן לפחות משחק אחד ב-V!", parent=self.root)
            return

        if total_stake > self.budget:
            messagebox.showerror("שגיאה",
                                 f"אין מספיק תקציב!\nנדרש: ₪{round(total_stake, 1)} | זמין: ₪{round(self.budget, 1)}",
                                 parent=self.root)
            return

        self.budget -= total_stake
        save_bankroll_data(self.budget, self.wins, self.losses, self.total_profit, self.total_loss)
        self.update_budget_labels()

        for item in to_delete:
            try:
                original_data = self.current_results[int(item)]
                log_bet(original_data)
            except:
                pass
            self.tree.delete(item)

        messagebox.showinfo("הצלחה", f"בוצע! {len(to_delete)} הימורים נרשמו בהצלחה ביומן.", parent=self.root)

    def start_scan(self):
        try:
            self.budget = float(self.budget_entry.get())
            save_bankroll_data(self.budget, self.wins, self.losses, self.total_profit, self.total_loss)
        except ValueError:
            messagebox.showerror("שגיאה", "נא להכניס מספר תקציב תקין.", parent=self.root)
            return

        self.show_results()
        for row in self.tree.get_children(): self.tree.delete(row)
        self.lbl_status.config(text="סורק את השוק, אנא המתן...", fg="#e0af68")

        def scan_thread():
            self.current_results = scan_markets(self.budget)
            self.root.after(0, self.populate_table)

        threading.Thread(target=scan_thread, daemon=True).start()

    def populate_table(self):
        if not self.current_results:
            self.lbl_status.config(text="השוק מאוזן. לא נמצאו עסקאות בפילטר.", fg="#f7768e")
            return

        self.lbl_status.config(text=f"נמצאו {len(self.current_results)} עסקאות נקיות.", fg="#7dcfff")
        for idx, res in enumerate(self.current_results):
            full_match = res['match']
            bet_side = res['bet']

            actual_team = bet_side
            if " v " in full_match:
                teams = full_match.split(" v ")
                if bet_side == "Home":
                    actual_team = f"{teams[0]} (בית)"
                elif bet_side == "Away":
                    actual_team = f"{teams[1]} (חוץ)"
                elif bet_side == "Draw":
                    actual_team = "תיקו"

            self.tree.insert("", tk.END, iid=str(idx), values=(
                "☐",
                f"  {full_match}",
                actual_team,
                res["bookie"],
                res["offered"],
                f"+{res['ev']}%",
                res["amount"]
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = StrikerApp(root)
    root.mainloop()
