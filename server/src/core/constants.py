"""
配置常量定义

包含技术指标阈值等配置常量。
"""


class Config:
    """技术指标配置常量"""

    # RSI 阈值
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70

    # KDJ J 阈值
    KDJ_J_OVERSOLD = 10
    KDJ_J_OVERBOUGHT = 90


# 全局配置实例
cfg = Config()
