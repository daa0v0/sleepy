#!/usr/bin/python3
# coding: utf-8
import utils as u
from data import data as data_init
from flask import Flask, render_template, request, url_for, redirect, flash, make_response
from markupsafe import escape

#add_an
import time  # 引入时间模块
import threading  # 引入线程模块
from datetime import datetime  # 引入时间模块

# 记录最后一次请求时间
last_request_time = time.time()

# 线程锁，确保并发安全
status_lock = threading.Lock()

#add_an

d = data_init()
app = Flask(__name__)

# ---


def reterr(code, message):
    ret = {
        'success': False,
        'code': code,
        'message': message
    }
    u.error(f'{code} - {message}')
    return u.format_dict(ret)


def showip(req, msg):
    ip1 = req.remote_addr
    try:
        ip2 = req.headers['X-Forwarded-For']
        u.infon(f'- Request: {ip1} / {ip2} : {msg}')
    except:
        ip2 = None
        u.infon(f'- Request: {ip1} : {msg}')

@app.route('/')
def index():
    d.load()
    showip(request, '/')
    ot = d.data['other']
    try:
        # 获取手机和电脑状态
        an_stat = d.data['an_status_list'][d.data['an_status']].copy()
        pc_stat = d.data['pc_status_list'][d.data['pc_status']].copy()

        # 判断手机和电脑的状态
        if d.data['an_status'] == 0:  # 手机在线
            an_stat['name'] = an_stat['an_name']
        else:
            an_stat['name'] = "不在使用"

        if d.data['pc_status'] == 0:  # 电脑在线
            pc_stat['name'] = pc_stat['pc_name']
        else:
            pc_stat['name'] = "不在使用"

        # 合并描述逻辑
        if d.data['an_status'] == 1 and d.data['pc_status'] == 1:
            combined_desc = "睡似了或其他原因不在线，紧急情况请使用电话联系。"
        else:
            combined_desc = "目前设备上打开的应用，大概率在摸鱼。"

        # 更新时间，取手机和电脑的最新更新时间
        an_updated_at = an_stat.get('updated_at', '暂无更新')
        pc_updated_at = pc_stat.get('updated_at', '暂无更新')
        combined_updated_at = max(an_updated_at, pc_updated_at)  # 使用最新的时间

    except Exception as e:
        # 异常处理
        an_stat = {"name": "未知", "an_color": "error"}
        pc_stat = {"name": "未知", "pc_color": "error"}
        combined_desc = "状态未知，请稍后再试。"
        combined_updated_at = "暂无更新"

    # 渲染模板
    return render_template(
        'index.html',
        user=ot['user'],
        learn_more=ot['learn_more'],
        repo=ot['repo'],
        phone_status_name=an_stat['name'],  # 手机状态
        phone_status_color=an_stat['an_color'],  # 手机状态颜色
        pc_status_name=pc_stat['name'],  # 电脑状态
        pc_status_color=pc_stat['pc_color'],  # 电脑状态颜色
        combined_desc=combined_desc,  # 合并后的描述
        updated_at=f"上次更新: {combined_updated_at}",
        more_text=ot['more_text']
    )


@app.route('/style.css')
def style_css():
    response = make_response(render_template(
        'style.css',
        bg=d.data['other']['background'],
        alpha=d.data['other']['alpha']
    ))
    response.mimetype = 'text/css'
    return response


@app.route('/query')
def query():
    d.load()
    showip(request, '/query')
    try:
        # 获取手机和电脑状态
        an_stat = d.data['an_status_list'][d.data['an_status']].copy()
        pc_stat = d.data['pc_status_list'][d.data['pc_status']].copy()

        ret = {
            "success": True,
            "an_status": d.data['an_status'],
            "an_name": an_stat['an_name'],
            "pc_status": d.data['pc_status'],
            "pc_name": pc_stat['pc_name']
        }
    except Exception as e:
        ret = {
            "success": False,
            "message": str(e)
        }
    return u.format_dict(ret)


