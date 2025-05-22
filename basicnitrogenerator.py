import random
import string
import requests
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

NITRO_URL = "https://discord.gift/"
CHARS = string.ascii_letters + string.digits

_sess = requests.Session()
_sess.mount('https://', requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100))

def make_code():
    return ''.join(random.choices(CHARS, k=18))

def verify_code(code):
    url = f"https://discordapp.com/api/v9/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"
    try:
        resp = _sess.get(url, timeout=3)
        return resp.status_code == 200
    except Exception:
        return False

def post_webhook(webhook_url, code):
    payload = {
        "content": f"🎉 Congratulations! A valid Nitro code was found: {NITRO_URL}{code}"
    }
    try:
        _sess.post(webhook_url, json=payload, timeout=3)
    except Exception:
        pass

class NitroGenApp:
    def __init__(self, root):
        self.root = root
        root.title("Nitro Generator")
        root.geometry("500x500")
        root.resizable(False, False)
        root.configure(bg="#23272A")

        self.is_running = False
        self.threads = []
        self.stop_flag = threading.Event()
        self.last_code = None
        self.checked = 0
        self.found = 0
        self.webhook = ""

        self.title = tk.Label(root, text="Discord Nitro Generator", font=("Segoe UI", 18, "bold"), fg="#7289DA", bg="#23272A")
        self.title.pack(pady=10)

        self.info = tk.Label(
            root,
            text="When a valid Nitro code is found, it will be sent to the webhook.",
            font=("Segoe UI", 10),
            fg="#99AAB5",
            bg="#23272A",
            wraplength=480,
            justify="center"
        )
        self.info.pack(pady=(0, 10))

        self.webhook_lbl = tk.Label(root, text="Enter Webhook URL:", font=("Segoe UI", 12), fg="#99AAB5", bg="#23272A")
        self.webhook_lbl.pack(pady=(5,0))
        self.webhook_entry = ttk.Entry(root, width=60)
        self.webhook_entry.pack(pady=(0,10))

        self.status = tk.Label(root, text="Status: Idle", font=("Segoe UI", 12), fg="#99AAB5", bg="#23272A")
        self.status.pack(pady=5)

        self.checked_lbl = tk.Label(root, text="Codes Checked: 0", font=("Segoe UI", 12), fg="#99AAB5", bg="#23272A")
        self.checked_lbl.pack(pady=5)

        self.found_lbl = tk.Label(root, text="Codes Found: 0", font=("Segoe UI", 12, "bold"), fg="#43B581", bg="#23272A")
        self.found_lbl.pack(pady=5)

        self.valid_lbl = tk.Label(root, text="", font=("Segoe UI", 12, "bold"), fg="#43B581", bg="#23272A")
        self.valid_lbl.pack(pady=5)

        self.start_btn = ttk.Button(root, text="Start", command=self.start)
        self.start_btn.pack(pady=10)

        self.stop_btn = ttk.Button(root, text="Stop", command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.footer = tk.Frame(root, bg="#23272A")
        self.footer.pack(side="bottom", pady=10)

        self.madeby = tk.Label(self.footer, text="Made by cerlux", font=("Segoe UI", 10, "italic"), fg="#99AAB5", bg="#23272A", cursor="hand2")
        self.madeby.pack(side="left")
        self.gh_link = tk.Label(self.footer, text="(GitHub)", font=("Segoe UI", 10, "underline"), fg="#7289DA", bg="#23272A", cursor="hand2")
        self.gh_link.pack(side="left", padx=(5,0))
        self.gh_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/JorisvanderVuurst"))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 11), padding=6)

    def set_status(self, msg):
        self.status.config(text=f"Status: {msg}")
        self.status.update_idletasks()

    def set_checked(self):
        self.checked_lbl.config(text=f"Codes Checked: {self.checked}")
        self.checked_lbl.update_idletasks()

    def set_found(self):
        self.found_lbl.config(text=f"Codes Found: {self.found}")
        self.found_lbl.update_idletasks()

    def set_valid(self, code):
        if code:
            self.valid_lbl.config(text=f"🎉 Valid Nitro code found!\n{NITRO_URL}{code}")
        else:
            self.valid_lbl.config(text="")
        self.valid_lbl.update_idletasks()

    def worker(self):
        while not self.stop_flag.is_set():
            code = make_code()
            if verify_code(code):
                post_webhook(self.webhook, code)
                self.last_code = code
                self.found += 1
                self.set_found()
                self.set_valid(code)
                self.set_status("Valid code found!")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success!",
                    f"Valid Nitro code found!\n{NITRO_URL}{code}\n\nThe code has been sent to your webhook."
                ))
                break
            else:
                self.checked += 1
                self.set_checked()
                self.set_status("Searching...")

    def start(self):
        if self.is_running:
            return
        url = self.webhook_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a Discord webhook URL before starting.")
            return
        self.webhook = url
        self.is_running = True
        self.checked = 0
        self.found = 0
        self.last_code = None
        self.set_checked()
        self.set_found()
        self.set_valid(None)
        self.set_status("Searching...")
        self.stop_flag.clear()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.start_btn.update_idletasks()
        self.stop_btn.update_idletasks()
        self.threads = []
        for _ in range(50):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            self.threads.append(t)
        self.root.after(100, self.check_threads)

    def stop(self):
        if not self.is_running:
            return
        self.stop_flag.set()
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.set_status("Stopped")
        self.start_btn.update_idletasks()
        self.stop_btn.update_idletasks()

    def check_threads(self):
        if not self.is_running:
            return
        if self.stop_flag.is_set():
            self.is_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.start_btn.update_idletasks()
            self.stop_btn.update_idletasks()
            if self.last_code:
                self.set_status("Valid code found!")
            else:
                self.set_status("Stopped")
            return
        self.root.after(100, self.check_threads)

def run_gui():
    root = tk.Tk()
    NitroGenApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
