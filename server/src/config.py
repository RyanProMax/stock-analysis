"""
全局配置模块

提供统一的配置管理和环境判断功能。
"""

import os
from typing import Optional


def get_env_value() -> str:
    """
    获取环境变量值（ENV 或 ENVIRONMENT），转换为小写。

    Returns:
        str: 环境变量值的小写形式，如果都不存在则返回空字符串
    """
    return os.environ.get("ENV", os.environ.get("ENVIRONMENT", "")).lower()


def is_development() -> bool:
    """
    判断是否为开发环境。

    开发环境的判断条件：
    - ENV 或 ENVIRONMENT 环境变量为 "development" 或 "dev"
    - DEBUG 环境变量为 "true"

    Returns:
        bool: 如果是开发环境返回 True，否则返回 False
    """
    env_value = get_env_value()
    return env_value in ("development", "dev") or os.environ.get("DEBUG", "").lower() == "true"


def is_production() -> bool:
    """
    判断是否为生产环境。

    生产环境的判断条件：
    - ENV 或 ENVIRONMENT 环境变量为 "production" 或 "prod"

    Returns:
        bool: 如果是生产环境返回 True，否则返回 False
    """
    env_value = get_env_value()
    return env_value in ("production", "prod")


class Config:
    """
    全局配置类（单例模式）

    管理所有配置项，包括：
    - 环境判断
    - API 密钥
    - 数据源配置
    """

    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_config()

    def _load_config(self):
        """从环境变量加载配置"""
        # LLM 配置
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
        self.openai_base_url: str = os.environ.get("OPENAI_BASE_URL", "")
        self.deepseek_api_key: str = os.environ.get("DEEPSEEK_API_KEY", "")

        # 数据源配置
        self.tushare_token: str = os.environ.get("TUSHARE_TOKEN", "")

        # 服务配置
        self.port: int = int(os.environ.get("PORT", "8080"))

    @property
    def env(self) -> str:
        """当前环境"""
        return get_env_value()

    @property
    def is_dev(self) -> bool:
        """是否为开发环境"""
        return is_development()

    @property
    def is_prod(self) -> bool:
        """是否为生产环境"""
        return is_production()


# 全局配置实例
config = Config()
