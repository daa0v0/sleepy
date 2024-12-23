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

        time.sleep(5)  # 每5秒检测一次

# 获取系统空闲时间（单位：秒）
def get_idle_time():
    # 获取系统空闲时间
    idle_time = ctypes.c_uint()
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(idle_time))
    idle_time = idle_time.value
    return idle_time

# 定时发送请求（每2分钟发送一次请求）
def send_periodic_request():
    last_sent_time = 0  # 上次请求的时间戳
    while True:
        idle_time = get_idle_time()  # 获取系统空闲时间
        current_app_name = get_active_window_name()  # 获取当前应用名称
        if idle_time < 120:  # 如果系统空闲时间小于 2 分钟（120秒），说明屏幕处于活跃状态
            current_time = time.time()
            if current_time - last_sent_time >= 120:  # 如果已经过了 2 分钟
                print("屏幕处于活动状态，发送定时请求...")
                send_request(current_app_name)  # 可以自定义发送的应用名称，这里用 "屏幕活动"
                last_sent_time = current_time  # 更新上次发送请求的时间
        time.sleep(10)  # 每 10 秒检查一次空闲时间

if __name__ == "__main__":
    print("开始监控前台应用...")
    from threading import Thread

    # 启动监控前台应用的线程
    thread_app_monitor = Thread(target=monitor_application)
    thread_app_monitor.daemon = True
    thread_app_monitor.start()

    # 启动定时发送请求的线程
    thread_periodic_request = Thread(target=send_periodic_request)
    thread_periodic_request.daemon = True
    thread_periodic_request.start()

    # 防止主线程退出，保持程序运行
    while True:
        time.sleep(1)
