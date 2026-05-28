import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from main import scan_markets

BANKROLL_FILE = "bankroll.json"


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
    # שומר רק את היתרה (אפשר להרחיב בהמשך למעקב היסטורי מלא)
    data = {"balance": amount}
    with open(BANKROLL_FILE, "w") as f:
        json.dump(data, f)


class StrikerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Striker - Value Dashboard")
        self.root.geometry("1050x550")

        self.budget = load_budget()

        # --- יצירת שני מסכים (Frames) ---
        self.home_frame = tk.Frame(self.root)
        self.results_frame = tk.Frame(self.root)

        self.build_home_screen()
        self.build_results_screen()

        # מתחילים תמיד ממסך הבית
        self.show_home()

    def show_home(self):
        self.results_frame.pack_forget()
        self.home_frame.pack(fill=tk.BOTH, expand=True)
        # עדכון שדה הטקסט עם התקציב השמור
        self.budget_entry.delete(0, tk.END)
        self.budget_entry.insert(0, str(round(self.budget, 2)))

    def show_results(self):
        self.home_frame.pack_forget()
        self.results_frame.pack(fill=tk.BOTH, expand=True)
        self.update_budget_label()

    def build_home_screen(self):
        # כותרת מרכזית
        tk.Label(self.home_frame, text="PROJECT STRIKER", font=("Arial", 32, "bold")).pack(pady=(100, 30))

        input_frame = tk.Frame(self.home_frame)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text=":בנקרול כולל זמין (₪)", font=("Arial", 16)).pack(side=tk.RIGHT, padx=10)
        self.budget_entry = tk.Entry(input_frame, font=("Arial", 16), width=12, justify="center")
        self.budget_entry.pack(side=tk.RIGHT)

        tk.Button(self.home_frame, text="התחל סריקת שווקים", font=("Arial", 14, "bold"), bg="#1a1a1a", fg="white",
                  command=self.start_scan, width=20, pady=10).pack(pady=40)

    def build_results_screen(self):
        # בר עליון (חזרה למסך קודם + תצוגת תקציב)
        top_bar = tk.Frame(self.results_frame, bg="#2c3e50", pady=10)
        top_bar.pack(fill=tk.X)

        tk.Button(top_bar, text="< חזור", font=("Arial", 10, "bold"), command=self.show_home).pack(side=tk.LEFT,
                                                                                                   padx=15)

        self.lbl_budget_display = tk.Label(top_bar, text="", font=("Arial", 14, "bold"), fg="#deff9a", bg="#2c3e50")
        self.lbl_budget_display.pack(side=tk.RIGHT, padx=20)

        # טבלת נתונים
        columns = ("match", "bet", "pin", "bookie", "target", "ev", "kelly", "amount")
        self.tree = ttk.Treeview(self.results_frame, columns=columns, show="headings", height=15)

        self.tree.heading("match", text="משחק")
        self.tree.heading("bet", text="הימור")
        self.tree.heading("pin", text="יחס פינאקל")
        self.tree.heading("bookie", text="סוכנות")
        self.tree.heading("target", text="יחס מטרה")
        self.tree.heading("ev", text="תוחלת (+EV)")
        self.tree.heading("kelly", text="קלי (Kelly)")
        self.tree.heading("amount", text="השקעה מומלצת (₪)")

        for col in columns:
            self.tree.column(col, anchor=tk.CENTER, width=100)
        self.tree.column("match", width=220)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # בר תחתון (סטטוס סריקה + כפתור ביצוע הימור)
        action_frame = tk.Frame(self.results_frame, pady=10)
        action_frame.pack(fill=tk.X)

        tk.Button(action_frame, text="✅ הימרתי (הורד מהתקציב)", font=("Arial", 12, "bold"), bg="#27ae60", fg="white",
                  command=self.place_bet, padx=10, pady=5).pack(side=tk.RIGHT, padx=20)

        self.lbl_status = tk.Label(action_frame, text="", font=("Arial", 12))
        self.lbl_status.pack(side=tk.LEFT, padx=20)

    def update_budget_label(self):
        self.lbl_budget_display.config(text=f"תקציב זמין: ₪{round(self.budget, 2)}")

    def start_scan(self):
        try:
            # שומרים את התקציב שהוזן במסך הבית כנקודת הפתיחה
            new_budget = float(self.budget_entry.get())
            self.budget = new_budget
            save_budget(self.budget)
        except ValueError:
            messagebox.showerror("שגיאה", "אנא הכנס תקציב תקין במספרים.")
            return

        # עוברים למסך התוצאות
        self.show_results()

        # מנקים טבלה ישנה
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.lbl_status.config(text="סורק שווקים... (נא להמתין)", fg="orange")

        # מריצים את הסריקה ברקע
        def scan_thread():
            results = scan_markets()
            self.root.after(0, self.populate_table, results)

        threading.Thread(target=scan_thread, daemon=True).start()

    def populate_table(self, results):
        if not results:
            self.lbl_status.config(text="השוק מאוזן. לא נמצאו עסקאות שעומדות בפילטר.", fg="red")
            return

        self.lbl_status.config(text=f"נמצאו {len(results)} עסקאות", fg="green")

        for res in results:
            # חישוב הסכום המדויק להשקעה ביחס לבנקרול
            bet_amount_ils = self.budget * (res["kelly"] / 100)

            self.tree.insert("", tk.END, values=(
                res["match"],
                res["bet"],
                res["pin_odds"],
                res["bookie"],
                res["target_odds"],
                f"+{res['ev']}%",
                f"{res['kelly']}%",
                round(bet_amount_ils, 2)
            ))

    def place_bet(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("שים לב", "אנא סמן שורה מהטבלה לפני שאתה לוחץ על 'הימרתי'.")
            return

        item = selected_item[0]
        values = self.tree.item(item, "values")
        bet_amount = float(values[7])  # הסכום נמצא בעמודה ה-8 (אינדקס 7)

        if bet_amount > self.budget:
            messagebox.showerror("שגיאה", "אין לך מספיק תקציב להימור זה! חזור למסך הבית לעדכון הבנקרול.")
            return

        # הורדה מהתקציב השמור
        self.budget -= bet_amount
        save_budget(self.budget)
        self.update_budget_label()

        # מחיקת השורה מהטבלה כדי שלא נלחץ עליה שוב בטעות
        self.tree.delete(item)
        messagebox.showinfo("הצלחה", f"ההימור נרשם! ירדו ₪{bet_amount} מהבנקרול שלך.")


if __name__ == "__main__":
    root = tk.Tk()
    app = StrikerApp(root)
    root.mainloop()