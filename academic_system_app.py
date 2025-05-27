# Python GUI for Academic Staff Using Tkinter and mysql-connector-python
import tkinter as tk
from tkinter import ttk, messagebox, Menu
from tkinter import *
import mysql.connector
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure


import os
from datetime import datetime

# Main app class
class AcademicSystemApp(tk.Tk):
    def __init__(self, conn, role, username, password, master):
        super().__init__()
        self.master = master
        self.iconbitmap(r"D:\\School_GUI\\icon.ico")
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
            self.open_teacher_id_window(self.conn, self.on_valid_teacher_id)
        elif self.role == "coordinator":
            self.create_coordinator_tab()
        elif self.role == "admin":
            self.create_admin_tab()

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
        profile_window.geometry("400x300")

        tk.Label(profile_window, text=f"Username: {self.conn.user}").pack(pady=10)
        tk.Label(profile_window, text=f"Password: {self.password}").pack(pady=10)
        tk.Label(profile_window, text=f"Role: {self.role}").pack(pady=10)

        try:
            self.cursor.execute("SHOW GRANTS FOR CURRENT_USER")
            grants = self.cursor.fetchall()
            tk.Label(profile_window, text="Privileges:").pack()
            for grant in grants:
                tk.Label(profile_window, text=grant[0], wraplength=380, justify="left").pack(anchor="w", padx=10)
        except mysql.connector.Error as err:
            tk.Label(profile_window, text=f"Error fetching privileges: {err}").pack()

    def logout(self):
        self.destroy()
        self.master.deiconify()  # show login window again

    def open_teacher_id_window(self, connection, on_valid_callback):
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

            if not data or data[0][0] == 'NOT FOUND':
                messagebox.showerror("Not Found", f"No class assigned to Teacher ID {teacher_id}")
            else:
                class_name = data[0][0]  # ClassName
                class_id = data[0][1]    # ClassID
                subject_id = data[0][2]  # SubjectID
                subject_name = data[0][3] # SubjectName

                top.destroy()
                on_valid_callback(teacher_id, class_name, class_id, subject_id, subject_name)

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

    def on_valid_teacher_id(self, teacher_id, class_name, class_id, subject_id, subject_name):
        self.teacher_id = teacher_id
        self.class_name = class_name
        self.class_id = class_id
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.create_teacher_tab(teacher_id, class_name, class_id, subject_id, subject_name)

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

    def open_attendance_window(self, class_name):
        attendance_window = tk.Toplevel(self)
        attendance_window.title(f"{class_name} Attendance")
        attendance_window.geometry("900x600")

        self.cursor.callproc('GetClassRosterByName', (class_name,))
        students = []
        for result in self.cursor.stored_results():
            students = result.fetchall()

        header = tk.Label(attendance_window, text=f"{class_name} - Class Roster", font=("Helvetica", 14))
        header.pack(pady=10)

    # Scrollable Frame for student input
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

            label = tk.Label(student_frame, text=f"{sid} - {name} ({bdate})", anchor="w", width=40)
            label.pack(side="left", padx=5)

            entry = tk.Entry(student_frame)
            entry.pack(side="left", padx=5)
            attendance_vars[sid] = entry

        def save_attendance():
            try:
                for student in students:
                    sid, name, bdate = student
                    # present = 1 if attendance_vars[sid].get() else 0
                    entry_value = attendance_vars[sid].get().strip().lower()
                    if entry_value == "attend":
                        present = 1
                    elif entry_value == "absent":
                        present = 0
                    else:
                        messagebox.showwarning("Invalid Input", f"Invalid input for {name}. Use 'Attend' or 'Absent'.")
                        return

            # Check if an attendance record exists for this student & class
                    self.cursor.execute(
                        "SELECT AttendanceStatus FROM Attendances WHERE StudentID = %s AND ClassID = %s",
                        (sid, self.class_id)
                    )
                    existing = self.cursor.fetchone()

                    if existing:
                # Add today's attendance to total count
                        new_value = existing[0] + present
                        self.cursor.execute(
                            "UPDATE Attendances SET AttendanceStatus = %s WHERE StudentID = %s AND ClassID = %s",
                            (new_value, sid, self.class_id)
                        )
                    else:
                # Insert first attendance record with present = 0 or 1
                        self.cursor.execute(
                            "INSERT INTO Attendances (StudentID, ClassID, AttendanceStatus) VALUES (%s, %s, %s)",
                            (sid, self.class_id, present)
                        )

                self.conn.commit()
                messagebox.showinfo("Saved", "Attendance successfully saved.")
                attendance_window.destroy()  # Close window after saving

            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Error", f"Failed to save attendance:\n{e}")

        save_button = tk.Button(attendance_window, text="Save Attendance", command=save_attendance)
        save_button.pack(pady=10)

        return_button = tk.Button(attendance_window, text="Return", command=attendance_window.destroy)
        return_button.place(x=10, y=10)

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
                print(f"[DEBUG] grade entered: '{grade}'")

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

        # ✅ Bind the handler ONCE
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



    # def create_coordinator_tab(self):
    #     frame = ttk.Frame(self)
    #     frame.pack(fill=tk.BOTH, expand=True)

    #     tk.Button(frame, text="Generate Scorecard", command=self.generate_scorecard).pack()
    #     tk.Button(frame, text="Teacher Load Summary", command=self.generate_teacher_summary).pack()

    # def generate_scorecard(self):
    #     top = tk.Toplevel(self)
    #     top.title("Scorecard")

    #     tree = ttk.Treeview(top, columns=("StudentID", "SubjectID", "Score"), show='headings')
    #     tree.heading("StudentID", text="Student ID")
    #     tree.heading("SubjectID", text="Subject ID")
    #     tree.heading("Score", text="Score")

    #     self.cursor.execute("SELECT StudentID, SubjectID, Score FROM Grades")
    #     for row in self.cursor.fetchall():
    #         tree.insert('', tk.END, values=row)

    #     tree.pack(fill=tk.BOTH, expand=True)

    # def generate_teacher_summary(self):
    #     top = tk.Toplevel(self)
    #     top.title("Teacher Load Summary")

    #     tree = ttk.Treeview(top, columns=("TeacherID", "SubjectID", "ClassCount"), show='headings')
    #     tree.heading("TeacherID", text="Teacher ID")
    #     tree.heading("SubjectID", text="Subject ID")
    #     tree.heading("ClassCount", text="Classes Assigned")

    #     self.cursor.execute("""
    #         SELECT Teachers.TeacherID, Teachers.SubjectID, COUNT(Classes.ClassID)
    #         FROM Teachers
    #         LEFT JOIN Classes ON Teachers.TeacherID = Classes.TeacherID
    #         GROUP BY Teachers.TeacherID
    #     """)
    #     for row in self.cursor.fetchall():
    #         tree.insert('', tk.END, values=row)

    #     tree.pack(fill=tk.BOTH, expand=True)

    def create_coordinator_tab(self):
        self.coordinator_frame = tk.Frame(self)
        self.coordinator_frame.pack(fill="both", expand=True)

        label = tk.Label(self.coordinator_frame, text="Coordinator Panel", font=("Helvetica", 16))
        label.pack(pady=20)

        insert_update_student_button = tk.Button(
            self.coordinator_frame, 
            text="Insert/Update Student Info", 
            command=self.open_student_info_window  # Placeholder: implement later
        )
        insert_update_student_button.pack(pady=10)

        scorecard_button = tk.Button(
            self.coordinator_frame,
            text="Generate Scorecard",
            command=self.open_scorecard_window
        )
        scorecard_button.pack(pady=10)

        class_perf_button = tk.Button(
            self.coordinator_frame,
            text="Generate Class Performance",
            command=self.open_class_performance_window
        )
        class_perf_button.pack(pady=10)

        # teacher_summary_button = tk.Button(
        #     self.coordinator_frame, 
        #     text="Create Teacher Load Summary", 
        #     command=self.teacher_load_summary # Placeholder: implement later
        # )
        # teacher_summary_button.pack(pady=10)

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
            cursor.execute("SELECT ClassID, ClassName FROM Classes")
            rows = cursor.fetchall()
            for row in rows:
                class_tree.insert('', 'end', values=row)
            cursor.close()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))


    def fetch_students(self):
        print("Fetching students...")
        try:
            for row in self.student_tree.get_children():
                self.student_tree.delete(row)

            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM Students")
            rows = cursor.fetchall()
            print(f"Rows fetched: {rows}")
            for row in rows:
                self.student_tree.insert('', 'end', values=row)
            cursor.close()
        except Exception as e:
            print(f"Error fetching students: {e}")
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
                query = "INSERT INTO Students (StudentID, StudentName, BirthDate, ClassID, Address) VALUES (%s, %s, %s, %s, %s)"
                data = (
                    entries["StudentID"].get(),
                    entries["StudentName"].get(),
                    entries["BirthDate (YYYY-MM-DD)"].get(),
                    entries["ClassID"].get(),
                    entries["Address"].get()
                )
                cursor.execute(query, data)
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
                query = """UPDATE Students 
                        SET StudentName=%s, BirthDate=%s, ClassID=%s, Address=%s 
                        WHERE StudentID=%s"""
                data = (
                    entries["StudentName"].get(),
                    entries["BirthDate (YYYY-MM-DD)"].get(),
                    entries["ClassID"].get(),
                    entries["Address"].get(),
                    values[0]  # StudentID
                )
                cursor.execute(query, data)
                self.conn.commit()
                cursor.close()
                popup.destroy()
                self.fetch_students()
            except Exception as e:
                messagebox.showerror("Update Error", str(e))

        tk.Button(popup, text="Submit", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def open_scorecard_window(self):
        self.scorecard_win = tk.Toplevel(self)
        win = self.scorecard_win
        win.title("Scorecard")
        win.state('zoomed')

        return_button = tk.Button(win, text="Return", command=win.destroy)
        return_button.pack(side="bottom", pady=10)

        fig, ax = plt.subplots(figsize=(10, 6))
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT SubjectName FROM Subjects")
            subjects = [row[0] for row in cursor.fetchall()]
            colors = self.assign_colors(subjects)

            has_data = False
            for subject in subjects:
                cursor.execute("""
                    SELECT g.Score
                    FROM Grades g
                    JOIN Subjects s ON g.SubjectID = s.SubjectID
                    WHERE s.SubjectName = %s
                """, (subject,))
                scores = [row[0] for row in cursor.fetchall()]
                if scores:
                    has_data = True
                    ax.hist(scores, bins=10, alpha=0.6, label=subject,
                            color=colors[subject], edgecolor='black')

            cursor.close()

            if not has_data:
                ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

            ax.set_title("Score Distribution by Subject")
            ax.set_xlabel("Score")
            ax.set_ylabel("Number of Students")
            ax.legend()
            fig.tight_layout()
            canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_class_performance_window(self):
        self.class_perf_win = tk.Toplevel(self)
        win = self.class_perf_win
        win.title("Class Performance")
        win.state('zoomed')

        # UI Elements
        top_frame = tk.Frame(win)
        top_frame.pack(side="top", fill="x", pady=10)

        tk.Label(top_frame, text="Enter Class Name:").pack(side="left", padx=10)
        class_entry = tk.Entry(top_frame)
        class_entry.pack(side="left", padx=5)

        fig, ax = plt.subplots(figsize=(10, 6))
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True)

        def generate_chart(class_name):
            ax.clear()
            if not class_name:
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
                        ax.hist(scores, bins=10, alpha=0.6, label=subject,
                                color=colors[subject], edgecolor='black')

                cursor.close()

                if not has_data:
                    ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

                ax.set_title(f"Score Distribution - Class {class_name}")
                ax.set_xlabel("Score")
                ax.set_ylabel("Number of Students")
                ax.legend()
                fig.tight_layout()
                canvas.draw()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        generate_button = tk.Button(top_frame, text="Generate", command=lambda: generate_chart(class_entry.get()))
        generate_button.pack(side="left", padx=10)

        return_button = tk.Button(win, text="Return", command=win.destroy)
        return_button.pack(side="bottom", pady=10)


    # def open_scorecard_window(self):
    #     win = tk.Toplevel(self)
    #     win.title("Scorecard")
    #     win.state('zoomed')

    #     # Return button
    #     return_button = tk.Button(win, text="Return", command=win.destroy)
    #     return_button.pack(side="bottom", pady=10)

    #     # Matplotlib figure
    #     fig, ax = plt.subplots(figsize=(10, 6))
    #     canvas = FigureCanvasTkAgg(fig, master=win)
    #     canvas.get_tk_widget().pack(fill="both", expand=True)

    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("SELECT SubjectName FROM Subjects")
    #         subjects = [row[0] for row in cursor.fetchall()]
    #         colors = self.assign_colors(subjects)

    #         has_data = False
    #         for subject in subjects:
    #             cursor.execute("""
    #                 SELECT g.Score
    #                 FROM Grades g
    #                 JOIN Subjects s ON g.SubjectID = s.SubjectID
    #                 WHERE s.SubjectName = %s
    #             """, (subject,))
    #             scores = [row[0] for row in cursor.fetchall()]
    #             if scores:
    #                 has_data = True
    #                 ax.hist(scores, bins=10, alpha=0.6, label=subject,
    #                         color=colors[subject], edgecolor='black')

    #         cursor.close()

    #         if not has_data:
    #             ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

    #         ax.set_title("Score Distribution by Subject")
    #         ax.set_xlabel("Score")
    #         ax.set_ylabel("Number of Students")
    #         ax.legend()
    #         fig.tight_layout()
    #         canvas.draw()
    #     except Exception as e:
    #         messagebox.showerror("Error", str(e))

    # def open_class_performance_window(self):
    #     win = tk.Toplevel(self)
    #     win.title("Class Performance")
    #     win.state('zoomed')

    #     # Top input area
    #     top_frame = tk.Frame(win)
    #     top_frame.pack(side="top", fill="x", pady=10)

    #     tk.Label(top_frame, text="Enter Class Name:").pack(side="left", padx=10)
    #     class_entry = tk.Entry(top_frame)
    #     class_entry.pack(side="left", padx=5)

    #     generate_button = tk.Button(top_frame, text="Generate", command=lambda: generate_chart(class_entry.get()))
    #     generate_button.pack(side="left", padx=10)

    #     # Return button
    #     return_button = tk.Button(win, text="Return", command=win.destroy)
    #     return_button.pack(side="bottom", pady=10)

    #     # Matplotlib chart area
    #     fig, ax = plt.subplots(figsize=(10, 6))
    #     canvas = FigureCanvasTkAgg(fig, master=win)
    #     canvas.get_tk_widget().pack(fill="both", expand=True)

    #     def generate_chart(class_name):
    #         ax.clear()
    #         if not class_name:
    #             messagebox.showwarning("Missing Input", "Please enter a class name.")
    #             return

    #         try:
    #             cursor = self.conn.cursor()
    #             cursor.execute("SELECT SubjectName FROM Subjects")
    #             subjects = [row[0] for row in cursor.fetchall()]
    #             colors = self.assign_colors(subjects)

    #             cursor.execute("SELECT ClassID FROM Classes WHERE ClassName = %s", (class_name,))
    #             row = cursor.fetchone()
    #             if not row:
    #                 messagebox.showerror("Invalid Class", f"No class named '{class_name}' found.")
    #                 return
    #             class_id = row[0]

    #             has_data = False
    #             for subject in subjects:
    #                 cursor.execute("""
    #                     SELECT g.Score
    #                     FROM Grades g
    #                     JOIN Students s ON g.StudentID = s.StudentID
    #                     JOIN Subjects sb ON g.SubjectID = sb.SubjectID
    #                     WHERE s.ClassID = %s AND sb.SubjectName = %s
    #                 """, (class_id, subject))
    #                 scores = [r[0] for r in cursor.fetchall()]
    #                 if scores:
    #                     has_data = True
    #                     ax.hist(scores, bins=10, alpha=0.6, label=subject,
    #                             color=colors[subject], edgecolor='black')

    #             cursor.close()

    #             if not has_data:
    #                 ax.text(0.5, 0.5, 'No scores to display', ha='center', va='center', transform=ax.transAxes)

    #             ax.set_title(f"Score Distribution - Class {class_name}")
    #             ax.set_xlabel("Score")
    #             ax.set_ylabel("Number of Students")
    #             ax.legend()
    #             fig.tight_layout()
    #             canvas.draw()
    #         except Exception as e:
    #             messagebox.showerror("Error", str(e))

    # def assign_colors(self, subjects):
    #     from matplotlib.colors import to_hex
    #     cmap = plt.cm.get_cmap('tab10', len(subjects))
    #     return {subj: to_hex(cmap(i)) for i, subj in enumerate(subjects)}









        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    def create_admin_tab(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Review Dashboard and Grant Privileges").pack()
        tk.Button(frame, text="Review Dashboard", command=self.review_dashboard).pack()
        tk.Button(frame, text="Grant Privilege", command=self.grant_privilege).pack()

    def review_dashboard(self):
        messagebox.showinfo("Dashboard", "Dashboard reviewed.")

    def grant_privilege(self):
        messagebox.showinfo("Privileges", "Privileges granted (simulated).")

    

