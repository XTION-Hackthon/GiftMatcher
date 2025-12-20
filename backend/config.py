import os

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    # AI 配置
    API_KEY = os.getenv("AI_API_KEY")
    BASE_URL = os.getenv("AI_BASE_URL")
    MODEL_NAME = os.getenv("AI_MODEL_NAME")
    
    # 飞书多维表格配置
    FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_a8088174413b900b")
    FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "RIQ9eph9dVicJfXseZjCE8ESUD2C8BmX")
    FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN", "T2WsbFLR3aNNnlscrQCchqjGn7c")
    FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblZPt93lnlPzIM8")
    FEISHU_TOKEN_REFRESH_THRESHOLD = 300  # 提前刷新阈值（秒），提前5分钟刷新
    
    # 邮件服务配置
    SMTP_HOST = os.getenv("SMTP_HOST", "")  # 如: smtp.qq.com, smtp.163.com
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # SSL端口通常为465
    SMTP_USER = os.getenv("SMTP_USER", "")  # 发件邮箱
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # 邮箱授权码（非登录密码）
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")  # 发件人地址，默认同SMTP_USER
    SENDER_NAME = os.getenv("SENDER_NAME", "圣诞礼物匹配系统")  # 发件人显示名称


settings = Settings()
