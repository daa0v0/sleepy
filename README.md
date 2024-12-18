# sleepy

> 一个用于查看个人在线状态和设备操作状态的 Flask 页面应用，支持手机和电脑实时同步。是一个基于1812z的代码为基础的修改版本[1812z佬的github](https://github.com/1812z/sleepy)

让他人能看到你目前在线状态，让他人能知道你不在而不是故意鸟他/她。该项目支持手机和电脑设备的操作状态同步，并通过简单的网页展示。

[**演示**](#演示) / [**部署**](#部署) / [**使用**](#使用)

---

## 演示
演示站: [Here](http://host.cherryglaze.cn:22233/)

### 网页效果
- 实时显示手机和电脑的状态以及最近使用的应用
- 动态更新时间，并支持自动刷新
- 提供友好的状态和应用描述

![web-preview-1](img/web1.png)

![web-preview-2](img/web2.png)

---

## 部署

该项目支持 Python >= 3.6 的平台。

### 1. 克隆项目
从 GitHub 克隆项目：
```bash
git clone https://github.com/daa0v0/sleepy.git
```

或下载发布的压缩包并解压。

### 2. 安装依赖

进入项目目录，运行以下命令安装依赖：
```bash
pip install -r requirements.txt
```

### 3. 启动服务
运行 `server.py` 启动服务：
```bash
python3 server.py
```

启动后，访问 `http://127.0.0.1:2233` 查看效果。

---

## 使用

项目支持以下功能：
- 实时显示设备状态（手机和电脑）。
- 自动刷新页面，显示最新状态和更新时间。
- 支持通过 REST API 上报设备状态。

### 配置文件

第一次启动时，程序会自动生成 `data.json` 文件。编辑该文件可以配置以下内容：
- `an_status_list` 和 `pc_status_list`：定义手机和电脑的状态。
- `secret`：用于请求鉴权的密钥。

### 使用 REST API

项目提供了一系列 REST API，用于同步设备状态：

#### `/update_status`
更新手机的状态。

**请求格式**：
```bash
GET /update_status?secret=<secret>&app_name=<应用名>&status=<状态>
```

- `<secret>`：配置文件中的密钥。
- `<app_name>`：当前手机正在运行的应用名。
- `<status>`：手机状态（`0` 表示在线，`1` 表示离线）。

**返回示例**：
```json
{
    "success": true,
    "updated_status": "0",
    "updated_an_name_in_list": "微信",
    "combined_updated_at": "2024-12-18 20:16:18"
}
```

---

#### `/update_pc_status`
更新电脑的状态。

**请求格式**：
```bash
GET /update_pc_status?secret=<secret>&pc_app_name=<应用名>
```

- `<secret>`：配置文件中的密钥。
- `<pc_app_name>`：当前电脑正在运行的应用名。

**返回示例**：
```json
{
    "success": true,
    "updated_pc_status": 0,
    "updated_pc_name_in_list": "VS Code",
    "combined_updated_at": "2024-12-18 20:16:18"
}
```

---

#### `/query`
查询当前设备状态。

**请求格式**：
```bash
GET /query
```

**返回示例**：
```json
{
    "success": true,
    "an_status": 0,
    "an_name": "微信",
    "pc_status": 0,
    "pc_name": "VS Code",
    "combined_updated_at": "2024-12-18 20:16:18"
}
```

---

## 客户端配置

### 1. 手机客户端
使用 MacroDroid 配置自动化任务，将前台应用信息实时上报到服务器。

#### 示例配置
- **触发器**：前台应用变更。
- **动作**：通过 HTTP 请求调用 `/update_status` 接口，上传应用名和状态。

#### 下载示例配置
[下载 MacroDroid 配置文件](./前台应用状态.macro)

---

### 2. 电脑客户端
使用 PC 端脚本（如 `win.py`）实现应用状态实时同步。

#### 示例启动
运行以下脚本即可：
```bash
python3 win.py
```

---

## 注意事项

1. **开发模式**：目前使用 Flask 自带的开发服务器，建议在生产环境下使用 WSGI 服务器（如 gunicorn）。
2. **安全性**：请妥善保管 `data.json` 中的密钥信息，避免被他人恶意使用。
3. **兼容性**：项目支持所有现代浏览器，推荐使用最新版的 Chrome 或 Firefox。

---

## 示例状态

项目支持多种状态描述，以下是默认配置：

```json
"an_status": 0,
"an_app_name": "系统桌面",
"an_status_list": [
    {
        "id": 0,
        "an_name": "APP_AN",
        "an_desc": "目前手机使用的应用，大概率在玩手机摸鱼。",
        "an_color": "awake",
        "updated_at": "2024-12-18 20:48:20"
    },
    {
        "id": 1,
        "an_name": "似了",
        "an_desc": "睡似了或其他原因不在线，紧急情况请使用电话联系。",
        "an_color": "sleeping"
    }
],
"pc_status": 0,
"pc_app_name": "系统桌面",
"pc_status_list": [
    {
        "id": 0,
        "pc_name": "APP_PC",
        "pc_desc": "目前电脑使用的应用，大概率在打电动摸鱼。",
        "pc_color": "awake",
        "updated_at": "2024-12-18 20:49:29"
    },
    {
        "id": 1,
        "pc_name": "似了",
        "pc_desc": "睡似了或其他原因不在线，紧急情况请使用电话联系。",
        "pc_color": "sleeping"
    }
]
```

---

## 默认访问路径

| 路径            | 功能          |
|-----------------|-------------|
| `/`             | 显示主页       |
| `/query`        | 查询状态       |
| `/update_status`| 更新手机状态    |
| `/update_pc_status` | 更新电脑状态 |

---



