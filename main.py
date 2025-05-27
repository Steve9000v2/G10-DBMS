import tkinter as tk
from log_in_window import LoginWindow

if __name__ == '__main__':
    root = tk.Tk()
    login_app = LoginWindow(root)
    root.mainloop()