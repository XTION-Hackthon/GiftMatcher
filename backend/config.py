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


settings = Settings()
