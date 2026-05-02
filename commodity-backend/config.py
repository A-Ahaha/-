import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # MySQL: mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@127.0.0.1:3306/commodity_quality?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRE_HOURS", "24")))

    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    # ABSA:
    # - USE_MOCK_ABSA=1 时不加载 transformers，走启发式
    USE_MOCK_ABSA = os.getenv("USE_MOCK_ABSA", "1").lower() in ("1", "true", "yes")
    ABSA_MODEL = os.getenv("ABSA_MODEL", "tabularisai/multilingual-sentiment-analysis")

    ABSA_MAX_COMMENTS = int(os.getenv("ABSA_MAX_COMMENTS", "800"))
    # CSV/采集导入默认走快速启发式；设为 1 时导入阶段也跑 Transformer（很慢）
    ABSA_IMPORT_USE_TRANSFORMER = os.getenv("ABSA_IMPORT_USE_TRANSFORMER", "0").lower() in ("1", "true", "yes")