@app.route('/get/status_list')
def get_status_list():
    showip(request, '/get/status_list')
    stlst = d.dget('status_list')
    return u.format_dict(stlst)


@app.route('/set')
def set_normal():
    showip(request, '/set')
    status = escape(request.args.get("status"))
    app_name = escape(request.args.get("app_name"))
    if not status.isdigit():
        status = None
    if app_name == "" or app_name == "None":
        app_name = None
    pc_status = escape(request.args.get("pc_status"))
    pc_app_name = escape(request.args.get("pc_app_name"))
    if not pc_status.isdigit():
        pc_status = None
    if pc_app_name == "" or pc_app_name == "None":
        pc_app_name = None
    secret = escape(request.args.get("secret"))
    u.info(f'status: {status}, name: {app_name}, secret: "{secret}", pc_status: {pc_status}, pc_name: {pc_app_name}')
    print(f'status: {status}, name: {app_name}, secret: "{secret}", pc_status: {pc_status}, pc_name: {pc_app_name}')
    secret_real = d.dget('secret')
    if secret == secret_real:
        if status is not None:
            d.dset('status', int(status))
        if app_name is not None:
            d.dset('app_name', app_name)
        if pc_status is not None:
            d.dset('pc_status', int(pc_status))
        if pc_app_name is not None:
            d.dset('pc_app_name', pc_app_name)
        u.info('set success')
        ret = {
            'success': True,
            'code': 'OK',
            'set_to': status,
            'app_name':app_name,
            'pc_set_to': pc_status,
            'pc_app_name': pc_app_name
        }
        return u.format_dict(ret)
    else:
        return reterr(
            code='not authorized',
            message='invaild secret'
        )

#add_pc
@app.route('/update_pc_status', methods=['GET'])
def update_pc_status():
    global last_request_time
    with status_lock:
        secret = escape(request.args.get("secret"))
        pc_app_name = escape(request.args.get("pc_app_name"))

        if secret != d.data['secret']:
            return reterr(code="unauthorized", message="Invalid secret")

        if pc_app_name:
            for item in d.data['pc_status_list']:
                if item['id'] == 0:
                    item['pc_name'] = pc_app_name
                    item['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 24小时制时间
                    break

        d.dset('pc_status', 0)
        last_request_time = time.time()
        return {"success": True, "updated_pc_status": 0, "updated_pc_name_in_list": pc_app_name}

#add_pc


#add_an

@app.route('/update_status', methods=['GET'])
def update_status():
    global last_request_time
    with status_lock:
        secret = escape(request.args.get("secret"))
        app_name = escape(request.args.get("app_name"))
        status = escape(request.args.get("status"))

        if secret != d.data['secret']:
            return reterr(code="unauthorized", message="Invalid secret")

        if app_name:
            for item in d.data['an_status_list']:
                if item['id'] == 0:
                    item['an_name'] = app_name
                    item['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 24小时制时间
                    break

        if status and status.isdigit():
            d.dset('an_status', int(status))

        last_request_time = time.time()
        return {"success": True, "updated_status": status, "updated_an_name_in_list": app_name}

#add
# 定时检查是否超时
def check_timeout():
    global last_request_time
    while True:
        with status_lock:
            current_time = time.time()
            # 如果超过10分钟（600秒）没有收到请求，设置状态
            if current_time - last_request_time > 150:
                d.dset('an_status', 1)
                d.dset('pc_status', 1)  # 同时检查 PC 状态
        time.sleep(60)  # 每60秒检查一次
#add

# 启动后台线程检查超时
timeout_thread = threading.Thread(target=check_timeout, daemon=True)
timeout_thread.start()

#add_an

if __name__ == '__main__':
    d.load()
    app.run(
        host=d.data['host'],
        port=d.data['port'],
        debug=d.data['debug']
    )

