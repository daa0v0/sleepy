import time
import requests
import os
import ctypes
import configparser
import threading
import tkinter as tk
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image
import sys
import queue

# Global variables
SERVER_URL = ""
SECRET = ""
last_app_name = ""
last_sent_time = 0
config_path = ""
START_SILENTLY = False

# Determine the base path for resources
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Load configuration from config.ini
def load_config():
    global SERVER_URL, SECRET, config_path, START_SILENTLY
    config = configparser.ConfigParser()
    
    if getattr(sys, 'frozen', False):
        config_path = os.path.join(os.path.dirname(sys.executable), 'config.ini')
    else:
        config_path = os.path.join(base_path, 'config.ini')
    
    if not os.path.exists(config_path):
        config['Settings'] = {
            'SERVER_URL': 'http://127.0.0.1:22233/update_pc_status',
            'SECRET': 'yoursecret',
            'START_SILENTLY': 'False'
        }
        try:
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            messagebox.showinfo("信息", "config.ini 未找到，已使用默认值创建。")
        except Exception as e:
            messagebox.showerror("错误", f"创建 config.ini 失败: {e}")
            exit(1)
    
    config.read(config_path)
    SERVER_URL = config.get('Settings', 'SERVER_URL', fallback='http://127.0.0.1:22233/update_pc_status')
    SECRET = config.get('Settings', 'SECRET', fallback='yoursecret')
    START_SILENTLY = config.getboolean('Settings', 'START_SILENTLY', fallback=False)

# Get the active window name (Windows)
def get_active_window_name():
    try:
        import win32gui
        window = win32gui.GetForegroundWindow()
        app_name = win32gui.GetWindowText(window)
        return app_name
    except ImportError:
        return "未知应用"

# Send request to server
def send_request(app_name, status_queue):
    try:
        response = requests.get(SERVER_URL, params={
            "secret": SECRET,
            "pc_app_name": app_name
        })
        if response.status_code == 200:
            status_queue.put(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 状态成功发送至 {SERVER_URL}: {app_name}\n")
        else:
            status_queue.put(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 发送失败至 {SERVER_URL}, 状态码: {response.status_code}\n")
    except Exception as e:
        status_queue.put(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 请求 {SERVER_URL} 失败: {e}\n")

# Monitor active application changes
def monitor_application(status_queue):
    global last_app_name
    while True:
        current_app_name = get_active_window_name()
        if current_app_name != last_app_name:
            status_queue.put(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 检测到应用切换: {current_app_name}\n")
            send_request(current_app_name, status_queue)
            last_app_name = current_app_name
        time.sleep(5)

# Get system idle time (in seconds)
def get_idle_time():
    idle_time = ctypes.c_uint()
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(idle_time))
    return idle_time.value

# Send periodic requests (every 2 minutes)
def send_periodic_request(status_queue):
    global last_sent_time
    while True:
        idle_time = get_idle_time()
        current_app_name = get_active_window_name()
        if idle_time < 120:
            current_time = time.time()
            if current_time - last_sent_time >= 120:
                status_queue.put(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 屏幕活动, 正在发送定期请求至 {SERVER_URL}...\n")
                send_request(current_app_name, status_queue)
                last_sent_time = current_time
        time.sleep(10)

# GUI Application class
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("状态监视器")
        self.root.geometry("400x300")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Create a hidden frame to keep Tkinter active
        self.hidden_frame = tk.Frame(root)
        self.hidden_frame.pack()

        # Set window icon
        icon_path = os.path.join(base_path, 'app_icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # Server URL label
        self.label_url = tk.Label(root, text=f"服务器 URL: {SERVER_URL}", font=("Microsoft YaHei", 10))
        self.label_url.pack(pady=5)

        # Secret label
        self.label_secret = tk.Label(root, text=f"密钥: {SECRET}", font=("Microsoft YaHei", 10))
        self.label_secret.pack(pady=5)

        # Status text area with resizing
        self.status_text = tk.Text(root, height=10, width=50, font=("Microsoft YaHei", 10))
        self.status_text.pack(pady=10, fill=tk.BOTH, expand=True)
        self.status_text.insert(tk.END, "应用程序已启动。\n")

        # Settings button in the upper right corner
        self.settings_button = tk.Button(root, text="设置", command=self.open_settings, font=("Microsoft YaHei", 10), width=10, height=2)
        self.settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        self.status_queue = queue.Queue()

        self.tray_icon = None
        self.tray_thread = None
        self.create_tray_icon()

        self.process_status_queue()

    def process_status_queue(self):
        try:
            while True:
                message = self.status_queue.get_nowait()
                self.status_text.insert(tk.END, message)
                self.status_text.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self.process_status_queue)

    def run_tray_icon(self):
        """Run the tray icon in a loop with error handling."""
        while True:
            try:
                icon_path = os.path.join(base_path, 'app_icon.ico')
                image = Image.open(icon_path) if os.path.exists(icon_path) else Image.new('RGB', (16, 16), color=(73, 109, 137))
                menu = Menu(
                    MenuItem('显示', self.show_window),
                    MenuItem('退出', self.quit_app)
                )
                self.tray_icon = Icon("状态监视器", image, menu=menu)
                print("Tray icon created, running...")
                self.tray_icon.run()
            except Exception as e:
                print(f"Tray icon error: {e}")
                time.sleep(2)  # Retry after delay

    def create_tray_icon(self):
        """Start the tray icon thread."""
        self.tray_thread = threading.Thread(target=self.run_tray_icon, daemon=True)
        self.tray_thread.start()
        print("Tray icon thread started.")

    def hide_window(self):
        """Hide the window but keep the hidden frame to maintain Tkinter activity."""
        self.root.withdraw()
        print("Window hidden, tray icon should remain visible.")

    def show_window(self, icon=None, item=None):
        """Show the window."""
        self.root.deiconify()

    def quit_app(self, icon=None, item=None):
        """Quit the application cleanly."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        os._exit(0)

    def open_settings(self):
        """Open the settings window."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("300x100")
        
        config = configparser.ConfigParser()
        config.read(config_path)
        start_silently = config.getboolean('Settings', 'START_SILENTLY', fallback=False)
        
        var = tk.BooleanVar(value=start_silently)
        
        checkbox = tk.Checkbutton(settings_window, text="静默启动（启动时不显示主窗口）", variable=var, font=("Microsoft YaHei", 10))
        checkbox.pack(pady=10)
        
        def save_setting():
            config['Settings']['START_SILENTLY'] = str(var.get())
            try:
                with open(config_path, 'w') as configfile:
                    config.write(configfile)
            except Exception as e:
                messagebox.showerror("错误", f"保存设置失败: {e}")
        
        var.trace('w', lambda *args: save_setting())
        
        close_button = tk.Button(settings_window, text="关闭", command=settings_window.destroy, font=("Microsoft YaHei", 10))
        close_button.pack(pady=5)

if __name__ == "__main__":
    load_config()

    root = tk.Tk()
    app = App(root)
    
    if START_SILENTLY:
        app.hide_window()

    thread_app_monitor = threading.Thread(target=monitor_application, args=(app.status_queue,), daemon=True)
    thread_app_monitor.start()

    thread_periodic_request = threading.Thread(target=send_periodic_request, args=(app.status_queue,), daemon=True)
    thread_periodic_request.start()

    root.mainloop()