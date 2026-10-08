import json
from datetime import datetime
from pathlib import Path
from tkinter import END, StringVar, Tk, messagebox, ttk
from uuid import uuid4


DATA_FILE = Path(__file__).with_name("reminders.json")


class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JCB Reminder")
        self.root.geometry("720x520")
        self.root.resizable(True, True)

        self.reminders = self.load_reminders()
        self.selected_id = None

        self.title_var = StringVar()
        self.date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.time_var = StringVar(value=datetime.now().strftime("%H:%M"))

        self.build_ui()
        self.populate_reminders()
        self.schedule_checker()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        form = ttk.LabelFrame(main, text="Add Reminder", padding=12)
        form.pack(fill="x", pady=(0, 10))

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(form, textvariable=self.title_var, width=50).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Date:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(form, textvariable=self.date_var, width=20).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(form, text="Time:").grid(row=1, column=2, sticky="w", padx=(10, 10), pady=4)
        ttk.Entry(form, textvariable=self.time_var, width=20).grid(row=1, column=3, sticky="w", pady=4)

        ttk.Label(form, text="Description:").grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=(8, 4))
        desc_box = ttk.Text(form, height=5, width=60)
        desc_box.grid(row=2, column=1, columnspan=3, sticky="ew", pady=(8, 4))
        self.desc_box = desc_box

        buttons = ttk.Frame(form)
        buttons.grid(row=3, column=1, columnspan=3, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text="Save Reminder", command=self.add_reminder).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Clear", command=self.clear_form).pack(side="left")

        list_frame = ttk.LabelFrame(main, text="Reminders", padding=10)
        list_frame.pack(fill="both", expand=True)

        self.reminder_list = ttk.Treeview(list_frame, columns=("date", "title", "status"), show="headings")
        self.reminder_list.heading("date", text="Date / Time")
        self.reminder_list.heading("title", text="Title")
        self.reminder_list.heading("status", text="Status")
        self.reminder_list.column("date", width=180, anchor="center")
        self.reminder_list.column("title", width=280)
        self.reminder_list.column("status", width=120, anchor="center")
        self.reminder_list.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.reminder_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.reminder_list.configure(yscrollcommand=scrollbar.set)

        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Delete Selected", command=self.delete_selected).pack(side="left")

    def load_reminders(self):
        if not DATA_FILE.exists():
            return []
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def save_reminders(self):
        try:
            with DATA_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.reminders, file, indent=2)
        except OSError as exc:
            messagebox.showerror("File Error", f"Unable to save reminders:\n{exc}")

    def clear_form(self):
        self.title_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.time_var.set(datetime.now().strftime("%H:%M"))
        self.desc_box.delete("1.0", END)

    def add_reminder(self):
        title = self.title_var.get().strip()
        reminder_date = self.date_var.get().strip()
        reminder_time = self.time_var.get().strip()
        description = self.desc_box.get("1.0", END).strip()

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

        for reminder in self.reminders:
            due_dt = datetime.fromisoformat(reminder["due"])
            status = "Due" if not reminder.get("notified") and due_dt <= datetime.now() else "Pending"
            if reminder.get("notified"):
                status = "Done"
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

    def check_due_reminders(self):
        changed = False
        for reminder in self.reminders:
            if reminder.get("notified"):
                continue
            due_dt = datetime.fromisoformat(reminder["due"])
            if due_dt <= datetime.now():
                reminder["notified"] = True
                changed = True
                messagebox.showinfo(
                    "Reminder",
                    f"{reminder['title']}\n\nDue: {reminder['date']} {reminder['time']}\n\n{reminder['description'] or 'No description provided.'}",
                )

        if changed:
            self.save_reminders()
            self.populate_reminders()

        self.schedule_checker()

    def schedule_checker(self):
        self.root.after(5000, self.check_due_reminders)


def main():
    root = Tk()
    app = ReminderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
