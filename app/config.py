from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables or .env file."""

    # Project directories
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    # LLM Settings
    LLM_PROVIDER: str = "openai_compatible"
    LLM_MODEL: str = "glm-4.7-flash:latest"
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    LLM_API_KEY: str = ""

    # Tesseract OCR Settings
    TESSERACT_CMD: Optional[str] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # MySQL Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "invoice_db"
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"

    # PO Line Item Matching Tolerances
    PO_PRICE_TOLERANCE: float = 0.01
    PO_TOTAL_TOLERANCE: float = 0.01
    PO_QUANTITY_TOLERANCE: float = 0.00

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def database_url(self) -> str:
        """Construct SQLAlchemy MySQL URL using PyMySQL driver."""
        escaped_pw = quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{escaped_pw}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
