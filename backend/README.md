# 圣诞礼物匹配系统 - Backend

## 快速开始

```bash
cd backend
python3 app.py
```

启动后会显示交互式菜单：

```
    ╔══════════════════════════════════════════╗
    ║       圣诞礼物匹配系统                   ║
    ╚══════════════════════════════════════════╝

    [1] 演示模式    使用模拟数据测试匹配流程
    [2] 正式运行    从飞书读取数据并匹配
    [3] 邮件测试    验证邮件配置是否正确
    [4] 启动服务    启动 API 服务器
    [0] 退出
```

邮件发送需要两次确认，防止误发。

## 配置

复制 `.env.example` 为 `.env` 并填写：

```env
# AI
AI_API_KEY=xxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4

# 邮件
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your@qq.com
SMTP_PASSWORD=授权码
```

## 文件结构

```
backend/
├── run.py           # 统一入口
├── services.py      # 匹配算法核心
├── email_service.py # 邮件服务
├── feishu_reader.py # 飞书数据读取
├── models.py        # 数据模型
├── config.py        # 配置
└── main.py          # FastAPI 服务
```
