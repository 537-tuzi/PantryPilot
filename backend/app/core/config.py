"""应用配置。

所有配置来自环境变量或根目录 .env；密钥只存在服务端。
环境变量清单见 文档/08 §2。
"""

from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_DIR.parent

# 空值与脚手架中的占位符都不允许作为实际的 JWT 签名密钥。
_INSECURE_SECRET_KEYS = {"", "change-me-to-a-long-random-string"}


class Settings(BaseSettings):
    """运行期配置。"""

    # 按文档在 backend 目录启动时，也能读到仓库根目录的 .env；
    # backend/.env 若存在则优先，真实环境变量始终优先于文件。
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    app_env: str = "development"
    # 无默认值：缺失即校验失败，避免静默使用弱密钥。
    secret_key: str
    # 临期/过期状态按该时区的“今天”计算；用户表暂无时区字段。
    app_timezone: str = "Asia/Shanghai"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    database_url: str = "postgresql+psycopg://pantry:pantry@localhost:5432/pantrypilot"
    api_prefix: str = "/api/v1"

    # 模型 API（仅服务端）
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: int = 20

    # 允许来源，逗号分隔
    cors_origins: str = "http://localhost:5200,http://localhost"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """拒绝空值与占位密钥，防止默认配置被用于真实签名。"""
        if value.strip() in _INSECURE_SECRET_KEYS:
            raise ValueError("SECRET_KEY must be a strong, non-default value")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """解析允许来源列表。"""
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回进程级配置单例；密钥不安全时拒绝启动。"""
    try:
        return Settings()
    except ValidationError as exc:
        if any(error["loc"] and error["loc"][0] == "secret_key" for error in exc.errors()):
            raise RuntimeError(
                "配置错误：SECRET_KEY 缺失或仍为默认占位符。请在仓库根目录或 "
                "backend 目录的 .env 中配置强随机 SECRET_KEY 后重启服务。"
            ) from None
        raise


settings = get_settings()
