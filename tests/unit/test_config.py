from app.config import settings


def test_settings_load():
    """Verify that settings are loaded correctly from environment/.env."""
    assert settings.LLM_MODEL == "glm-4.7-flash:latest"
    assert settings.TESSERACT_CMD is not None
    assert "mysql+pymysql://" in settings.database_url
