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

URL_MAP = {
    "FANDUEL": "https://sportsbook.fanduel.com/",
    "UNIBET": "https://www.unibet.com/",
    "BETONLIN": "https://www.betonline.ag/",
    "BOVADA": "https://www.bovada.lv/",
    "STAKE": "https://stake.com/sports",
    "BET365": "https://www.bet365.com/",
}


def load_budget():
    if os.path.exists(BANKROLL_FILE):
        try:
            with open(BANKROLL_FILE, "r") as f:
                data = json.load(f)
                return data.get("balance", 1000.0)
        except:
            pass
    return 1000.0


def save_budget(amount):
    data = {"balance": amount}
    with open(BANKROLL_FILE, "w") as f:
        json.dump(data, f)


class StrikerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Striker - Pro Terminal")
        self.root.geometry("1150x600")
        self.root.configure(bg="#1a1b26")

        self.budget = load_budget()
        self.current_results = []

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#24283b", foreground="#a9b1d6", fieldbackground="#24283b", rowheight=38,
                        borderwidth=0, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#16161e", foreground="#7aa2f7", font=("Arial", 11, "bold"),
                        borderwidth=0)

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

    def show_results(self):
        self.home_frame.pack_forget()
        self.journal_frame.pack_forget()
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        self.update_budget_label()

    def show_journal(self):
        self.home_frame.pack_forget()
        self.results_frame.pack_forget()
        self.journal_frame.pack(fill=tk.BOTH, expand=True)
        self.load_journal_data()

    def build_home_screen(self):
        tk.Label(self.home_frame, text="PROJECT STRIKER", font=("Arial", 38, "bold"), fg="#7aa2f7", bg="#1a1b26").pack(
            pady=(90, 20))

        input_frame = tk.Frame(self.home_frame, bg="#1a1b26")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text=":בנקרול כולל זמין (₪)", font=("Arial", 16), fg="#a9b1d6", bg="#1a1b26").pack(
            side=tk.RIGHT, padx=10)
        self.budget_entry = tk.Entry(input_frame, font=("Arial", 16, "bold"), width=12, justify="center", bg="#24283b",
                                     fg="#9ece6a", insertbackground="white")
        self.budget_entry.pack(side=tk.RIGHT)

        tk.Button(self.home_frame, text="🔍 סרוק שווקי לייב", font=("Arial", 14, "bold"), bg="#7aa2f7", fg="#1a1b26",
                  relief=tk.FLAT, command=self.start_scan, width=22, pady=12).pack(pady=(30, 15))

        tk.Button(self.home_frame, text="📖 צפה ביומן ההימורים", font=("Arial", 14, "bold"), bg="#bb9af7", fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_journal, width=22, pady=12).pack(pady=10)

    def build_results_screen(self):
        top_bar = tk.Frame(self.results_frame, bg="#16161e", pady=15)
        top_bar.pack(fill=tk.X)

        tk.Button(top_bar, text="< חזור למסך הבית", font=("Arial", 11, "bold"), bg="#f7768e", fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_home).pack(side=tk.LEFT, padx=20)
        self.lbl_budget_display = tk.Label(top_bar, text="", font=("Arial", 16, "bold"), fg="#9ece6a", bg="#16161e")
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
        self.tree.column("bet", anchor=tk.CENTER, width=100)
        self.tree.column("bookie", anchor=tk.CENTER, width=110)
        self.tree.column("target", anchor=tk.CENTER, width=100)
        self.tree.column("ev", anchor=tk.CENTER, width=110)
        self.tree.column("amount", anchor=tk.CENTER, width=140)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tag_configure("checked", background="#1f2d24", foreground="#9ece6a")
        self.tree.bind("<Button-1>", self.on_table_click)

        action_frame = tk.Frame(self.results_frame, bg="#1a1b26", pady=15)
        action_frame.pack(fill=tk.X, padx=30)

        tk.Button(action_frame, text="🚀 אשר והימר על כל המסומנים", font=("Arial", 12, "bold"), bg="#9ece6a",
                  fg="#1a1b26",
                  relief=tk.FLAT, command=self.place_selected_bets, padx=20, pady=8).pack(side=tk.RIGHT)

        self.lbl_status = tk.Label(action_frame, text="קליק על [ ] מסמן וי. קליק על שם המשחק פותח את האתר.",
                                   font=("Arial", 11, "italic"), fg="#7dcfff", bg="#1a1b26")
        self.lbl_status.pack(side=tk.LEFT)

    def build_journal_screen(self):
        top_bar = tk.Frame(self.journal_frame, bg="#16161e", pady=15)
        top_bar.pack(fill=tk.X)

        tk.Button(top_bar, text="< חזור למסך הבית", font=("Arial", 11, "bold"), bg="#f7768e", fg="#1a1b26",
                  relief=tk.FLAT, command=self.show_home).pack(side=tk.LEFT, padx=20)
        tk.Label(top_bar, text="📜 יומן הימורים רשומים", font=("Arial", 16, "bold"), fg="#bb9af7", bg="#16161e").pack(
            side=tk.RIGHT, padx=20)

        table_container = tk.Frame(self.journal_frame, bg="#1a1b26", padx=30, pady=20)
        table_container.pack(fill=tk.BOTH, expand=True)

        # הוספת עמודת מועד המשחק לטבלה הויזואלית
        columns = ("match", "match_time", "stake", "profit", "status")
        self.journal_tree = ttk.Treeview(table_container, columns=columns, show="headings", height=12)

        self.journal_tree.heading("match", text="משחק / סוג הימור")
        self.journal_tree.heading("match_time", text="📅 מועד המשחק")
        self.journal_tree.heading("stake", text="כמה הימרנו (₪)")
        self.journal_tree.heading("profit", text="כמה אמור להרוויח (₪)")
        self.journal_tree.heading("status", text="סטטוס")

        self.journal_tree.column("match", anchor=tk.W, width=300)
        self.journal_tree.column("match_time", anchor=tk.CENTER, width=140)
        self.journal_tree.column("stake", anchor=tk.CENTER, width=120)
        self.journal_tree.column("profit", anchor=tk.CENTER, width=150)
        self.journal_tree.column("status", anchor=tk.CENTER, width=120)

        self.journal_tree.pack(fill=tk.BOTH, expand=True)

    def load_journal_data(self):
        for row in self.journal_tree.get_children():
            self.journal_tree.delete(row)

        if not os.path.exists(LOG_FILE): return

        try:
            with open(LOG_FILE, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # דילוג על כותרות

                for row in reader:
                    if len(row) < 11: continue
                    match_display = f"{row[1]} ({row[4]})"
                    match_time = row[2]  # שאיבת מועד המשחק החדש
                    stake = f"₪{row[9]}"

                    try:
                        offered_odds = float(row[7])
                        stake_value = float(row[9])
                        profit_value = round(stake_value * (offered_odds - 1), 1)
                        profit = f"₪{profit_value}"
                    except:
                        profit = "N/A"

                    status = row[10]

                    self.journal_tree.insert("", tk.END, values=(match_display, match_time, stake, profit, status))
        except Exception as e:
            print(f"[X] שגיאה בטעינת קובץ הלוג: {e}")

    def on_table_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item: return
        values = list(self.tree.item(item, "values"))

        if column == "#1":
            if values[0] == "☐":
                values[0] = "☑"
                self.tree.item(item, tags=("checked",))
            else:
                values[0] = "☐"
                self.tree.item(item, tags=())
            self.tree.item(item, values=values)

        elif column == "#2":
            bookie_name = values[3]
            url = URL_MAP.get(bookie_name, f"https://www.google.com/search?q={bookie_name}+sportsbook")
            webbrowser.open(url)

    def place_selected_bets(self):
        to_delete = []
        total_stake = 0.0

        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == "☑":
                to_delete.append(item)
                total_stake += float(values[6])

        if not to_delete:
            messagebox.showwarning("שים לב", "נא לסמן לפחות משחק אחד ב-V!")
            return

        if total_stake > self.budget:
            messagebox.showerror("שגיאה",
                                 f"אין מספיק תקציב!\nנדרש: ₪{round(total_stake, 1)} | זמין: ₪{round(self.budget, 1)}")
            return

        self.budget -= total_stake
        save_budget(self.budget)
        self.update_budget_label()

        for item in to_delete:
            try:
                original_data = self.current_results[int(item)]
                log_bet(original_data)
            except:
                pass
            self.tree.delete(item)

        messagebox.showinfo("הצלחה", f"בוצע! {len(to_delete)} הימורים נרשמו בהצלחה ביומן החדש.")

    def update_budget_label(self):
        self.lbl_budget_display.config(text=f"יתרה: ₪{round(self.budget, 2)}")

    def start_scan(self):
        try:
            self.budget = float(self.budget_entry.get())
            save_budget(self.budget)
        except ValueError:
            messagebox.showerror("שגיאה", "נא להכניס מספר תקציב תקין.")
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
            self.tree.insert("", tk.END, iid=str(idx), values=(
                "☐",
                f"  {res['match']}",
                res["bet"],
                res["bookie"],
                res["offered"],
                f"+{res['ev']}%",
                res["amount"]
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = StrikerApp(root)
    root.mainloop()