import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

BASE_DIR = Path(__file__).resolve().parent
TASK_FILE = BASE_DIR / "tasks.json"
STUDY_FILE = BASE_DIR / "Studytime.csv"
HABIT_FILE = BASE_DIR / "habits.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BG = "#F7F5F0"
SIDEBAR = "#E8F0EA"
CARD = "#FFFFFF"
TEXT = "#26352F"
MUTED = "#78877F"
GREEN = "#A8C7B5"
GREEN_DARK = "#527A65"
PEACH = "#F4D7C5"
LAVENDER = "#E4DDF2"
BORDER = "#E5E9E3"

WEEKLY_GOAL_HOURS = 15

def load_tasks():
    if not TASK_FILE.exists():
        return []
    try:
        with TASK_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_tasks(tasks):
    with TASK_FILE.open("w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4)


def read_study_records():
    records = []
    if not STUDY_FILE.exists():
        return records
    try:
        with STUDY_FILE.open("r", newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                try:
                    records.append({
                        "Date": row["Date"],
                        "Category": row["Category"],
                        "Hours": float(row["Hours"])
                    })
                except (KeyError, ValueError):
                    continue
    except OSError:
        pass
    return records


def total_study_hours():
    return sum(record["Hours"] for record in read_study_records())

def load_habits():
    if not HABIT_FILE.exists():
        return []

    try:
        with HABIT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_habits(habits):
    with HABIT_FILE.open("w", encoding="utf-8") as file:
        json.dump(habits, file, indent=4)

def get_habit_stats(completed_dates):
    today = datetime.now().date()

    valid_dates = set()

    for item in completed_dates:
        try:
            valid_dates.add(datetime.strptime(item, "%Y-%m-%d").date())
        except ValueError:
            continue

    # Weekly progress (Monday to Sunday)
    week_start = today - timedelta(days=today.weekday())

    weekly_count = sum(
        1 for day in valid_dates
        if week_start <= day <= today
    )

    # Consecutive-day streak
    if today in valid_dates:
        current_day = today
    elif today - timedelta(days=1) in valid_dates:
        current_day = today - timedelta(days=1)
    else:
        return weekly_count, 0

    streak = 0

    while current_day in valid_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return weekly_count, streak
    
class StudyPlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Study Planner | Productivity Tracker")
        self.geometry("1280x800")
        self.minsize(1050, 680)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self.build_sidebar()
        self.build_main_shell()
        self.show_dashboard()

    def build_sidebar(self):

        ctk.CTkLabel(
            self.sidebar, text="✿  STUDY SPACE",
            font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=22, pady=(30, 6))
        ctk.CTkLabel(
            self.sidebar, text="Plan gently. Make progress.",
            font=ctk.CTkFont(size=12), text_color=MUTED
        ).pack(anchor="w", padx=24, pady=(0, 28))

        buttons = [
            ("⌂   Dashboard", self.show_dashboard),
            ("＋   Add a task", self.add_task_screen),
            ("▤   All tasks", lambda: self.view_tasks(False)),
            ("✓   Completed tasks", lambda: self.view_tasks(True)),
            ("◷   Log study time", self.log_study_time_screen),
            ("▥   Weekly analytics", self.weekly_analytics_screen),
            ("♡   Habit tracker", self.habit_tracker_screen),
            ("✧   Productivity insights", self.productivity_insights_screen),
        ]
        for label, command in buttons:
            ctk.CTkButton(
                self.sidebar, text=label, command=command, height=43,
                corner_radius=12, anchor="w", fg_color="transparent",
                hover_color="#D7E5DA", text_color=TEXT,
                font=ctk.CTkFont(size=14)
            ).pack(fill="x", padx=13, pady=4)

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True, fill="both")
        ctk.CTkLabel(
            self.sidebar, text="YOUR DAILY RESET  ♡",
            text_color=GREEN_DARK, font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="w", padx=22, pady=(0, 22))

    def build_main_shell(self):
        self.header = ctk.CTkFrame(self.main, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.header.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.header, text="Your study dashboard",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=TEXT
        )
        self.page_title.grid(row=0, column=0, sticky="w")
        self.date_label = ctk.CTkLabel(
            self.header, text=datetime.now().strftime("%A, %d %B %Y"),
            font=ctk.CTkFont(size=13), text_color=MUTED
        )
        self.date_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.cards = ctk.CTkFrame(self.main, fg_color="transparent")
        self.cards.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        for column in range(3):
            self.cards.grid_columnconfigure(column, weight=1)

        self.display = ctk.CTkFrame(
            self.main, fg_color=CARD, corner_radius=18,
            border_width=1, border_color=BORDER
        )
        self.display.grid(row=2, column=0, sticky="nsew")
        self.display.grid_columnconfigure(0, weight=1)
        self.display.grid_rowconfigure(0, weight=1)

    def clear_display(self):
        for widget in self.display.winfo_children():
            widget.destroy()

    def set_page_title(self, title, subtitle=None):
        self.page_title.configure(text=title)
        self.date_label.configure(
            text=subtitle if subtitle else datetime.now().strftime("%A, %d %B %Y")
        )

    def refresh_cards(self):
        for widget in self.cards.winfo_children():
            widget.destroy()
        tasks = load_tasks()
        completed = sum(1 for task in tasks if task.get("status") == "completed")
        hours = total_study_hours()
        card_data = [
            ("TOTAL TASKS", str(len(tasks)), GREEN),
            ("COMPLETED", str(completed), PEACH),
            ("STUDY HOURS", f"{hours:.1f} hrs", LAVENDER),
        ]
        for column, (label, value, color) in enumerate(card_data):
            card = ctk.CTkFrame(self.cards, fg_color=color, corner_radius=16, height=100)
            card.grid(
                row=0, column=column, sticky="ew",
                padx=(0 if column == 0 else 9, 9 if column < 2 else 0)
            )
            card.grid_propagate(False)
            ctk.CTkLabel(
                card, text=label, text_color=TEXT,
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(anchor="w", padx=18, pady=(17, 5))
            ctk.CTkLabel(
                card, text=value, text_color=TEXT,
                font=ctk.CTkFont(size=25, weight="bold")
            ).pack(anchor="w", padx=18)

    def section_heading(self, parent, title, subtitle=None):
        ctk.CTkLabel(
            parent, text=title, text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold")
        ).pack(anchor="w", padx=22, pady=(20, 3))
        if subtitle:
            ctk.CTkLabel(
                parent, text=subtitle, text_color=MUTED,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=22, pady=(0, 12))

    def show_dashboard(self):
        self.set_page_title("Your study dashboard", "A little progress every day adds up. ♡")
        self.refresh_cards()
        self.clear_display()

        wrapper = ctk.CTkFrame(self.display, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=20, pady=8)
        wrapper.grid_columnconfigure((0, 1), weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        tasks = load_tasks()
        completed = sum(1 for task in tasks if task.get("status") == "completed")
        progress = completed / len(tasks) if tasks else 0

        progress_card = ctk.CTkFrame(wrapper, fg_color="#F1F6F1", corner_radius=16)
        progress_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=8)
        ctk.CTkLabel(
            progress_card, text="Today's task progress",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(17, 3))
        ctk.CTkLabel(
            progress_card, text=f"{completed} of {len(tasks)} tasks completed",
            text_color=MUTED, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=18, pady=(0, 12))
        bar = ctk.CTkProgressBar(progress_card, progress_color=GREEN_DARK, fg_color="#DCE7DE")
        bar.pack(fill="x", padx=18, pady=(0, 18))
        bar.set(progress)

        goal_card = ctk.CTkFrame(wrapper, fg_color="#FBF1E9", corner_radius=16)
        goal_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=8)
        ctk.CTkLabel(
            goal_card, text="Study time recorded",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(17, 3))
        ctk.CTkLabel(
            goal_card, text=f"{total_study_hours():.1f} hours in total",
            text_color=MUTED, font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=18, pady=(0, 12))
        ctk.CTkLabel(
            goal_card, text="Keep showing up for your goals. ✿",
            text_color=GREEN_DARK, font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=18, pady=(0, 18))

        recent = ctk.CTkFrame(wrapper, fg_color="#FAF9F6", corner_radius=16)
        recent.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=8)
        self.section_heading(recent, "Your tasks", "A quick look at what you're working on")
        pending = [task for task in tasks if task.get("status") != "completed"][:5]
        if not pending:
            ctk.CTkLabel(
                recent, text="You're all caught up. Add a new task when you're ready!",
                text_color=MUTED
            ).pack(anchor="w", padx=22, pady=12)
        else:
            for task in pending:
                row = ctk.CTkFrame(recent, fg_color="white", corner_radius=10)
                row.pack(fill="x", padx=18, pady=4)
                ctk.CTkLabel(
                    row, text="○", text_color=GREEN_DARK,
                    font=ctk.CTkFont(size=17)
                ).pack(side="left", padx=(12, 8), pady=8)
                ctk.CTkLabel(
                    row, text=task.get("title", "Untitled task"), text_color=TEXT
                ).pack(side="left", padx=4, pady=8)
                ctk.CTkLabel(
                    row, text=task.get("deadline", ""), text_color=MUTED
                ).pack(side="right", padx=12)

    def add_task_screen(self):
        self.set_page_title("Add a task", "Break your goals into small, manageable steps.")
        self.refresh_cards()
        self.clear_display()
        self.section_heading(self.display, "Create a new task", "Add a title and deadline to stay organised.")
        form = ctk.CTkFrame(self.display, fg_color="transparent")
        form.pack(anchor="nw", padx=24, pady=10)

        ctk.CTkLabel(form, text="Task title", text_color=TEXT).pack(anchor="w", pady=(4, 5))
        title_entry = ctk.CTkEntry(
            form, width=430, height=40, placeholder_text="e.g. Revise Computer Networks"
        )
        title_entry.pack(anchor="w", pady=(0, 16))
        ctk.CTkLabel(form, text="Deadline (DD-MM-YYYY)", text_color=TEXT).pack(anchor="w", pady=(0, 5))
        deadline_entry = ctk.CTkEntry(
            form, width=430, height=40, placeholder_text="e.g. 25-11-2026"
        )
        deadline_entry.pack(anchor="w", pady=(0, 20))


        ctk.CTkLabel(
            form,
            text="Task priority",
            text_color=TEXT
        ).pack(anchor="w", pady=(0, 5))

        priority_option = ctk.CTkOptionMenu(
            form,
            width=430,
            height=40,
            values=["High", "Medium", "Low"],
            fg_color=GREEN_DARK,
            button_color=GREEN_DARK,
            button_hover_color="#416653"
        )
        priority_option.set("Medium")
        priority_option.pack(anchor="w", pady=(0, 20))

        def save():
            task_title = title_entry.get().strip()
            deadline = deadline_entry.get().strip()
            if not task_title:
                messagebox.showwarning("Missing title", "Please enter a task title.")
                return
            try:
                datetime.strptime(deadline, "%d-%m-%Y")
            except ValueError:
                messagebox.showwarning("Invalid deadline", "Enter the deadline in DD-MM-YYYY format.")
                return
            tasks = load_tasks()
            next_id = max((task.get("id", 0) for task in tasks), default=0) + 1
            
            tasks.append({
                "id": next_id,
                "title": task_title,
                "added_date": datetime.now().strftime("%Y-%m-%d"),
                "deadline": deadline,
                "status": "pending",
                "priority": priority_option.get()
            })

            save_tasks(tasks)
            self.refresh_cards()
            messagebox.showinfo("Task added", "Your task has been saved successfully.")
            self.show_dashboard()

        ctk.CTkButton(
            form, text="Save task", width=160, height=40,
            corner_radius=10, fg_color=GREEN_DARK, hover_color="#416653",
            command=save
        ).pack(anchor="w")

    
    def view_tasks(self, only_completed=False):
        title = "Completed tasks" if only_completed else "All tasks"
        self.set_page_title(title, "Review your tasks and keep moving forward.")
        self.refresh_cards()
        self.clear_display()
        self.section_heading(self.display, title, "Your task list")

        # Search and filter section
        filter_frame = ctk.CTkFrame(self.display, fg_color="transparent")
        filter_frame.pack(fill="x", padx=22, pady=(5, 10))

        search_var = tk.StringVar()

        search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="🔍 Search tasks by name...",
            textvariable=search_var,
            width=300,
            height=38
        )
        search_entry.pack(side="left", padx=(0, 12))

        filter_option = ctk.CTkOptionMenu(
            filter_frame,
            values=["All", "Pending", "Completed"],
            width=150,
            height=38
        )
        filter_option.set("Completed" if only_completed else "All")
        filter_option.pack(side="left")

        table_frame = ctk.CTkFrame(self.display, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=22, pady=(5, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background="#FFFFFF", foreground=TEXT,
            fieldbackground="#FFFFFF", rowheight=34, font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading", background="#E8F0EA",
            foreground=TEXT, font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Treeview", background=[("selected", "#DCEADF")],
            foreground=[("selected", TEXT)]
        )

        tree = ttk.Treeview(
                table_frame,
                columns=("ID", "Title", "Deadline", "Priority", "Status"),
                show="headings",
                height=12
            )
        tree.tag_configure("High", foreground="#D9534F")
        tree.tag_configure("Medium", foreground="#C28A25")
        tree.tag_configure("Low", foreground="#4F8A65")

        for col, width in [
            ("ID", 50),
            ("Title", 350),
            ("Deadline", 140),
            ("Priority", 110),
            ("Status", 110)
        ]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w" if col == "Title" else "center")
        tree.pack(fill="both", expand=True)

        # Display tasks based on search and filter
        def update_task_list(*args):
            for item in tree.get_children():
                tree.delete(item)

            search_text = search_var.get().lower().strip()
            selected_filter = filter_option.get()

            for task in load_tasks():
                task_title = task.get("title", "")
                task_status = task.get("status", "pending").lower()

                if search_text not in task_title.lower():
                    continue

                if selected_filter == "Pending" and task_status != "pending":
                    continue

                if selected_filter == "Completed" and task_status != "completed":
                    continue
                
                priority = task.get("priority", "Medium")

                tree.insert(
                    "",
                    "end",
                    values=(
                        task.get("id", ""),
                        task_title,
                        task.get("deadline", ""),
                        priority,
                        task_status.title()
                    ),
                    tags=(priority,)
                )

        search_var.trace_add("write", update_task_list)
        filter_option.configure(command=lambda choice: update_task_list())

        update_task_list()

        actions = ctk.CTkFrame(self.display, fg_color="transparent")
        actions.pack(anchor="w", padx=22, pady=(0, 18))

        ctk.CTkButton(
            actions,
            text="Mark selected complete",
            command=lambda: self.complete_selected(tree),
            fg_color=GREEN_DARK,
            hover_color="#416653"
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions,
            text="Delete selected",
            command=lambda: self.delete_selected(tree),
            fg_color="#C47B69",
            hover_color="#A96252"
        ).pack(side="left")

    def complete_selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select a task", "Please select a task first.")
            return
        task_id = int(tree.item(selected[0], "values")[0])
        tasks = load_tasks()
        for task in tasks:
            if task.get("id") == task_id:
                task["status"] = "completed"
                break
        save_tasks(tasks)
        self.view_tasks(False)

    def delete_selected(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select a task", "Please select a task first.")
            return
        task_id = int(tree.item(selected[0], "values")[0])
        if not messagebox.askyesno("Delete task", "Are you sure you want to delete this task?"):
            return
        tasks = [task for task in load_tasks() if task.get("id") != task_id]
        save_tasks(tasks)
        self.view_tasks(False)
  
    def log_study_time_screen(self):
        self.set_page_title(
            "Log study time",
            "Every focused hour brings you closer to your goals. ♡"
        )
        self.refresh_cards()
        self.clear_display()

        self.section_heading(
            self.display,
            "Your study sessions",
            "Track your learning time and celebrate your consistency."
        )

        # Main layout
        body = ctk.CTkFrame(self.display, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        form_card = ctk.CTkFrame(
            body, fg_color="#F1F6F1", corner_radius=16
        )
        form_card.grid(
            row=0, column=0, sticky="nsew",
            padx=(0, 8), pady=8
        )

        ctk.CTkLabel(
            form_card,
            text="✿  Add a study session",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(18, 5))

        ctk.CTkLabel(
            form_card,
            text="The current date is recorded automatically.",
            text_color=MUTED,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            form_card, text="Study hours",
            text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(5, 5))

        hours_entry = ctk.CTkEntry(
            form_card,
            width=280,
            height=38,
            placeholder_text="e.g. 1.5"
        )
        hours_entry.pack(anchor="w", padx=20, pady=(0, 12))

        ctk.CTkLabel(
            form_card, text="Subject / category",
            text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(0, 5))

        category = ctk.CTkOptionMenu(
            form_card,
            width=280,
            height=38,
            values=[
                "Python", "DSA", "GATE",
                "Computer Networks",
                "Artificial Intelligence",
                "Data Mining", "Project", "Others"
            ],
            fg_color=GREEN_DARK,
            button_color=GREEN_DARK,
            button_hover_color="#416653"
        )
        category.pack(anchor="w", padx=20, pady=(0, 18))

        goal_card = ctk.CTkFrame(
            body, fg_color="#FBF1E9", corner_radius=16
        )
        goal_card.grid(
            row=0, column=1, sticky="nsew",
            padx=(8, 0), pady=8
        )

        ctk.CTkLabel(
            goal_card,
            text="🎯  Your weekly study goal",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=20, pady=(18, 12))

    # Calculate study hours for the last 7 calendar days
        today = datetime.now().date()
        week_start = today - timedelta(days=6)

        weekly_total = 0

        for record in read_study_records():
            try:
                record_date = datetime.strptime(
                    record["Date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                continue

            if week_start <= record_date <= today:
                weekly_total += record["Hours"]

        progress = min(
            weekly_total / WEEKLY_GOAL_HOURS, 1.0
        )

        ctk.CTkLabel(
            goal_card,
            text=f"{weekly_total:.1f} / {WEEKLY_GOAL_HOURS} hours",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color=GREEN_DARK
        ).pack(anchor="w", padx=20, pady=(5, 3))

        goal_bar = ctk.CTkProgressBar(
            goal_card,
            height=13,
            progress_color=GREEN_DARK,
            fg_color="#E5DCD1"
        )
        goal_bar.pack(fill="x", padx=20, pady=12)
        goal_bar.set(progress)

        percentage = int(progress * 100)

        ctk.CTkLabel(
            goal_card,
            text=f"{percentage}% of your weekly goal completed",
            text_color=MUTED,
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=20, pady=(0, 5))

        ctk.CTkLabel(
            goal_card,
            text="Small steps. Consistent progress. ♡",
            text_color=GREEN_DARK,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(5, 12))

        def save():
            try:
                hours = float(hours_entry.get().strip())

                if hours <= 0:
                    raise ValueError

            except ValueError:
                messagebox.showwarning(
                    "Invalid hours",
                    "Please enter a number greater than zero."
                )
                return

            new_file = (
                not STUDY_FILE.exists()
                or STUDY_FILE.stat().st_size == 0
            )

            with STUDY_FILE.open(
                "a", newline="", encoding="utf-8"
            ) as file:
                writer = csv.writer(file)

                if new_file:
                    writer.writerow(["Date", "Category", "Hours"])

                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d"),
                    category.get(),
                    hours
                ])

            messagebox.showinfo(
                "Study session saved",
                "Your study session has been recorded successfully!"
            )

            self.log_study_time_screen()

        ctk.CTkButton(
            form_card,
            text="＋  Save study session",
            width=190,
            height=40,
            corner_radius=10,
            fg_color=GREEN_DARK,
            hover_color="#416653",
            command=save
        ).pack(anchor="w", padx=20, pady=(0, 18))

        recent_card = ctk.CTkFrame(
            body, fg_color="#FAF9F6", corner_radius=16
        )
        recent_card.grid(
            row=1, column=0, columnspan=2,
            sticky="nsew", padx=8, pady=8
        )

        ctk.CTkLabel(
            recent_card,
            text="Recent study sessions",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(15, 3))

        ctk.CTkLabel(
            recent_card,
            text="A quick look at your latest learning activities.",
            font=ctk.CTkFont(size=12),
            text_color=MUTED
        ).pack(anchor="w", padx=18, pady=(0, 10))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Study.Treeview",
            background="#FFFFFF",
            foreground=TEXT,
            fieldbackground="#FFFFFF",
            rowheight=30,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Study.Treeview.Heading",
            background="#E8F0EA",
            foreground=TEXT,
            font=("Segoe UI", 10, "bold")
        )

        table = ttk.Treeview(
            recent_card,
            columns=("Subject", "Date", "Hours"),
            show="headings",
            height=5,
            style="Study.Treeview"
        )

        table.heading("Subject", text="Subject")
        table.heading("Date", text="Date")
        table.heading("Hours", text="Study Hours")

        table.column("Subject", width=350, anchor="w")
        table.column("Date", width=180, anchor="center")
        table.column("Hours", width=150, anchor="center")

        table.pack(
            fill="both", expand=True,
            padx=18, pady=(0, 16)
        )

        records = read_study_records()

        def sort_key(record):
            try:
                return datetime.strptime(
                    record["Date"], "%Y-%m-%d"
                )
            except ValueError:
                return datetime.min

        recent_records = sorted(
            records, key=sort_key, reverse=True
        )[:5]

        if not recent_records:
            table.insert(
                "", "end",
                values=("No study sessions yet", "-", "-")
            )
        else:
            for record in recent_records:
                table.insert(
                    "", "end",
                    values=(
                        record["Category"],
                        record["Date"],
                        f'{record["Hours"]:.1f} hrs'
                    )
                )

    def weekly_analytics_screen(self):
        self.set_page_title(
            "Weekly analytics",
            "See how your study time is distributed by subject."
        )
        self.refresh_cards()
        self.clear_display()
        self.section_heading(
            self.display, "Your last 7 days", "Study hours by subject"
        )

        cutoff = datetime.now() - timedelta(days=7)
        totals = {}
        for record in read_study_records():
            try:
                record_date = datetime.strptime(record["Date"], "%Y-%m-%d")
            except ValueError:
                continue
            if record_date >= cutoff:
                category = record["Category"]
                totals[category] = totals.get(category, 0) + record["Hours"]

        if not totals:
            ctk.CTkLabel(
                self.display, text="No study records found for the last 7 days.",
                text_color=MUTED
            ).pack(pady=40)
            return

        figure = Figure(figsize=(8, 4.2), dpi=100, facecolor="#FFFFFF")
        axis = figure.add_subplot(111)
        axis.set_facecolor("#FFFFFF")
        axis.bar(
            list(totals.keys()), list(totals.values()),
            color=["#A8C7B5", "#F4D7C5", "#C9BCE3", "#E8D99B", "#AFCBD1"]
        )
        axis.set_title("Weekly study hours", color=TEXT, pad=14, fontsize=13, weight="bold")
        axis.set_ylabel("Hours", color=TEXT)
        axis.tick_params(axis="x", labelrotation=15, colors=TEXT)
        axis.tick_params(axis="y", colors=TEXT)
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.2)
        axis.set_axisbelow(True)
        figure.tight_layout()

        chart_holder = ctk.CTkFrame(self.display, fg_color="transparent")
        chart_holder.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        canvas = FigureCanvasTkAgg(figure, master=chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    def habit_tracker_screen(self):
        self.set_page_title(
            "Habit tracker",
            "Build small habits. Create big changes. ♡"
        )
        self.refresh_cards()
        self.clear_display()

        today = datetime.now().strftime("%Y-%m-%d")
        habits = load_habits()

        self.section_heading(
            self.display,
            "Your daily habits",
            "Show up for yourself, one day at a time."
        )

        # Calculate today's progress
        completed = sum(
            1 for habit in habits
            if today in habit.get("completed_dates", [])
        )
        total = len(habits)
        progress = completed / total if total else 0

        # Progress card
        progress_card = ctk.CTkFrame(
            self.display,
            fg_color="#F1F6F1",
            corner_radius=16
        )
        progress_card.pack(fill="x", padx=22, pady=12)

        ctk.CTkLabel(
            progress_card,
            text="Today's progress",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(15, 5))

        ctk.CTkLabel(
            progress_card,
            text=f"{completed} of {total} habits completed",
            text_color=MUTED
        ).pack(anchor="w", padx=18)

        progress_bar = ctk.CTkProgressBar(
            progress_card,
            progress_color=GREEN_DARK,
            fg_color="#DCE7DE",
            height=12
        )
        progress_bar.pack(fill="x", padx=18, pady=12)
        progress_bar.set(progress)

        # Add habit form
        form = ctk.CTkFrame(
            self.display,
            fg_color="#FBF1E9",
            corner_radius=16
        )
        form.pack(fill="x", padx=22, pady=10)

        ctk.CTkLabel(
            form,
            text="＋ Add a new habit",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(14, 7))

        entry_row = ctk.CTkFrame(form, fg_color="transparent")
        entry_row.pack(fill="x", padx=18, pady=(0, 15))

        habit_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text="e.g. Practice DSA for 30 minutes",
            height=38,
            width=360
        )
        habit_entry.pack(side="left", padx=(0, 10))

        def add_habit():
            name = habit_entry.get().strip()

            if not name:
                messagebox.showwarning(
                    "Missing habit",
                    "Please enter a habit name."
                )
                return

            if any(
                h.get("name", "").casefold() == name.casefold()
                for h in load_habits()
            ):
                messagebox.showwarning(
                    "Already exists",
                    "This habit is already in your list."
                )
                return

            current_habits = load_habits()
            current_habits.append({
                "name": name,
                "completed_dates": []
            })
            save_habits(current_habits)
            self.habit_tracker_screen()

        ctk.CTkButton(
            entry_row,
            text="Add habit",
            height=38,
            fg_color=GREEN_DARK,
            hover_color="#416653",
            command=add_habit
        ).pack(side="left")

        # Habit list
        list_card = ctk.CTkFrame(
            self.display,
            fg_color="#FAF9F6",
            corner_radius=16
        )
        list_card.pack(
            fill="both", expand=True,
            padx=22, pady=(5, 18)
        )

        ctk.CTkLabel(
            list_card,
            text="Your habits",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(15, 10))

        if not habits:
            ctk.CTkLabel(
                list_card,
                text="No habits added yet. Start with one small goal! ✿",
                text_color=MUTED
            ).pack(anchor="w", padx=18, pady=15)
            return

        for habit in habits:
            name = habit.get("name", "Unnamed habit")
            completed_dates = habit.get("completed_dates", [])

            row = ctk.CTkFrame(
                list_card,
                fg_color="#FFFFFF",
                corner_radius=10
            )
            row.pack(fill="x", padx=16, pady=5)

            checked = tk.BooleanVar(
                value=today in completed_dates
            )

            def toggle_habit(
                habit_name=name,
                variable=checked
            ):
                current_habits = load_habits()

                for item in current_habits:
                    if item.get("name") == habit_name:
                        dates = item.setdefault(
                            "completed_dates", []
                        )

                        if variable.get():
                            if today not in dates:
                                dates.append(today)
                        else:
                            if today in dates:
                                dates.remove(today)

                        break

                save_habits(current_habits)
                self.habit_tracker_screen()

            ctk.CTkCheckBox(
                row,
                text=name,
                variable=checked,
                command=toggle_habit,
                text_color=TEXT,
                fg_color=GREEN_DARK,
                hover_color="#416653",
                font=ctk.CTkFont(size=14)
            ).pack(side="left", padx=16, pady=13)
            
            weekly_count, streak = get_habit_stats(completed_dates)

            ctk.CTkLabel(
                row,
                text=f"📅 {weekly_count}/7 days   🔥 {streak} day streak",
                text_color=MUTED,
                font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=10)

            def delete_habit(habit_name=name):
                if not messagebox.askyesno(
                    "Delete habit",
                    f"Remove '{habit_name}' from your habits?"
                ):
                    return

                current_habits = [
                    item for item in load_habits()
                    if item.get("name") != habit_name
                ]
                save_habits(current_habits)
                self.habit_tracker_screen()

            ctk.CTkButton(
                row,
                text="Delete",
                width=75,
                height=30,
                fg_color="#EEDDD6",
                hover_color="#E4C7BB",
                text_color="#8C5548",
                command=delete_habit
            ).pack(side="right", padx=12, pady=8)

    
    def productivity_insights_screen(self):
        self.set_page_title(
            "Productivity insights",
            "Understand your progress and celebrate your consistency. ♡"
        )
        self.refresh_cards()
        self.clear_display()

        self.section_heading(
            self.display,
            "Your productivity overview",
            "A summary of your tasks, study time and habits."
        )

        # Task statistics
        tasks = load_tasks()
        completed_tasks = sum(
            1 for task in tasks
            if task.get("status") == "completed"
        )

        task_percentage = (
            completed_tasks / len(tasks) * 100
            if tasks else 0
        )

        # Study statistics for the current week
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

        weekly_hours = 0
        subject_hours = {}

        for record in read_study_records():
            try:
                record_date = datetime.strptime(
                    record["Date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                continue

            if week_start <= record_date <= today:
                weekly_hours += record["Hours"]
                subject = record["Category"]
                subject_hours[subject] = (
                    subject_hours.get(subject, 0)
                    + record["Hours"]
                )

        best_subject = (
            max(subject_hours, key=subject_hours.get)
            if subject_hours else "No data yet"
        )

        study_percentage = min(
            weekly_hours / WEEKLY_GOAL_HOURS * 100,
            100
        )

        # Habit statistics
        habits = load_habits()

        weekly_habit_completions = 0
        best_streak = 0

        for habit in habits:
            completed_dates = habit.get("completed_dates", [])

            weekly_count, streak = get_habit_stats(
                completed_dates
            )

            weekly_habit_completions += weekly_count
            best_streak = max(best_streak, streak)

        # Statistics cards
        cards_frame = ctk.CTkFrame(
            self.display,
            fg_color="transparent"
        )
        cards_frame.pack(
            fill="x", padx=15, pady=10
        )

        cards_frame.grid_columnconfigure(
            (0, 1), weight=1
        )

        insights = [
            (
                "✓  TASK COMPLETION",
                f"{task_percentage:.0f}%",
                f"{completed_tasks} of {len(tasks)} tasks",
                "#E8F0EA"
            ),
            (
                "◷  WEEKLY STUDY",
                f"{weekly_hours:.1f} hrs",
                f"{study_percentage:.0f}% of weekly goal",
                "#FBF1E9"
            ),
            (
                "♡  HABIT COMPLETIONS",
                str(weekly_habit_completions),
                "This week",
                "#E4DDF2"
            ),
            (
                "🔥  BEST ACTIVE STREAK",
                f"{best_streak} days",
                "Across all habits",
                "#F1F6F1"
            )
        ]

        for index, (heading, value, subtitle, color) in enumerate(insights):
            card = ctk.CTkFrame(
                cards_frame,
                fg_color=color,
                corner_radius=15,
                height=125
            )
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=7,
                pady=7
            )
            card.grid_propagate(False)

            ctk.CTkLabel(
                card,
                text=heading,
                text_color=TEXT,
                font=ctk.CTkFont(
                    size=12, weight="bold"
                )
            ).pack(anchor="w", padx=16, pady=(15, 5))

            ctk.CTkLabel(
                card,
                text=value,
                text_color=GREEN_DARK,
                font=ctk.CTkFont(
                    size=24, weight="bold"
                )
            ).pack(anchor="w", padx=16)

            ctk.CTkLabel(
                card,
                text=subtitle,
                text_color=MUTED,
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", padx=16)

        # Best subject section
        subject_card = ctk.CTkFrame(
            self.display,
            fg_color="#FAF9F6",
            corner_radius=15
        )
        subject_card.pack(
            fill="x", padx=22, pady=12
        )

        ctk.CTkLabel(
            subject_card,
            text="✧  Your most studied subject",
            text_color=TEXT,
            font=ctk.CTkFont(
                size=16, weight="bold"
            )
        ).pack(anchor="w", padx=18, pady=(15, 5))

        ctk.CTkLabel(
            subject_card,
            text=best_subject,
            text_color=GREEN_DARK,
            font=ctk.CTkFont(
                size=21, weight="bold"
            )
        ).pack(anchor="w", padx=18, pady=(0, 15))

        # Weekly study goal progress
        goal_card = ctk.CTkFrame(
            self.display,
            fg_color="#F1F6F1",
            corner_radius=15
        )
        goal_card.pack(
            fill="x", padx=22, pady=(0, 15)
        )

        ctk.CTkLabel(
            goal_card,
            text="Your weekly study goal",
            text_color=TEXT,
            font=ctk.CTkFont(
                size=16, weight="bold"
            )
        ).pack(anchor="w", padx=18, pady=(15, 5))

        goal_bar = ctk.CTkProgressBar(
            goal_card,
            progress_color=GREEN_DARK,
            fg_color="#DCE7DE",
            height=12
        )
        goal_bar.pack(
            fill="x", padx=18, pady=10
        )
        goal_bar.set(study_percentage / 100)

        ctk.CTkLabel(
            goal_card,
            text=(
                f"{weekly_hours:.1f} of "
                f"{WEEKLY_GOAL_HOURS} hours completed"
            ),
            text_color=MUTED
        ).pack(anchor="w", padx=18, pady=(0, 15))


if __name__ == "__main__":
    app = StudyPlannerApp()
    app.mainloop()