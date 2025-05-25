# Python GUI for Academic Staff Using Tkinter and mysql-connector-python

import tkinter as tk
from tkinter import ttk, messagebox, Menu
import mysql.connector
from PIL import Image, ImageTk

# Global login window
class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Login")
        master.iconbitmap(r"D:\\School_GUI\\icon.ico")
        master.geometry("900x600")
        master.state('zoomed')
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        taskbar_height = 40  # adjust if needed


        self.frame = tk.Frame(master)
        self.frame.pack(expand=True)

        img = Image.open(r"D:/School_GUI/Logo.png") 
        img = img.resize((150, 150))  # resize as needed
        self.logo_img = ImageTk.PhotoImage(img)
        self.logo = tk.Label(self.frame, image=self.logo_img)
        self.logo.pack(pady=10)

        self.title_label = tk.Label(self.frame, text="Academic staff portal", font=("Arial", 14))
        self.title_label.pack(pady=5)

        self.username_entry = tk.Entry(self.frame)
        self.username_entry.insert(0, "Username")
        self.username_entry.bind("<FocusIn>", self.clear_username_placeholder)
        self.username_entry.bind("<FocusOut>", self.add_username_placeholder)
        self.username_entry.pack(pady=5)

        self.password_entry = tk.Entry(self.frame, show="")
        self.password_entry.insert(0, "Password")
        self.password_entry.pack(pady=5)
        self.password_entry.bind("<FocusIn>", self.clear_password_placeholder)
        self.password_entry.bind("<FocusOut>", self.add_password_placeholder)
        self.password_entry.bind("<KeyRelease>", self.password_key_release)

        self.show_pass = tk.BooleanVar()
        self.show_pass.set(False)
        self.show_button = tk.Checkbutton(self.frame, text="Show Password", variable=self.show_pass, command=self.toggle_password)
        self.show_button.pack()

        self.login_button = tk.Button(self.frame, text="Login", command=self.check_login)
        self.login_button.pack(pady=10)

        self.exit_button = tk.Button(self.frame, text="Exit", command=self.master.quit)
        self.exit_button.pack(pady=5)

    def clear_username_placeholder(self, event):
        if self.username_entry.get() == "Username":
            self.username_entry.delete(0, tk.END)

    def add_username_placeholder(self, event):
        if not self.username_entry.get():
            self.username_entry.insert(0, "Username")

    def clear_password_placeholder(self, event):
        if self.password_entry.get() == "Password":
            self.password_entry.delete(0, tk.END)
            self.password_entry.config(show="")  # hide password when user starts typing

    def add_password_placeholder(self, event):
        if not self.password_entry.get():
            self.password_entry.insert(0, "Password")
            self.password_entry.config(show="")  # show placeholder text visibly
   
    def password_key_release(self, event):
        if self.show_pass.get():
            self.password_entry.config(show="")  # Show actual password if checked
        else:
            self.password_entry.config(show="*")  # Hide password if unchecked

    def toggle_password(self):
        if self.show_pass.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user=username,
                password=password,
                database="School"
            )
            cursor = conn.cursor()
            role = username.split("_")[0]  # extract 'teacher' from 'teacher_user'
            cursor.execute(f"SET ROLE '{role}'")
            self.master.withdraw()
            app = AcademicSystemApp(conn, role, username, password, self.master)
            app.mainloop()
        except mysql.connector.Error:
            messagebox.showerror("Login Failed", "Please check your user name and password")

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

    # Frame to hold Treeview and Checkboxes side by side
        table_frame = tk.Frame(attendance_window)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Name", "BirthDate")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)
        tree.pack(side="left", fill="both", expand=True, padx=10)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        checkbox_frame = tk.Frame(table_frame)
        checkbox_frame.pack(side="left", padx=10)

        attendance_vars = {}

        for student in students:
            sid, name, bdate = student
            tree.insert("", "end", iid=sid, values=(sid, name, bdate))
            attendance_vars[sid] = tk.BooleanVar()
            cb = tk.Checkbutton(checkbox_frame, variable=attendance_vars[sid])
            cb.pack(anchor="w", pady=2)

        def save_attendance():
            try:
                for student in students:
                    sid, name, bdate = student
                    present = 1 if attendance_vars[sid].get() else 0

            # Check if an attendance record exists for this student & class
                    self.cursor.execute(
                        "SELECT Attendance FROM Attendance WHERE StudentID = %s AND ClassID = %s",
                        (sid, self.class_id)
                    )
                    existing = self.cursor.fetchone()

                    if existing:
                # Add today's attendance to total count
                        new_value = existing[0] + present
                        self.cursor.execute(
                            "UPDATE Attendance SET Attendance = %s WHERE StudentID = %s AND ClassID = %s",
                            (new_value, sid, self.class_id)
                        )
                    else:
                # Insert first attendance record with present = 0 or 1
                        self.cursor.execute(
                            "INSERT INTO Attendance (StudentID, ClassID, Attendance) VALUES (%s, %s, %s)",
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

    # Create Treeview
        columns = ("StudentID", "StudentName", "SubjectID", "SubjectName", "Grade")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(expand=True, fill="both", padx=10, pady=10)

    # Dictionary to store grade entries
        grade_entries = {}

    # Fetch student data from the TempClassRoster
        try:
            cursor = connection.cursor()
            cursor.callproc("GetClassRosterByName", (class_name,))
            for result in cursor.stored_results():
                students = result.fetchall()
        
            for student in students:
                student_id, student_name, birthdate = student

            # Insert row with empty grade field
                tree.insert("", "end", values=(student_id, student_name, subject_id, subject_name, ""))

                # Add double-click binding to open grade entry
                def on_double_click(event):
                    selected_item = tree.focus()
                    if not selected_item:
                        return
                    values = tree.item(selected_item, "values")
                    student_id = values[0]

                    # Popup to enter grade
                    def save_popup_grade():
                        grade = grade_var.get().strip()
                        tree.set(selected_item, "Grade", grade)
                        grades_dict[student_id] = grade
                        popup.destroy()

                    popup = tk.Toplevel(top)
                    popup.title("Enter Grade")
                    popup.geometry("250x100")
                    grade_var = tk.StringVar()

                    tk.Label(popup, text=f"Grade for {values[1]}:").pack(pady=5)
                    tk.Entry(popup, textvariable=grade_var).pack()
                    tk.Button(popup, text="Save", command=save_popup_grade).pack(pady=5)

                tree.bind("<Double-1>", on_double_click)


            # Add a grade entry widget
                grade_entries[student_id] = tk.StringVar()

        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            top.destroy()
            return

    # Function to save grades
        def save_grades():
            cursor = connection.cursor()
            inserted = 0
            for child in tree.get_children():
                values = tree.item(child)["values"]
                student_id = values[0]
                grade = grades_dict.get(student_id, "").strip()
                # if grade.strip() == "":
                #     continue
                if not grade:
                    continue
                try:
                    cursor.execute("INSERT INTO Grades (StudentID, SubjectID, Grade) VALUES (%s, %s, %s)",
                                (student_id, subject_id, grade))
                    inserted += 1   
                except Exception as e:
                    messagebox.showerror("Insert Error", f"Error for Student ID {student_id}: {e}")
            connection.commit()
            messagebox.showinfo("Success", f"{inserted} grades inserted successfully.")

    # Save and Return buttons
        button_frame = tk.Frame(top)
        button_frame.pack(pady=10)

        save_button = tk.Button(button_frame, text="Save Grades", command=save_grades)
        save_button.pack(side="left", padx=10)

        return_button = tk.Button(button_frame, text="Return", command=top.destroy)
        return_button.pack(side="left", padx=10)
    #     def save_grades():
    #         grade_entries = []
    #         for row in rows:
    #             student_id = row["StudentID"]
    #             grade_value = row["grade_var"].get().strip()
    #             if grade_value:
    #                 try:
    #                     grade_value = float(grade_value)
    #                     grade_entries.append((student_id, subject_id, grade_value))
    #                 except ValueError:
    #                     messagebox.showwarning("Invalid Grade", f"Grade for StudentID {student_id} must be a number.")
    #                     return

    #         cursor = self.connection.cursor()
    #         for student_id, subj_id, grade in grade_entries:
    #             cursor.execute("""
    #                 INSERT INTO Grades (StudentID, SubjectID, Grade)
    #                 VALUES (%s, %s, %s)
    #                 ON DUPLICATE KEY UPDATE Grade = VALUES(Grade)
    #             """, (student_id, subj_id, grade))
    #         self.connection.commit()
    #         messagebox.showinfo("Success", "Grades saved successfully.")

    #     def return_to_teacher_tab():
    #         top.destroy()

    #     # Create grade input window
    #     top = tk.Toplevel(self)
    #     top.title(f"Insert Grades for {class_name} - {subject_name}")
    #     top.geometry("800x500")

    # # Run stored procedure to populate TempClassRoster
    #     cursor = self.connection.cursor()
    #     cursor.callproc("GetClassRosterByName", (class_name,))
    #     for result in cursor.stored_results():
    #         students = result.fetchall()

    # # Build headers
    #     headers = ["StudentID", "StudentName", "SubjectID", "SubjectName", "Grade"]
    #     for col, text in enumerate(headers):
    #         tk.Label(top, text=text, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=10, pady=5)

    #     rows = []
    #     for i, student in enumerate(students, start=1):
    #         student_id, student_name, _ = student
    #         grade_var = tk.StringVar()

    #         tk.Label(top, text=student_id).grid(row=i, column=0)
    #         tk.Label(top, text=student_name).grid(row=i, column=1)
    #         tk.Label(top, text=subject_id).grid(row=i, column=2)
    #         tk.Label(top, text=subject_name).grid(row=i, column=3)
    #         tk.Entry(top, textvariable=grade_var).grid(row=i, column=4)

    #         rows.append({"StudentID": student_id, "grade_var": grade_var})

    # # Save and Return buttons
    #     save_btn = tk.Button(top, text="Save", command=save_grades, bg="#4CAF50", fg="white", width=12)
    #     save_btn.grid(row=len(students) + 1, column=3, pady=15)

    #     return_btn = tk.Button(top, text="Return", command=return_to_teacher_tab, bg="#f44336", fg="white", width=12)
    #     return_btn.grid(row=len(students) + 1, column=4, pady=15)


    def create_coordinator_tab(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Button(frame, text="Generate Scorecard", command=self.generate_scorecard).pack()
        tk.Button(frame, text="Teacher Load Summary", command=self.generate_teacher_summary).pack()

    def generate_scorecard(self):
        top = tk.Toplevel(self)
        top.title("Scorecard")

        tree = ttk.Treeview(top, columns=("StudentID", "SubjectID", "Score"), show='headings')
        tree.heading("StudentID", text="Student ID")
        tree.heading("SubjectID", text="Subject ID")
        tree.heading("Score", text="Score")

        self.cursor.execute("SELECT StudentID, SubjectID, Score FROM Grades")
        for row in self.cursor.fetchall():
            tree.insert('', tk.END, values=row)

        tree.pack(fill=tk.BOTH, expand=True)

    def generate_teacher_summary(self):
        top = tk.Toplevel(self)
        top.title("Teacher Load Summary")

        tree = ttk.Treeview(top, columns=("TeacherID", "SubjectID", "ClassCount"), show='headings')
        tree.heading("TeacherID", text="Teacher ID")
        tree.heading("SubjectID", text="Subject ID")
        tree.heading("ClassCount", text="Classes Assigned")

        self.cursor.execute("""
            SELECT Teachers.TeacherID, Teachers.SubjectID, COUNT(Classes.ClassID)
            FROM Teachers
            LEFT JOIN Classes ON Teachers.TeacherID = Classes.TeacherID
            GROUP BY Teachers.TeacherID
        """)
        for row in self.cursor.fetchall():
            tree.insert('', tk.END, values=row)

        tree.pack(fill=tk.BOTH, expand=True)

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

if __name__ == '__main__':
    root = tk.Tk()
    login_app = LoginWindow(root)
    root.mainloop()

