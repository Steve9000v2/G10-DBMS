import tkinter as tk
from tkinter import ttk, messagebox, Menu
from tkinter import *

import mysql.connector

from PIL import Image, ImageTk

import smtplib

from email.mime.text import MIMEText

import random

import subprocess

import os

from academic_system_app import AcademicSystemApp

# Global login window

class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Login")
        master.iconbitmap(r"D:/School_GUI/icon.ico")
        master.geometry("900x600")
        master.state('zoomed')

        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        taskbar_height = 40  # adjust if needed

        bg_image = Image.open(r"D:/School_GUI/background.png")  # Replace with your image path
        bg_image = bg_image.resize((screen_width, screen_height - taskbar_height))
        self.bg_photo = ImageTk.PhotoImage(bg_image)

        self.bg_label = tk.Label(master, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.frame = tk.Frame(master, bg="white", bd=2, relief="groove")
        self.frame.pack(expand=True)
        self.frame.configure(highlightbackground="black", highlightthickness=1)

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

        self.login_button = tk.Button(
            self.frame, 
            text="Login", 
            command=self.check_login, 
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            activebackground="#45a049",
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.login_button.pack(pady=10)
        self.master.bind('<Return>', lambda event: self.check_login())

        self.forgot_button = tk.Button(
            self.frame,
            text="Forgot Password?",
            command=self.open_forgot_password_window,
            bg="#4169E1",         # Royal blue
            fg="white",
            font=("Arial", 12, "bold"),
            activebackground="#27408B",
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.forgot_button.pack(pady=10)


        self.exit_button = tk.Button(
            self.frame, 
            text="Exit", 
            command=self.master.quit,
            bg="#f44336",        
            fg="white",
            font=("Arial", 12, "bold"),
            activebackground="#e53935",
            relief="flat",
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.exit_button.pack(pady=10)
        self.master.bind('<Escape>', lambda event: self.master.quit())

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

    def open_forgot_password_window(self):
        self.pin_attempts = 3
        self.generated_pin = None

        popup = tk.Toplevel(self.master)
        popup.title("Reset Password")
        popup.geometry("400x350")
        popup.grab_set()

        tk.Label(popup, text="Username").pack(pady=5)
        username_entry = tk.Entry(popup)
        username_entry.pack(pady=5)

        tk.Label(popup, text="Email Address").pack(pady=5)
        email_entry = tk.Entry(popup)
        email_entry.pack(pady=5)

        def send_pin():
            username = username_entry.get()
            email = email_entry.get()
            if not username or not email:
                messagebox.showwarning("Missing Info", "Please enter Username and Email first.")
                return
            self.generated_pin = f"{random.randint(100000, 999999)}"
            success = send_email(email, self.generated_pin)
            if success:
                messagebox.showinfo("PIN Sent", f"PIN sent to {email}.")
            else:
                messagebox.showerror("Error", "Failed to send email. Check your internet or email config.")

        def send_email(recipient_email, pin_code):
            # Get app password
            def get_email_credentials():
                try:
                    with open("GmailAppPassword.txt", "r") as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            email = lines[0].strip()
                            password = lines[1].strip()
                            return email, password
                        else:
                            messagebox.showerror("File Error", "Email file must contain email on line 1 and password on line 2.")
                    return None, None
                except FileNotFoundError:
                    messagebox.showerror("Missing File", "email_password.txt not found.")
                    return None
                
            sender_email, app_password = get_email_credentials()
            if not sender_email or not app_password:
                return False

            msg = MIMEText(f"Your verification PIN is: {pin_code}")
            msg["Subject"] = "Password Reset - PIN Code"
            msg["From"] = sender_email
            msg["To"] = recipient_email

            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(sender_email, app_password)
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                return True
            except Exception as e:
                print("Error sending email:", e)
                return False

        send_button = tk.Button(popup, text="Send PIN", command=send_pin)
        send_button.pack(pady=5)

        tk.Label(popup, text="Enter Received PIN").pack(pady=5)
        pin_entry = tk.Entry(popup)
        pin_entry.pack(pady=5)

        def verify_pin():
            entered_pin = pin_entry.get()
            username = username_entry.get()

            if self.generated_pin is None:
                messagebox.showwarning("PIN Required", "Please click Send PIN first.")
                return
            
            if entered_pin == self.generated_pin:
                popup.destroy()
                self.open_password_change_window(username)
            else:
                self.pin_attempts -= 1
                if self.pin_attempts <= 0:
                    messagebox.showerror("Too Many Attempts", "Please resend PIN to try again.")
                else:
                    messagebox.showwarning("Incorrect PIN", f"Wrong PIN. {self.pin_attempts} attempt(s) left.")

        tk.Button(popup, text="Verify PIN", command=verify_pin).pack(pady=10)
        
    def open_password_change_window(self, username):
        win = tk.Toplevel(self.master)
        win.title("Set New Password")
        win.geometry("300x200")
        win.grab_set()

        tk.Label(win, text="New Password").pack(pady=5)
        new_pass_entry = tk.Entry(win, show="")
        new_pass_entry.pack(pady=5)

        def run_sql_file(filepath):
            try:
                with open("mysql_credentials.txt", "r") as cred_file:
                    user = cred_file.readline().strip()
                    password = cred_file.readline().strip()

                mysql_path = "mysql"  
                sql_file_path = os.path.abspath(filepath)

                command = f'{mysql_path} -u{user} -p{password} -e "source {sql_file_path}"'

                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True
                )

            except Exception as e:
                messagebox.showerror("Execution Failed", f"Could not run Privileges.sql:\n{e}")

        def save_new_password():
            new_pass = new_pass_entry.get()
            if not new_pass:
                messagebox.showwarning("Empty", "Password cannot be empty.")
                return

            try:
                with open("Privileges.sql", "r") as file:
                    lines = file.readlines()

                for i, line in enumerate(lines):
                    if f"CREATE USER IF NOT EXISTS '{username}'" in line or f"Alter USER '{username}'" in line:
                        lines[i] = f"ALTER USER '{username}'@'localhost' IDENTIFIED BY '{new_pass}';\n"
                        break
                else:
                    messagebox.showerror("Error", "Username not found in Privileges.sql")
                    return

                with open("Privileges.sql", "w") as file:
                    file.writelines(lines)

                run_sql_file("Privileges.sql") # Commit new password

                # Optional: run the script here with mysql if needed
                messagebox.showinfo("Success", "Password updated successfully.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(win, text="Save", command=save_new_password).pack(pady=15)
