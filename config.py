import os

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Settings:
    API_KEY = os.getenv("AI_API_KEY")
    BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-4o")

settings = Settings()
