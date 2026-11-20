"""应用配置。

所有配置来自环境变量或根目录 .env；密钥只存在服务端。
环境变量清单见 文档/08 §2。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行期配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_env: str = "development"
    secret_key: str = "change-me-to-a-long-random-string"
    database_url: str = "postgresql+psycopg://pantry:pantry@localhost:5432/pantrypilot"
    api_prefix: str = "/api/v1"

    # 模型 API（仅服务端）
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 20

    # 允许来源，逗号分隔
    cors_origins: str = "http://localhost:5200,http://localhost"

    @property
    def cors_origin_list(self) -> list[str]:
        """解析允许来源列表。"""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回进程级配置单例。"""
    return Settings()


settings = get_settings()
