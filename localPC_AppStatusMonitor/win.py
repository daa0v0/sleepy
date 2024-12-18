import time
import requests
import os

# 服务器配置
SERVER_URL = "http://127.0.0.1:22233/update_pc_status"
SECRET = "yoursecret"

# 获取当前前台应用名称 (Windows 示例)
def get_active_window_name():
    try:
        import win32gui  # 需要安装 pywin32
        window = win32gui.GetForegroundWindow()
        app_name = win32gui.GetWindowText(window)
        return app_name
    except ImportError:
        return "未知应用"

# 发送请求到服务器
def send_request(app_name):
    try:
        response = requests.get(SERVER_URL, params={
            "secret": SECRET,
            "pc_app_name": app_name
        })
        if response.status_code == 200:
            print(f"状态已发送成功: {app_name}")
        else:
            print(f"发送失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"请求失败: {e}")

# 检测前台应用变化并发送请求
def monitor_application():
    last_app_name = ""  # 保存上一次的应用名称
    while True:
        current_app_name = get_active_window_name()  # 获取当前应用名称
        if current_app_name != last_app_name:  # 检查是否切换了应用
            print(f"检测到应用切换: {current_app_name}")
            send_request(current_app_name)  # 发送请求到服务器
            last_app_name = current_app_name  # 更新上一次的应用名称

        time.sleep(10)  # 每1秒检测一次

if __name__ == "__main__":
    print("开始监控前台应用...")
    monitor_application()
