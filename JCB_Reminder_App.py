import json
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import END, StringVar, Tk, messagebox, ttk
from uuid import uuid4


DATA_FILE = Path(__file__).with_name("reminders.json")
REPEAT_OPTIONS = ["None", "Daily", "Weekly", "Monthly"]


class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JCB Reminder")
        self.root.geometry("840x620")
        self.root.minsize(720, 520)
        self.root.configure(bg="#f3f4f6")

        self.reminders = self.load_reminders()
        self.title_var = StringVar()
        self.date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.time_var = StringVar(value=datetime.now().strftime("%H:%M"))
        self.repeat_var = StringVar(value="None")

        self.apply_theme()
        self.build_ui()
        self.populate_reminders()
        self.schedule_checker()

    def apply_theme(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#f3f4f6")
        style.configure("TLabelframe", background="#f3f4f6")
        style.configure("TLabelframe.Label", background="#f3f4f6", foreground="#111827", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#f3f4f6", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#111827")
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#111827")
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background="#4f46e5", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#4338ca")], foreground=[("active", "#ffffff")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#111827", rowheight=28)
        style.configure("Treeview.Heading", background="#e5e7eb", foreground="#111827", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#c7d2fe")], foreground=[("selected", "#111827")])

    def build_ui(self):
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        form = ttk.LabelFrame(main, text="Add Reminder", padding=15)
        form.pack(fill="x", pady=(0, 12))

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
        ttk.Entry(form, textvariable=self.title_var, width=48, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="ew", pady=(0, 8), columnspan=3)

        ttk.Label(form, text="Date:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(form, textvariable=self.date_var, width=18, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Time:").grid(row=1, column=2, sticky="w", padx=(16, 10), pady=6)
        ttk.Entry(form, textvariable=self.time_var, width=18, font=("Segoe UI", 10)).grid(row=1, column=3, sticky="w", pady=6)

        ttk.Label(form, text="Repeat:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Combobox(form, textvariable=self.repeat_var, values=REPEAT_OPTIONS, state="readonly", width=18).grid(row=2, column=1, sticky="w", pady=6)

        ttk.Label(form, text="Description:").grid(row=3, column=0, sticky="nw", padx=(0, 10), pady=(10, 6))
        desc_box = tk.Text(form, height=5, width=70, font=("Segoe UI", 10), wrap="word", bg="#ffffff", fg="#111827")
        desc_box.grid(row=3, column=1, columnspan=3, sticky="ew", pady=(10, 6))
        self.desc_box = desc_box

        button_row = ttk.Frame(form)
        button_row.grid(row=4, column=1, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(button_row, text="Save Reminder", style="Accent.TButton", command=self.add_reminder).pack(side="left", padx=(0, 8))
        ttk.Button(button_row, text="Clear", command=self.clear_form).pack(side="left")

        list_frame = ttk.LabelFrame(main, text="Reminders", padding=12)
        list_frame.pack(fill="both", expand=True)

        self.reminder_list = ttk.Treeview(list_frame, columns=("date", "title", "status"), show="headings")
        self.reminder_list.heading("date", text="Date / Time")
        self.reminder_list.heading("title", text="Title")
        self.reminder_list.heading("status", text="Status")
        self.reminder_list.column("date", width=220, anchor="center")
        self.reminder_list.column("title", width=350)
        self.reminder_list.column("status", width=150, anchor="center")
        self.reminder_list.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reminder_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.reminder_list.configure(yscrollcommand=scrollbar.set)

        action_row = ttk.Frame(main)
        action_row.pack(fill="x", pady=(12, 0))
        ttk.Button(action_row, text="Delete Selected", command=self.delete_selected).pack(side="left")

    def normalize_reminder(self, reminder):
        if not isinstance(reminder, dict):
            return None

        reminder.setdefault("id", uuid4().hex)
        reminder.setdefault("title", "Untitled")
        reminder.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        reminder.setdefault("time", datetime.now().strftime("%H:%M"))
        reminder.setdefault("description", "")
        reminder.setdefault("repeat", "None")
        reminder.setdefault("notified", False)

        if "due" not in reminder:
            try:
                reminder["due"] = datetime.strptime(f"{reminder['date']} {reminder['time']}", "%Y-%m-%d %H:%M").isoformat()
            except ValueError:
                reminder["due"] = datetime.now().isoformat()

        return reminder

    def load_reminders(self):
        if not DATA_FILE.exists():
            return []

        try:
            with DATA_FILE.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return []

        if not isinstance(data, list):
            return []

        reminders = []
        for item in data:
            normalized = self.normalize_reminder(item)
            if normalized is not None:
                reminders.append(normalized)

        reminders.sort(key=lambda item: item["due"])
        return reminders

    def save_reminders(self):
        try:
            with DATA_FILE.open("w", encoding="utf-8") as handle:
                json.dump(self.reminders, handle, indent=2)
        except OSError as exc:
            messagebox.showerror("File Error", f"Unable to save reminders:\n{exc}")

    def clear_form(self):
        self.title_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.time_var.set(datetime.now().strftime("%H:%M"))
        self.repeat_var.set("None")
        self.desc_box.delete("1.0", END)

    def get_repeat_delta(self, repeat_value):
        if repeat_value == "Daily":
            return timedelta(days=1)
        if repeat_value == "Weekly":
            return timedelta(days=7)
        if repeat_value == "Monthly":
            return timedelta(days=30)
        return None

    def add_reminder(self):
        title = self.title_var.get().strip()
        reminder_date = self.date_var.get().strip()
        reminder_time = self.time_var.get().strip()
        description = self.desc_box.get("1.0", END).strip()
        repeat_value = self.repeat_var.get()

        if not title or not reminder_date or not reminder_time:
            messagebox.showwarning("Missing Data", "Please enter a title, date, and time.")
            return

        try:
            due_datetime = datetime.strptime(f"{reminder_date} {reminder_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please use the format YYYY-MM-DD and HH:MM.")
            return

        reminder = {
            "id": uuid4().hex,
            "title": title,
            "date": reminder_date,
            "time": reminder_time,
            "description": description,
            "due": due_datetime.isoformat(),
            "repeat": repeat_value,
            "notified": False,
        }

        self.reminders.append(reminder)
        self.reminders.sort(key=lambda item: item["due"])
        self.save_reminders()
        self.populate_reminders()
        self.clear_form()

    def populate_reminders(self):
        for item in self.reminder_list.get_children():
            self.reminder_list.delete(item)

        now = datetime.now()
        for reminder in self.reminders:
            due_dt = datetime.fromisoformat(reminder["due"])

            if reminder.get("notified") and reminder.get("repeat") == "None":
                status = "Done"
            elif due_dt <= now:
                status = "Due"
            else:
                status = "Upcoming"

            self.reminder_list.insert(
                "",
                "end",
                values=(due_dt.strftime("%Y-%m-%d %H:%M"), reminder["title"], status),
                iid=reminder["id"],
            )

    def delete_selected(self):
        selected = self.reminder_list.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select a reminder to delete.")
            return

        reminder_id = selected[0]
        self.reminders = [item for item in self.reminders if item["id"] != reminder_id]
        self.save_reminders()
        self.populate_reminders()

    def trigger_reminder(self, reminder):
        due_dt = datetime.fromisoformat(reminder["due"])
        description = reminder.get("description") or "No description provided."
        repeat_label = reminder.get("repeat", "None")

        if repeat_label == "None":
            reminder["notified"] = True
            messagebox.showinfo(
                "Reminder",
                f"{reminder['title']}\n\nDue: {due_dt.strftime('%Y-%m-%d %H:%M')}\n\n{description}",
            )
            return

        delta = self.get_repeat_delta(repeat_label)
        if delta is None:
            reminder["notified"] = True
            return

        next_due = due_dt + delta
        reminder["due"] = next_due.isoformat()
        reminder["date"] = next_due.strftime("%Y-%m-%d")
        reminder["time"] = next_due.strftime("%H:%M")
        reminder["notified"] = False

        messagebox.showinfo(
            "Reminder",
            f"{reminder['title']}\n\nTriggered: {due_dt.strftime('%Y-%m-%d %H:%M')}\n\nNext {repeat_label.lower()} reminder: {next_due.strftime('%Y-%m-%d %H:%M')}\n\n{description}",
        )

    def check_due_reminders(self):
        changed = False
        now = datetime.now()

        for reminder in self.reminders:
            if not isinstance(reminder, dict):
                continue

            due_dt = datetime.fromisoformat(reminder["due"])
            if due_dt <= now and not reminder.get("notified"):
                self.trigger_reminder(reminder)
                changed = True

        if changed:
            self.reminders.sort(key=lambda item: item["due"])
            self.save_reminders()
            self.populate_reminders()

        self.schedule_checker()

    def schedule_checker(self):
        self.root.after(5000, self.check_due_reminders)


def main():
    root = Tk()
    ReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

