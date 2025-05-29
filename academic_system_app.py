# Python GUI for Academic Staff Using Tkinter and mysql-connector-python
import tkinter as tk
from tkinter import ttk, messagebox, Menu, filedialog, scrolledtext
from tkinter import *

import mysql.connector

from PIL import Image, ImageTk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from matplotlib.cm import get_cmap
from matplotlib.colors import to_hex

import numpy as np

import shutil

import os

from datetime import datetime, timedelta

import subprocess

import sys

# Main app class

class AcademicSystemApp(tk.Tk):
    def __init__(self, conn, role, username, password, master):
        super().__init__()
        self.master = master
        self.iconbitmap(r"D:/School_GUI/icon.ico")
        self.conn = conn
        self.cursor = conn.cursor()
        self.role = role
        self.username = username
        self.password = password

        self.title("Academic Staff Panel")
        self.geometry("900x600")
        self.state('zoomed')
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        taskbar_height = 40  # adjust if needed

        self.create_menu()

        if self.role == "teacher":
            self.open_teacher_id_window(self.conn)
        elif self.role == "coordinator":
            self.create_coordinator_tab()
        elif self.role == "admin":
            self.create_admin_tab()


    # Menu Ribbon
    def create_menu(self):
        menubar = Menu(self)
        profile_menu = Menu(menubar, tearoff=0)
        profile_menu.add_command(label="Profile", command=self.show_profile)
        profile_menu.add_command(label="Log out", command=self.logout)

        menubar.add_cascade(label="Profile", menu=profile_menu)
        self.config(menu=menubar)

    def show_profile(self):
        profile_window = tk.Toplevel(self)
        profile_window.title("User Profile")
        profile_window.geometry("370x450")
        profile_window.resizable(False, False)

        tk.Label(profile_window, text="User Profile", font=("Helvetica", 18, "bold") ).pack(pady=10)

        info_frame = tk.Frame(profile_window, padx=20, pady=10)
        info_frame.pack(fill="x")

        def add_info(label_text, value):
            row = tk.Frame(info_frame)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, font=("Arial", 12, "bold"), width=15, anchor='w').pack(side=tk.LEFT)
            tk.Label(row, text=value, font=("Arial", 12), anchor='w').pack(side=tk.LEFT)

        add_info("Username:", self.conn.user)

        # Add TeacherID and ClassName for teachers
        if self.role.lower() == 'teacher':
            teacher_id = getattr(self, 'teacher_id', 'N/A')
            class_name = getattr(self, 'class_name', 'N/A')
            add_info("Teacher ID:", teacher_id)
            add_info("Class Name:", class_name)

        add_info("Password:", self.password)
        add_info("Role:", self.role) 

    def logout(self):
        try:
            self.conn.close()
        except:
            pass  # In case it's already closed
        self.destroy()       # Close AcademicSystemApp
        self.master.destroy()  # Close the hidden login window too

        # Restart the whole app (session reset)
        subprocess.Popen([sys.executable, "main.py"])
        sys.exit()


    # Teacher Filter
    def open_class_filter_window(self, connection, teacher_id):
        def submit_class_name():
            class_name = entry.get().strip()
            if not checkbox_var.get():
                messagebox.showwarning("Input Required", "Please confirm by checking the box.")
                return
            if not class_name:
                messagebox.showwarning("Invalid", "Class name cannot be empty.")
                return

            cursor = connection.cursor()
            cursor.callproc('VerifyTeacherClassPair', (teacher_id, class_name))
            data = []
            for result in cursor.stored_results():
                data = result.fetchall()

            if not data or data[0][0] == 'NOT FOUND':
                messagebox.showerror("Not Found", f"Class '{class_name}' is not assigned to Teacher ID {teacher_id}")
            else:
                # Expected to return: ClassName, ClassID, SubjectID, SubjectName
                class_name_db = data[0][0]
                class_id = data[0][1]
                subject_id = data[0][2]
                subject_name = data[0][3]

                self.class_name = class_name_db  # Store class name
                top.destroy()
                self.on_valid_info(teacher_id, class_name_db, class_id, subject_id, subject_name)

        top = tk.Toplevel()
        top.title("Enter Class Name")
        top.geometry("400x200")

        tk.Label(top, text="Enter your Class Name:").pack(pady=5)
        entry = tk.Entry(top)
        entry.pack(pady=5)

        checkbox_var = tk.BooleanVar()
        tk.Checkbutton(top, text="I confirm this is my class", variable=checkbox_var).pack()

        tk.Button(top, text="Submit", command=submit_class_name).pack(pady=10)

        top.grab_set()
        entry.focus()

    def open_teacher_id_window(self, connection):
        def submit_teacher_id():
            teacher_id = entry.get().strip()
            if not checkbox_var.get():
                messagebox.showwarning("Input Required", "Please confirm by checking the box.")
                return
            if not teacher_id.isdigit():
                messagebox.showwarning("Invalid", "Teacher ID must be a number.")
                return

            cursor = connection.cursor()
            cursor.callproc('CheckClass', (int(teacher_id),))
            for result in cursor.stored_results():
                data = result.fetchall()

            if not data:
                messagebox.showerror("Error", "Unexpected error occurred.")
            elif data[0][0] == 'NOT FOUND':
                messagebox.showerror("Not Found", f"No class assigned to Teacher ID {teacher_id}")
            elif data[0][0] == 'EMPTY SCHEDULE':
                messagebox.showinfo("Notice", "The schedule is currently empty.\nProceeding without verification.")
                top.destroy()
                self.teacher_id = int(teacher_id)  # Store teacher ID
                self.open_class_filter_window(connection, int(teacher_id))
            else:
                self.teacher_id = int(teacher_id)  # Store teacher ID
                top.destroy()
                self.open_class_filter_window(connection, int(teacher_id))

        top = tk.Toplevel()
        top.title("Enter Your Teacher ID")

        top.geometry("400x200")

        tk.Label(top, text="Enter your Teacher ID:").pack(pady=5)
        entry = tk.Entry(top)
        entry.pack(pady=5)

        checkbox_var = tk.BooleanVar()
        tk.Checkbutton(top, text="I confirm this is my ID", variable=checkbox_var).pack()

        tk.Button(top, text="Submit", command=submit_teacher_id).pack(pady=10)

        top.grab_set()
        entry.focus()

    def on_valid_info(self, teacher_id, class_name, class_id, subject_id, subject_name):
        self.teacher_id = teacher_id
        self.class_name = class_name
        self.class_id = class_id
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.create_teacher_tab(teacher_id, class_name, class_id, subject_id, subject_name)

    # Teacher Tab
    def create_teacher_tab(self, teacher_id, class_name, class_id, subject_id, subject_name):
        class_name = self.class_name
        class_id = self.class_id
        teacher_id = self.teacher_id
        subject_id = self.subject_id
        subject_name = self.subject_name

        self.teacher_frame = tk.Frame(self)
        self.teacher_frame.pack(fill="both", expand=True)

        label = tk.Label(self.teacher_frame, text=f"{class_name} Management", font=("Helvetica", 16))
        label.pack(pady=20)

        check_attendance_button = tk.Button(
            self.teacher_frame, 
            text="Check Attendance", 
            command=lambda: self.open_attendance_window(class_name)
        )
        check_attendance_button.pack(pady=10)

        insert_grade_button = tk.Button(
            self.teacher_frame, 
            text="Insert Grade", 
            command=lambda: self.insert_grade(self.class_name, self.subject_id, self.subject_name, self.conn)
        )
        insert_grade_button.pack(pady=10)

        request_priv_button = tk.Button(
            self.teacher_frame,
            text="Request Privilege",
            command=self.open_privilege_request_editor
        )
        request_priv_button.pack(pady=10)

        review_load_button = tk.Button(
            self.teacher_frame,
            text="Review Teacher Load",
            command=lambda: self.review_latest_pdf(os.path.join(os.getcwd(), "TeacherLoadSummary"), "Teacher Load Summary")
        )
        review_load_button.pack(pady=10)

    # Check Attendance
    def open_attendance_window(self, class_name):
        attendance_window = tk.Toplevel(self)
        attendance_window.title(f"{class_name} Attendance")
        attendance_window.geometry("1000x700")

        self.cursor.callproc('GetClassRosterByName', (class_name,))
        students = []
        for result in self.cursor.stored_results():
            students = result.fetchall()

        header = tk.Label(attendance_window, text=f"{class_name} - Class Roster", font=("Helvetica", 14))
        header.pack(pady=10)

        # Check Buttons Area
        canvas = tk.Canvas(attendance_window)
        frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(attendance_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=frame, anchor="nw")

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        attendance_vars = {}

        for student in students:
            sid, name, bdate = student

            student_frame = tk.Frame(frame)
            student_frame.pack(fill="x", pady=5)

            label = tk.Label(student_frame, text=f"{sid} - {name} ({bdate})", width=40, anchor="w").pack(side="left", padx=5)
            label.pack(side="left", padx=5)

            absent_var = tk.IntVar()
            attend_var = tk.IntVar()

            tk.Checkbutton(student_frame, text="Absented", variable=absent_var,
                        command=lambda a=attend_var: a.set(0)).pack(side="left")
            tk.Checkbutton(student_frame, text="Attended", variable=attend_var,
                        command=lambda a=absent_var: a.set(0)).pack(side="left")

            attendance_vars[sid] = {"absent": absent_var, "attend": attend_var}

            # view_label = tk.Label(attendance_window, text="Current Attendance Records", font=("Helvetica", 12, "underline"))
            # view_label.pack(pady=10)

            attendance_table = tk.Frame(attendance_window)
            attendance_table.pack(pady=5, fill="both", expand=False)

        def save_attendance():
            try:
                for student in students:
                    sid, name, bdate = student
                    attend_checked = attendance_vars[sid]["attend"].get()
                    absent_checked = attendance_vars[sid]["absent"].get()

                    # Convert checkbox state to status
                    if attend_checked and not absent_checked:
                        present = 1
                    elif absent_checked and not attend_checked:
                        present = 0
                    else:
                        messagebox.showwarning("Invalid Selection", f"Please select only one option for {name}.")
                        return

                    # Call stored procedure instead of raw SQL
                    self.cursor.callproc('SaveOrUpdateAttendance', (sid, self.class_id, present))

                self.conn.commit()
                messagebox.showinfo("Saved", "Attendance successfully saved.")


            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Failed to save attendance:\n{e}")

        save_button = tk.Button(attendance_window, text="Save Attendance", command=save_attendance)
        save_button.pack(pady=10)

        return_button = tk.Button(attendance_window, text="Return", command=attendance_window.destroy)
        return_button.place(x=10, y=10)

    # Insert Grade
    def insert_grade(self, class_name, subject_id, subject_name, connection):
        top = tk.Toplevel(self)
        top.title("Insert Grades")
        top.geometry("800x500")

        label = tk.Label(top, text=f"Insert Grades for {class_name} - {subject_name}", font=("Helvetica", 14))
        label.pack(pady=10)

        grades_dict = {}

        columns = ("StudentID", "StudentName", "SubjectID", "SubjectName", "Score")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(expand=True, fill="both", padx=10, pady=10)

        # Fetch students and populate the table
        try:
            cursor = connection.cursor()
            cursor.callproc("GetClassRosterByName", (class_name,))
            for result in cursor.stored_results():
                students = result.fetchall()

            for student in students:
                student_id, student_name, _ = student
                tree.insert("", "end", iid=str(student_id), values=(
                    student_id, student_name, subject_id, subject_name, ""
                ))

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            top.destroy()
            return

        # Function to handle double-click and input grade
        def on_double_click(event):
            item_id = tree.identify_row(event.y)
            if not item_id:
                return

            values = tree.item(item_id, "values")
            student_id = values[0]
            student_name = values[1]

            popup = tk.Toplevel(top)
            popup.title(f"Enter Grade for {student_name}")
            popup.geometry("250x120")


            tk.Label(popup, text=f"Grade for {student_name}:").pack(pady=5)
            entry = tk.Entry(popup)
            entry.pack(pady=5)
            entry.focus()   


            def save_grade():
                grade = entry.get().strip()

                if not grade:
                    messagebox.showwarning("Invalid", "Grade cannot be empty")
                    return
                try:
                    float_grade = float(grade)
                except ValueError:
                    messagebox.showwarning("Invalid", "Grade must be a number")
                    return
                float_grade = float(grade)
                grades_dict[student_id] = float_grade
                tree.set(item_id, "Score", float_grade)
                popup.destroy()

            tk.Button(popup, text="Save", command=save_grade).pack(pady=5)

        # Bind the handler ONCE
        tree.bind("<Double-1>", on_double_click)

        # Save all grades
        def save_grades():
            cursor = connection.cursor()
            inserted = 0

            for student_id, grade in grades_dict.items():
                try:
                    cursor.execute("""
                        INSERT INTO Grades (StudentID, SubjectID, Score)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE Score = VALUES(Score)       
                    """, (student_id, subject_id, grade))
                    inserted += 1
                except Exception as e:
                    messagebox.showerror("Insert Error", f"Student {student_id}: {e}")

            connection.commit()
            messagebox.showinfo("Saved", f"{inserted} grade(s) saved successfully.")

        # Buttons
        button_frame = tk.Frame(top)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Save Grades", command=save_grades).pack(side="left", padx=10)
        tk.Button(button_frame, text="Return", command=top.destroy).pack(side="left", padx=10)


    # Coordinator Tab
    def create_coordinator_tab(self):
        self.coordinator_frame = tk.Frame(self)
        self.coordinator_frame.pack(fill="both", expand=True)

        label = tk.Label(self.coordinator_frame, text="Coordinator Panel", font=("Helvetica", 16))
        label.pack(pady=20)

        insert_update_student_button = tk.Button(
            self.coordinator_frame, 
            text="Adjust Student Info", 
            command=self.open_student_info_window  # Placeholder: implement later
        )
        insert_update_student_button.pack(pady=10)

        scorecard_button = tk.Button(
            self.coordinator_frame,
            text="Generate Scorecard Dashboard",
            command=self.open_scorecard_window
        )
        scorecard_button.pack(pady=10)

        class_perf_button = tk.Button(
            self.coordinator_frame,
            text="Generate Class Performance Dashboard",
            command=self.open_class_performance_window
        )
        class_perf_button.pack(pady=10)

        teacher_summary_button = tk.Button(
            self.coordinator_frame, 
            text="Create Teacher Load Summary", 
            command=self.open_teacher_load_summary # Placeholder: implement later
        )
        teacher_summary_button.pack(pady=10)

        request_priv_button = tk.Button(
            self.coordinator_frame,
            text="Request Privilege",
            command=self.open_privilege_request_editor
        )
        request_priv_button.pack(pady=10)

    # Adjust Student Info
    def open_student_info_window(self):
        self.student_info_window = tk.Toplevel(self)
        self.student_info_window.title("Insert/Update Student Info")
        self.student_info_window.geometry("1100x700")

        # Student Treeview
        self.student_tree = ttk.Treeview(self.student_info_window, columns=("StudentID", "StudentName", "BirthDate", "ClassID", "Address"), show="headings")
        for col in ("StudentID", "StudentName", "BirthDate", "ClassID", "Address"):
            self.student_tree.heading(col, text=col)
            self.student_tree.column(col, width=150)
        self.student_tree.pack(padx=10, pady=10, fill="both", expand=True)

        # Button Panel
        button_frame = tk.Frame(self.student_info_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Insert", command=self.insert_student_popup).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Update", command=self.update_student_popup).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Delete", command=self.delete_student_popup).grid(row=0, column=3, padx=10)
        tk.Button(button_frame, text="Return", command=self.close_student_info_window).grid(row=0, column=2, padx=10)

        # Persistent Class Info Window
        self.open_class_info_window()

        # Load students
        self.fetch_students()

    def close_student_info_window(self):
        self.student_info_window.destroy()
        if self.class_info_window and self.class_info_window.winfo_exists():
            self.class_info_window.destroy()

    def open_class_info_window(self):
        self.class_info_window = tk.Toplevel(self)
        self.class_info_window.title("Class Info")
        self.class_info_window.geometry("400x200+0+100")  # Dock left-ish
        self.class_info_window.attributes("-topmost", True)

        class_tree = ttk.Treeview(self.class_info_window, columns=("ClassID", "ClassName"), show="headings")
        class_tree.heading("ClassID", text="ClassID")
        class_tree.heading("ClassName", text="ClassName")
        class_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Load class data
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Classes")
            rows = cursor.fetchall()
            for row in rows:
                class_tree.insert('', 'end', values=row)
            cursor.close()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def fetch_students(self):
        try:
            for row in self.student_tree.get_children():
                self.student_tree.delete(row)

            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Students")
            rows = cursor.fetchall()
            for row in rows:
                self.student_tree.insert('', 'end', values=row)
            cursor.close()
        except Exception as e:
            messagebox.showerror("Error Fetching Students", str(e))

    def insert_student_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Insert New Student")
        popup.geometry("400x300")

        fields = ["StudentID", "StudentName", "BirthDate (YYYY-MM-DD)", "ClassID", "Address"]
        entries = {}

        for idx, field in enumerate(fields):
            tk.Label(popup, text=field).grid(row=idx, column=0, padx=10, pady=5)
            entry = tk.Entry(popup, width=30)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entries[field] = entry

        def submit():
            try:
                cursor = self.conn.cursor()
                cursor.callproc("InsertStudentInfo", (
                    entries["StudentID"].get(),
                    entries["StudentName"].get(),
                    entries["BirthDate (YYYY-MM-DD)"].get(),
                    entries["ClassID"].get(),
                    entries["Address"].get()
                ))
                self.conn.commit()
                cursor.close()
                popup.destroy()
                self.fetch_students()
            except Exception as e:
                messagebox.showerror("Insert Error", str(e))

        tk.Button(popup, text="Submit", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def update_student_popup(self):
        # Temporary placeholder function
        # messagebox.showinfo("Update", "Update Student popup - To be implemented")
        selected_item = self.student_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a student to update.")
            return

        values = self.student_tree.item(selected_item, 'values')
        popup = tk.Toplevel(self)
        popup.title("Update Student Info")
        popup.geometry("400x300")

        fields = ["StudentName", "BirthDate (YYYY-MM-DD)", "ClassID", "Address"]
        entries = {}

        for idx, field in enumerate(fields):
            tk.Label(popup, text=field).grid(row=idx, column=0, padx=10, pady=5)
            entry = tk.Entry(popup, width=30)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entry.insert(0, values[idx + 1])  # Skip StudentID
            entries[field] = entry

        def submit():
            try:
                cursor = self.conn.cursor()
                cursor.callproc("UpdateStudentInfo", (
                    values[0],  # StudentID
                    entries["StudentName"].get(),
                    entries["BirthDate (YYYY-MM-DD)"].get(),
                    entries["ClassID"].get(),
                    entries["Address"].get()
                ))

                self.conn.commit()
                cursor.close()
                popup.destroy()
                self.fetch_students()
            except Exception as e:
                messagebox.showerror("Update Error", str(e))

        tk.Button(popup, text="Submit", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def delete_student_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Delete Student")
        popup.geometry("300x150")

        tk.Label(popup, text="Enter StudentID to delete:").pack(pady=10)
        id_entry = tk.Entry(popup, width=30)
        id_entry.pack(pady=5)

        def submit_deletion():
            student_id = id_entry.get()
            if not student_id:
                messagebox.showwarning("Input Error", "Please enter a StudentID.")
                return
            try:
                cursor = self.conn.cursor()
                cursor.callproc("DeleteStudent", (student_id,))

                self.conn.commit()
                cursor.close()
                popup.destroy()
                self.fetch_students()
                messagebox.showinfo("Deleted", f"Student with ID {student_id} deleted.")
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))

        tk.Button(popup, text="Save", command=submit_deletion).pack(pady=10)

    # Scorecard Dashboard
    def open_scorecard_window(self):
        win = tk.Toplevel(self.master)
        win.title("Scorecard")
        win.state('zoomed')

        main_frame = tk.Frame(win)
        main_frame.pack(fill="both", expand=True)

        # Center - Chart + Right Metrics
        center_panel = tk.Frame(main_frame)
        center_panel.pack(side="left", fill="both", expand=True)

        # Tabs per subject
        notebook = ttk.Notebook(center_panel)
        notebook.pack(fill="both", expand=True)

        self.scorecard_notebook = notebook

        # Load Subjects
        cursor = self.conn.cursor()
        cursor.execute("SELECT SubjectID, SubjectName FROM Subjects")
        subjects = cursor.fetchall()
        colors = self.assign_colors([sub[1] for sub in subjects])
        cursor.close()

        self.scorecard_tabs = {}

        for subject_id, subject_name in subjects:
            tab_frame = tk.Frame(notebook)
            notebook.add(tab_frame, text=subject_name)

            # Split: Left = Histogram, Right = Metrics
            chart_container = tk.Frame(tab_frame)
            chart_container.pack(fill="both", expand=True)

            # Chart Frame
            chart_frame = tk.Frame(chart_container)
            chart_frame.pack(side="left", fill="both", expand=True)

            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)

            # Scores for this subject
            cursor = self.conn.cursor()
            cursor.execute("SELECT Score FROM Grades WHERE SubjectID = %s", (subject_id,))
            scores = [row[0] for row in cursor.fetchall()]
            cursor.close()

            if scores:
                ax.hist(scores, bins=10, color=colors[subject_name], edgecolor='black', linewidth=1.0)
                ax.set_title(f"{subject_name} Score Distribution")
                ax.set_xlabel("Score")
                ax.set_ylabel("Number of Students")
                ax.grid(True)
            else:
                ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            canvas.get_tk_widget().bind("<Double-Button-1>", lambda event, sn=subject_name: self.restore_original_histogram(sn))

            # Metrics Frame
            metric_frame = tk.Frame(chart_container, width=200, padx=20)
            metric_frame.pack(side="right", fill="y")

            tk.Label(metric_frame, text="Score Metrics", font=("Arial", 12, "bold")).pack(pady=10)

            try:
                cursor = self.conn.cursor()
                cursor.callproc("GetScoreStats", (subject_id,))
                for result in cursor.stored_results():
                    stats = result.fetchone()
                cursor.close()

                metric_labels = [
                    f"Average: {stats[1]}",
                    f"Median: {stats[2]}",
                    f"Mode: {stats[3]}",
                    f"Std Dev: {stats[4]}"
                ]

                for line in metric_labels:
                    tk.Label(metric_frame, text=line, font=("Arial", 10)).pack(pady=5)
            except Exception as e:
                tk.Label(metric_frame, text=f"Error loading metrics: {str(e)}", fg="red").pack()

            self.scorecard_tabs[subject_name] = {
                "fig": fig,
                "canvas": canvas,
                "ax": ax,
                "scores": scores,
                "subject_id": subject_id,
                "color": colors[subject_name]
            }

        # Bottom buttons
        return_button = tk.Button(win, text="Return", command=win.destroy)
        return_button.pack(side="bottom", pady=10)

        export_button = tk.Button(win, text="Export to PDF",
            command=lambda: self.export_to_pdf(self.scorecard_tabs[notebook.tab(notebook.select(), 'text')]['fig'], "scorecard"))
        export_button.pack(side="bottom", pady=5)

        win.lift()
        win.focus_force()

    def open_class_performance_window(self):
        win = tk.Toplevel()
        win.title("Class Performance")
        win.state('zoomed')

        #Layout Frames
        top_frame = tk.Frame(win)
        top_frame.pack(side="top", fill="x", pady=10)

        chart_frame = tk.Frame(win)
        chart_frame.pack(fill="both", expand=True)

        bottom_frame = tk.Frame(win)
        bottom_frame.pack(side="bottom", pady=10)

        #Class Name Entry
        tk.Label(top_frame, text="Enter Class Name:").pack(side="left", padx=10)
        class_entry = tk.Entry(top_frame)
        class_entry.pack(side="left", padx=5)

        #Buttons
        return_button = tk.Button(bottom_frame, text="Return", command=win.destroy)
        return_button.pack(side="left", pady=10)

        export_button = tk.Button(bottom_frame, text="Export to PDF", command=lambda: self.export_to_pdf(self.current_class_fig, f"{class_entry.get().strip()}_class_performance"))
        export_button.pack(side="left", padx=10)

        generate_button = tk.Button(top_frame, text="Generate", command=lambda: generate_chart(class_entry.get()))
        generate_button.pack(side="left", padx=10)

        fig = Figure(figsize=(10,6))
        ax = fig.add_subplot(111)

        def generate_chart(class_name):
            ax.clear()
            if not class_name.strip():
                messagebox.showwarning("Missing Input", "Please enter a class name.")
                return

            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT SubjectName FROM Subjects")
                subjects = [row[0] for row in cursor.fetchall()]
                colors = self.assign_colors(subjects)

                cursor.execute("SELECT ClassID FROM Classes WHERE ClassName = %s", (class_name,))
                row = cursor.fetchone()
                if not row:
                    messagebox.showerror("Invalid Class", f"No class named '{class_name}' found.")
                    return
                class_id = row[0]

                has_data = False
                for subject in subjects:
                    cursor.execute("""
                        SELECT g.Score
                        FROM Grades g
                        JOIN Students s ON g.StudentID = s.StudentID
                        JOIN Subjects sb ON g.SubjectID = sb.SubjectID
                        WHERE s.ClassID = %s AND sb.SubjectName = %s
                    """, (class_id, subject))
                    scores = [r[0] for r in cursor.fetchall()]
                    if scores:
                        has_data = True
                        ax.hist(scores, bins=10, alpha=0.7, label=subject,
                                color=colors[subject], edgecolor='black', linewidth=1.0, histtype='bar' )

                cursor.close()

                if not has_data:
                    ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

                win.update()

                ax.set_title(f"Score Distribution - Class {class_name}")
                ax.set_xlabel("Score")
                ax.set_ylabel("Number of Students")
                ax.legend()
                fig.tight_layout()

                self.current_class_fig = fig

                # Clear previous canvas if exists
                if hasattr(self, 'current_canvas') and self.current_canvas:
                    self.current_canvas.get_tk_widget().destroy()

                # Draw new canvas
                canvas = FigureCanvasTkAgg(fig, master=chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
                self.current_canvas = canvas

                canvas.get_tk_widget().focus_force()
                win.lift()
                win.focus_force()
                win.update_idletasks()

            except Exception as e:
                messagebox.showerror("Error", str(e))

        win.after(100, lambda: generate_chart)

    # Teacher Load Summary
    def open_teacher_load_summary(self):
        # Create fullscreen window with taskbar and titlebar visible
        top = tk.Toplevel(self.master)
        top.title("Teacher Load Summary")
        top.state('zoomed')

        # Create the main layout frame
        main_frame = tk.Frame(top)
        main_frame.pack(fill="both", expand=True)

        # Define layout proportions
        left_frame = tk.Frame(main_frame, width=int(top.winfo_screenwidth() * 0.2))
        center_frame = tk.Frame(main_frame, width=int(top.winfo_screenwidth() * 0.6))
        right_frame = tk.Frame(main_frame, width=int(top.winfo_screenwidth() * 0.2))

        left_frame.pack(side="left", fill="both", expand=True)
        center_frame.pack(side="left", fill="both", expand=True)
        right_frame.pack(side="right", fill="both", expand=True)

        for frame in (left_frame, center_frame, right_frame):
            frame.pack_propagate(False)  # Prevent shrinking to widget size
            frame.pack(side="left", fill="both", expand=True)

        # ----- Teacher View (Left Frame) -----
        tk.Label(left_frame, text="Teacher List", font=("Helvetica", 14)).pack(pady=10)
        teacher_columns = ("TeacherID", "TeacherName")
        teacher_tree_frame = tk.Frame(left_frame)
        teacher_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        teacher_tree_scrollbar_y = tk.Scrollbar(teacher_tree_frame)
        teacher_tree_scrollbar_y.pack(side="right", fill="y")

        teacher_tree = ttk.Treeview(teacher_tree_frame, columns=teacher_columns, show="headings", yscrollcommand=teacher_tree_scrollbar_y.set)
        for col in teacher_columns:
            teacher_tree.heading(col, text=col)
            teacher_tree.column(col, width=100, anchor="center")
        teacher_tree.pack(fill="both", expand=True, padx=5, pady=5)

        teacher_tree_scrollbar_y.config(command=teacher_tree.yview)

        # Fetch teacher data
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT TeacherID, TeacherName FROM Teachers")
            for tid, tname in cursor.fetchall():
                teacher_tree.insert("", "end", values=(tid, tname))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        # ----- Schedule View (Center Frame) -----
        tk.Label(center_frame, text="Schedule View", font=("Helvetica", 14)).pack(pady=10)
        schedule_columns = ("TeacherName", "ClassName", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
        schedule_tree_frame = tk.Frame(center_frame)
        schedule_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        schedule_tree_scrollbar_y = tk.Scrollbar(schedule_tree_frame)
        schedule_tree_scrollbar_y.pack(side="right", fill="y")

        schedule_tree = ttk.Treeview(schedule_tree_frame, columns=schedule_columns, show="headings", yscrollcommand=schedule_tree_scrollbar_y.set)
        for col in schedule_columns:
            schedule_tree.heading(col, text=col)
            schedule_tree.column(col, width=100, anchor="center")
        schedule_tree.pack(fill="both", expand=True)

        schedule_tree_scrollbar_y.config(command=schedule_tree.yview)

        # ----- Class View (Right Frame) -----
        tk.Label(right_frame, text="Class List", font=("Helvetica", 14)).pack(pady=10)
        class_columns = ("ClassID", "ClassName")
        class_tree_frame = tk.Frame(right_frame)
        class_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        class_tree_scrollbar_y = tk.Scrollbar(class_tree_frame)
        class_tree_scrollbar_y.pack(side="right", fill='y')

        class_tree = ttk.Treeview(class_tree_frame, columns=class_columns, show="headings", yscrollcommand=class_tree_scrollbar_y.set)
        for col in class_columns:
            class_tree.heading(col, text=col)
            class_tree.column(col, width=100)
        class_tree.pack(fill="both", expand=True, padx=5, pady=5)

        class_tree_scrollbar_y.config(command=class_tree.yview)

        # Fetch class data
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ClassID, ClassName FROM Classes")
            for cid, cname in cursor.fetchall():
                class_tree.insert("", "end", values=(cid, cname))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

        # ----- Bottom Buttons -----
        bottom_frame = tk.Frame(top)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Add Schedule", command=lambda: self.open_enter_schedule_popup(schedule_tree)).pack()
        tk.Button(bottom_frame, text="Return", command=top.destroy).pack(side="left", padx=10)
        tk.Button(bottom_frame, text="Export to PDF", command=lambda: self.export_schedule_to_pdf(schedule_tree)).pack(side="left", padx=10)

        # Save widgets for future reference
        self.schedule_tree = schedule_tree
        self.teacher_tree = teacher_tree
        self.class_tree = class_tree
    
    def open_enter_schedule_popup(self, schedule_tree):
        popup = tk.Toplevel(self.master)
        popup.title("Enter Schedule")
        popup.geometry("400x450")
        popup.grab_set()  # Modal behavior

        # --- Form Frame ---
        form_frame = tk.Frame(popup)
        form_frame.pack(pady=10)

        entries = {}
        for label in ["TeacherID", "TeacherName", "ClassID", "ClassName"]:
            tk.Label(form_frame, text=label).pack()
            entry = tk.Entry(form_frame)
            entry.pack()
            entries[label] = entry

        # --- Day Checkboxes ---
        days_frame = tk.Frame(popup)
        days_frame.pack(pady=10)

        tk.Label(days_frame, text="Days to Teach:").pack()

        day_vars = {}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(days_frame, text=day, variable=var)
            cb.pack(anchor="w")
            day_vars[day] = var

        # --- Save Button ---
        save_button = tk.Button(popup, text="Save", command=lambda: self.save_schedule(popup, entries["TeacherID"], entries["TeacherName"], entries["ClassID"], entries["ClassName"], day_vars, schedule_tree))
        save_button.pack(pady=5)

        # --- Bottom Buttons ---
        bottom_frame = tk.Frame(popup)
        bottom_frame.pack(pady=10)

    def save_schedule(self, popup, teacher_id_entry, teacher_name_entry, class_id_entry, class_name_entry, day_vars, schedule_tree):
        try:    
            teacher_id = int(teacher_id_entry.get().strip())
            teacher_name = teacher_name_entry.get().strip()
            class_id = int(class_id_entry.get().strip())
            class_name = class_name_entry.get().strip()
            selected_days = [day for day, var in day_vars.items() if var.get() == 1]

            if not (teacher_id and teacher_name and class_id and class_name and selected_days):
                messagebox.showwarning("Input Error", "Please fill all required fields and select at least one day.")
                return
            
            cursor = self.conn.cursor()


            # Check for duplicate composite key (TeacherID, ClassID)

            for day in selected_days:
                try:
                    cursor.callproc("InsertScheduleStrict", (teacher_id, class_id, day))
                except mysql.connector.Error as err:
                    messagebox.showerror("Insert Error", f"{day}: {err.msg}")
                    return

            # Insert one row per selected day
            for day in selected_days:
                cursor.callproc('InsertScheduleIfNotExists', (teacher_id, class_id, day))

            self.conn.commit()

            # Prepare row data for view
            row_data = {
                "TeacherName": teacher_name,
                "ClassName": class_name,
                "Monday": "",
                "Tuesday": "",
                "Wednesday": "",
                "Thursday": "",
                "Friday": "",
                "Saturday": ""
            }

            for day in selected_days:
                row_data[day] = "✔"

            schedule_tree.insert("", "end", values=(
                row_data["TeacherName"],
                row_data["ClassName"],
                row_data["Monday"],
                row_data["Tuesday"],
                row_data["Wednesday"],
                row_data["Thursday"],
                row_data["Friday"],
                row_data["Saturday"]
            ))

            popup.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def export_schedule_to_pdf(self, schedule_tree):
        try:
            # Define folder and auto-named file
            folder = os.path.join(os.getcwd(), "TeacherLoadSummary")
            os.makedirs(folder, exist_ok=True)  # Ensure folder exists

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"TeacherLoadSummary_{timestamp}.pdf"
            file_path = os.path.join(folder, file_name)

            # Create PDF
            c = canvas.Canvas(file_path, pagesize=landscape(letter))
            width, height = landscape(letter)

            x_offset = 40
            y_offset = height - 40
            row_height = 20
            col_width = 100

            # Column headers
            columns = ["TeacherName", "ClassName", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            for i, col in enumerate(columns):
                c.drawString(x_offset + i * col_width, y_offset, col)
            y_offset -= row_height

            # Data rows
            for item in schedule_tree.get_children():
                values = schedule_tree.item(item)['values']
                for i, value in enumerate(values):
                    c.drawString(x_offset + i * col_width, y_offset, str(value))
                y_offset -= row_height
                if y_offset < 40:
                    c.showPage()
                    y_offset = height - 40
                    for i, col in enumerate(columns):
                        c.drawString(x_offset + i * col_width, y_offset, col)
                    y_offset -= row_height

            c.save()
            messagebox.showinfo("Export Successful", f"Schedule saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export schedule.\n{str(e)}")


    # Global application

    # Privilege Request functions (for Teacher and Coordinator)
    def open_privilege_request_editor(self):
        editor = tk.Toplevel(self)
        editor.title("Request Privilege")
        editor.geometry("500x400")
        editor.state('zoomed')

        text_frame = tk.Frame(editor)
        text_frame.pack(fill="both", padx=10, pady=(10, 5)) 

        text_area = tk.Text(editor, wrap="word", font=("Helvetica", 12))
        text_area.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = tk.Frame(editor)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        def save_request():
            content = text_area.get("1.0", tk.END).strip()
            if not content:
                messagebox.showwarning("Empty Request", "Please write your privilege request before saving.")
                return
            
            folder_path = os.path.join(os.getcwd(), "PrivilegeRequest")
            os.makedirs(folder_path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.username}_priv_request_{timestamp}.txt"
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "w") as f:
                f.write(content)

            messagebox.showinfo("Saved", f"Privilege request saved to:\n{file_path}")
            editor.destroy()

        save_button = tk.Button(button_frame, text="Save Request", command=save_request)
        save_button.pack(pady=10)

    # Assign Color
    def assign_colors(self, subjects):
        # Use 'tab20' which offers more distinct, vibrant colors
        cmap = get_cmap('tab20', len(subjects))

        # Return high-contrast hex colors
        return {subj: to_hex(cmap(i)) for i, subj in enumerate(subjects)}

    # Export Figure to PDF
    def export_to_pdf(self, fig, tag):
        try:
            if not self.conn.is_connected():
                self.conn.reconnect()
            if not fig:
                return
            base_dir = os.path.dirname(os.path.abspath(__file__))  # path to current script
            if "scorecard" in tag:
                export_dir = os.path.join(base_dir, "Scorecard")
            elif "class_performance" in tag:
                export_dir = os.path.join(base_dir, "ClassPerformanceChart")
            else:
                pass

            # Create folder if it doesn't exist
            os.makedirs(export_dir, exist_ok=True)

            # Timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tag}_{timestamp}.pdf"
            file_path = os.path.join(export_dir, filename)

            # Save figure
            fig.savefig(file_path)

            fig.savefig(file_path, bbox_inches='tight')
            messagebox.showinfo("Export Successful", f"Scorecard exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export to PDF:\n{e}")


    # Admin Tab
    def create_admin_tab(self):
        self.admin_frame = tk.Frame(self)
        self.admin_frame.pack(fill="both", expand=True)

        label = tk.Label(self.admin_frame, text="Admin Panel", font=("Helvetica", 16))
        label.pack(pady=20)

        review_scorecard_button = tk.Button(
            self.admin_frame,
            text="Review Scorecard",
            command=lambda: self.review_latest_pdf("Scorecard", "Scorecard")
        )
        review_scorecard_button.pack(pady=10)

        review_class_perf_button = tk.Button(
            self.admin_frame,
            text="Review Class Performance Chart",
            command=lambda: self.review_latest_pdf("ClassPerformanceChart", "Class Performance Chart")
        )
        review_class_perf_button.pack(pady=10)

        grant_privilege_button = tk.Button(
            self.admin_frame,
            text="Grant Privilege",
            command=self.grant_privilege
        )
        grant_privilege_button.pack(pady=10)

    # Review Dashboard
    def review_latest_pdf(self, folder_path, tag):
        try:
            pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
            if not pdf_files:
                messagebox.showinfo("No File Found", f"No {tag} files found in:\n{folder_path}")
                return

            # Get the latest file by modified time
            latest_file = max(pdf_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
            latest_file_path = os.path.join(folder_path, latest_file)

            # Ask user where to save it
            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=latest_file,
                title=f"Save {tag}"
            )
            if not save_path:
                return  # User cancelled

            shutil.copyfile(latest_file_path, save_path)
            messagebox.showinfo("Download Complete", f"{tag} saved to:\n{save_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve {tag}:\n{e}")

    # Grant privilege
    def grant_privilege(self):
        editor = tk.Toplevel(self.master)
        editor.title("Grant Privileges")
        editor.geometry("800x600")

        # Text display
        view_area = scrolledtext.ScrolledText(editor, wrap="word", font=("Courier", 11))
        view_area.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        view_area.config(state="disabled")

        # Frame for Save button
        button_frame = tk.Frame(editor)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Prepare file merge
        today_str = datetime.now().strftime("%Y%m%d")
        request_folder = os.path.join(os.getcwd(), "PrivilegeRequest")
        merged_content = ""

        if not os.path.exists(request_folder):
            messagebox.showinfo("No Requests", "No Privileges request folder found.")
            editor.destroy()
            return

        # Merge today's files
        for filename in os.listdir(request_folder):
            if filename.endswith(".txt") and today_str in filename:
                with open(os.path.join(request_folder, filename), "r") as f:
                    merged_content += f.read().strip() + "\n\n"

        if not merged_content.strip():
            messagebox.showinfo("No Requests", "No privilege requests found for today.")
            editor.destroy()
            return

        # Show merged content
        view_area.config(state="normal")
        view_area.insert("1.0", merged_content)
        view_area.config(state="disabled")

        # Save and execute GRANTs
        def save_and_execute():
            try:
                sql_path = os.path.join(os.getcwd(), "Privileges.sql")
                
                # Read existing file content
                if os.path.exists(sql_path):
                    with open(sql_path, "r") as sql_file:
                        existing_content = sql_file.read()
                else:
                    existing_content = ""

                # Prepare new content with timestamp comment
                new_grants = f"\n-- Grants on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + merged_content + "\n"

                # Insert new_grants above FLUSH PRIVILEGES; (case insensitive)
                flush_index = existing_content.lower().rfind("flush privileges;")
                if flush_index != -1:
                    # Split content and insert before flush
                    before_flush = existing_content[:flush_index]
                    after_flush = existing_content[flush_index:]
                    updated_content = before_flush + new_grants + after_flush
                else:
                    # No flush found, just append at the end
                    updated_content = existing_content + new_grants

                # Write back updated content
                with open(sql_path, "w") as sql_file:
                    sql_file.write(updated_content)

                # Use admin credentials from login
                username = self.username
                password = self.password

                command = f'mysql -u{username} -p{password} < "{sql_path}"'
                # Run SQL file with mysql client (update user/pass/DB as needed)
                result = subprocess.run(
                    command, 
                    shell=True, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                if result.returncode == 0:
                    messagebox.showinfo("Success", "Privileges granted and flushed successfully.")
                    editor.destroy()
                else:
                    messagebox.showerror("Error", f"MySQL returned error code {result.returncode}.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to grant privileges:\n{e}")

        # Save button
        save_button = tk.Button(button_frame, text="Save", command=save_and_execute, font=("Helvetica", 12))
        save_button.pack(pady=5)


    

