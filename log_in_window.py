import tkinter as tk
from tkinter import ttk, messagebox, Menu
from tkinter import *
import mysql.connector
from PIL import Image, ImageTk
from academic_system_app import AcademicSystemApp

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