import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    posthog_api_key: str
    posthog_host: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    app_name: str
    database_path: str
    conversations_token: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            posthog_api_key=os.environ.get("POSTHOG_API_KEY", ""),
            posthog_host=os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com"),
            llm_api_key=os.environ.get("LLM_API_KEY", ""),
            llm_base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
            llm_model=os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
            app_name=os.environ.get("APP_NAME", "Hog Supply Co."),
            database_path=os.environ.get("DATABASE_PATH", "data/shop.db"),
            conversations_token=os.environ.get("POSTHOG_CONVERSATIONS_TOKEN", ""),
        )


settings = Settings.from_env()
