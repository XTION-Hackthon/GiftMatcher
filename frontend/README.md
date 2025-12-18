# 圣诞礼物交换系统 - 前端

这是圣诞礼物交换系统的前端部分，用于收集用户信息并存入飞书多维表格。

## 项目结构

```
frontend/
├── index.html          # 主页面（单页应用）
├── api/
│   └── index.py        # Flask API 服务（用于提交数据到飞书）
├── vercel.json         # Vercel 部署配置
├── requirements.txt    # Python 依赖
└── *.png               # 图片资源
```

## 技术栈

- **前端**: 原生 HTML + TailwindCSS + JavaScript
- **后端 API**: Flask + Flask-CORS
- **数据存储**: 飞书多维表格

## 功能说明

1. **用户信息收集**: 收集参与者的姓名、邮箱、微信、MBTI 等信息
2. **礼物描述**: 用户填写准备的礼物描述
3. **问卷调查**: 收集用户的偏好问卷答案
4. **数据提交**: 将收集的数据提交到飞书多维表格

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动本地服务器

```bash
python api/index.py
```

启动后访问: `http://localhost:5000`

## Vercel 部署

项目已配置 Vercel 部署，直接推送到 Git 仓库即可自动部署。

### 部署配置

`vercel.json` 配置了 API 路由重写：
- `/api/*` 请求会被转发到 `api/index.py`

## 飞书配置

API 服务会将用户数据提交到飞书多维表格，配置信息在 `api/index.py` 中：

```python
FEISHU_CONFIG = {
    "app_id": "cli_a8088174413b900b",
    "app_secret": "...",
    "app_token": "T2WsbFLR3aNNnlscrQCchqjGn7c",
    "table_id": "tblZPt93lnlPzIM8"
}
```

## 图片资源

| 文件名 | 用途 |
| :--- | :--- |
| background.png | 页面背景图 |
| tree_bg.png | 圣诞树背景 |
| vibehacks_logo.png | Logo 图片 |
| x_mark.png | 关闭按钮图标 |
| 其他 .png | 装饰图片 |

## 数据流程

1. 用户在前端页面填写信息
2. 点击提交后，数据发送到 `/api/submit` 接口
3. Flask API 获取飞书 `tenant_access_token`
4. 将数据写入飞书多维表格
5. 返回提交结果给前端

## 与后端配合

前端收集完所有用户数据后，后端可以通过 CLI 命令读取飞书表格并运行匹配分析：

```bash
cd ../backend
python cli.py analyze
```
