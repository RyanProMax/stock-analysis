"""
环境配置工具模块

提供统一的环境判断函数，用于区分开发环境和生产环境。
"""

import os


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
