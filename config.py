import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    import os
from datetime import timedelta


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:4200"
    ).split(",")

