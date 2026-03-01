"""
技术面因子库

包含所有技术面因子的计算逻辑：
- 趋势因子：MA、EMA、MACD
- 动量因子：RSI、KDJ、WR
- 波动率因子：布林带、ATR、贪恐指数
- 量能因子：成交量比率、VR
"""

from typing import List, Optional
import pandas as pd
from stockstats import StockDataFrame

from ..core import FactorDetail
from ..core.constants import cfg
from .base import BaseFactor, FactorLibrary


class MAFactor(BaseFactor):
    """MA 均线因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """MA 均线因子分析：评估指标：MA5/MA20/MA60 多头/空头排列"""
        last_row = self.stock.iloc[-1]
        close = float(last_row.get("close", 0.0))
        bull, bear = [], []
        ma5 = last_row.get("close_5_sma", close)
        ma20 = last_row.get("close_20_sma", close)
        ma60 = last_row.get("close_60_sma", close)

        status = "震荡/不明确"

        if close > ma20 and ma20 > ma60:
            status = "📈 多头趋势 (中期看涨)"
            bull.append(self._create_signal("technical", "价格站上 MA20/MA60，趋势排列良好"))
        elif close < ma20 and ma20 < ma60:
            status = "📉 空头趋势 (中期看跌)"
            bear.append(self._create_signal("technical", "价格跌破 MA20/MA60，趋势走弱"))

        if close > ma5:
            bull.append(self._create_signal("technical", "价格站上 MA5"))
        else:
            bear.append(self._create_signal("technical", "价格跌破 MA5"))

        return FactorDetail(
            key="ma",
            name="MA均线",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class EMAFactor(BaseFactor):
    """EMA 指数均线因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """EMA 指数均线因子分析：评估指标：12日/26日 EMA 交叉信号"""
        last_row = self.stock.iloc[-1]
        close = float(last_row.get("close", 0.0))
        bull, bear = [], []
        ema12 = last_row.get("close_12_ema", close)
        ema26 = last_row.get("close_26_ema", close)

        if ema12 > ema26 * 1.01:
            status = "EMA 多头排列"
            bull.append(self._create_signal("technical", "12 日 EMA 上穿 26 日 EMA"))
        elif ema12 < ema26 * 0.99:
            status = "EMA 空头排列"
            bear.append(self._create_signal("technical", "12 日 EMA 跌破 26 日 EMA"))
        else:
            status = "EMA 震荡"

        return FactorDetail(
            key="ema",
            name="EMA指数均线",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class MACDFactor(BaseFactor):
    """MACD 因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """MACD 因子分析：评估指标：MACD 柱线（MACDH）方向与强度"""
        last_row = self.stock.iloc[-1]
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row
        bull, bear = [], []
        macd_h = last_row.get("macdh", 0.0)
        prev_macd_h = prev_row.get("macdh", macd_h)
        macd = last_row.get("macd", 0.0)

        if macd_h > 0 and macd_h >= prev_macd_h:
            status = "MACD 柱线抬升，动能增强"
            bull.append(self._create_signal("technical", "MACD 柱线抬升，动能增强"))
        elif macd_h < 0 and macd_h <= prev_macd_h:
            status = "MACD 柱线走弱，动能衰减"
            bear.append(self._create_signal("technical", "MACD 柱线走弱，动能衰减"))
        elif macd > 0:
            status = "MACD 主线为正，动能向上"
            bull.append(self._create_signal("technical", "MACD 主线为正，动能向上"))
        elif macd < 0:
            status = "MACD 主线为负，动能向下"
            bear.append(self._create_signal("technical", "MACD 主线为负，动能向下"))
        else:
            status = "MACD 中性"

        return FactorDetail(
            key="macd",
            name="MACD",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class RSIFactor(BaseFactor):
    """RSI 因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """RSI 因子分析：评估指标：RSI 相对强弱指标，超买超卖判断"""
        last_row = self.stock.iloc[-1]
        bull, bear = [], []
        rsi = last_row.get("rsi_14", 50.0)

        if 45 <= rsi <= 60:
            status = f"RSI 处于健康区间 ({rsi:.1f})"
        elif rsi < cfg.RSI_OVERSOLD:
            status = f"RSI 超卖 ({rsi:.1f})"
            bull.append(self._create_signal("technical", f"RSI 超卖 ({rsi:.1f})，反弹概率高"))
        elif rsi > cfg.RSI_OVERBOUGHT:
            status = f"RSI 超买 ({rsi:.1f})"
            bear.append(self._create_signal("technical", f"RSI 超买 ({rsi:.1f})，易回调"))
        else:
            status = f"RSI 正常 ({rsi:.1f})"

        return FactorDetail(
            key="rsi",
            name="RSI",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class KDJFactor(BaseFactor):
    """KDJ 因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """KDJ 因子分析：评估指标：KDJ 随机指标，J 线形态与 K/D 交叉信号"""
        last_row = self.stock.iloc[-1]
        bull, bear = [], []
        kdjk = last_row.get("kdjk", 50.0)
        kdjd = last_row.get("kdjd", 50.0)
        kdjj = last_row.get("kdjj", 50.0)

        if kdjk > kdjd and kdjj > kdjk:
            status = "KDJ 多头形态"
            bull.append(self._create_signal("technical", "KDJ 多头形态，J 线上穿"))
        elif kdjk < kdjd and kdjj < kdjd:
            status = "KDJ 空头形态"
            bear.append(self._create_signal("technical", "KDJ 空头形态，J 下穿"))
        else:
            status = "KDJ 震荡"

        return FactorDetail(
            key="kdj",
            name="KDJ",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class WRFactor(BaseFactor):
    """WR 威廉指标因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """WR 威廉指标因子分析：评估指标：短期超买超卖灵敏度高"""
        last_row = self.stock.iloc[-1]
        bull, bear = [], []
        wr = last_row.get("wr_14", -50.0)

        if wr <= -80:
            status = f"WR 进入底部区域 ({wr:.1f})"
            bull.append(self._create_signal("technical", f"WR 进入底部区域 ({wr:.1f})"))
        elif wr >= -20:
            status = f"WR 逼近顶部区域 ({wr:.1f})"
            bear.append(self._create_signal("technical", f"WR 逼近顶部区域 ({wr:.1f})"))
        else:
            status = f"WR 正常 ({wr:.1f})"

        return FactorDetail(
            key="wr",
            name="WR威廉指标",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class BollingerFactor(BaseFactor):
    """布林带因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """布林带因子分析：评估指标：布林带宽度和位置（%B）"""
        last_row = self.stock.iloc[-1]
        close = float(last_row.get("close", 0.0))
        bull, bear = [], []
        lb = last_row.get("boll_lb", close * 0.9)
        ub = last_row.get("boll_ub", close * 1.1)

        band_width = (ub - lb) / close if close > 0 and ub > lb else 0.0
        if 0.05 <= band_width <= 0.18:
            bull.append(self._create_signal("technical", "布林带宽度处于健康波动区间"))
            status = "布林带宽度正常"
        elif band_width < 0.05:
            bear.append(self._create_signal("technical", "波动率偏低，方向感不足"))
            status = "布林带宽度偏窄"
        else:
            bear.append(self._create_signal("technical", "波动率过高，短期风险放大"))
            status = "布林带宽度偏宽"

        if ub > lb:
            pct_b = self._clamp_ratio((close - lb) / (ub - lb))
        else:
            pct_b = 0.5
        if pct_b <= 0.2:
            bull.append(self._create_signal("technical", "价格贴近布林下轨，存在支撑"))
        elif pct_b >= 0.8:
            bear.append(self._create_signal("technical", "价格逼近布林上轨，压力较大"))

        return FactorDetail(
            key="bollinger",
            name="布林带",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class ATRFactor(BaseFactor):
    """ATR 真实波动幅度因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """ATR 真实波动幅度因子分析：评估指标：波动剧烈程度"""
        last_row = self.stock.iloc[-1]
        close = float(last_row.get("close", 0.0))
        bull, bear = [], []
        atr = last_row.get("atr", 0.0)
        atr_ratio = atr / close if close > 0 else 0.0

        if atr_ratio > 0.08:
            status = f"ATR 波动剧烈 ({atr_ratio:.2%})"
            bear.append(self._create_signal("technical", "ATR 显示波动剧烈，注意风险"))
        else:
            status = f"ATR 波动正常 ({atr_ratio:.2%})"

        return FactorDetail(
            key="atr",
            name="ATR",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class SentimentFactor(BaseFactor):
    """
    贪恐指数因子

    基于7个技术指标加权合成：
    - RSI (20%)、布林带 %B (20%)、WR (15%)、KDJ J值 (15%)
    - MACD 柱 (15%)、价格动量 (10%)、VR 量比 (5%)

    情绪等级：
    - 0-19: 极度恐慌（买入机会）
    - 20-39: 恐慌
    - 40-59: 中性
    - 60-79: 贪婪
    - 80-100: 极度贪婪（警惕回调）
    """

    def calculate(self, fg_index: float = 50.0, **kwargs) -> FactorDetail:
        """贪恐指数分析：评估指标：逆向情绪指标（恐慌买入/贪婪卖出）"""
        bull, bear = [], []

        if fg_index < 20:
            status = f"情绪极度恐慌 ({fg_index:.0f})"
            bull.append(
                self._create_signal("technical", f"情绪极度恐慌 ({fg_index:.0f})，具备逆向价值")
            )
        elif fg_index < 40:
            status = f"情绪恐慌 ({fg_index:.0f})"
        elif fg_index < 60:
            status = f"情绪中性 ({fg_index:.0f})"
        elif fg_index < 80:
            status = f"情绪贪婪 ({fg_index:.0f})"
        else:
            status = f"情绪极度贪婪 ({fg_index:.0f})"
            bear.append(
                self._create_signal("technical", f"情绪极度贪婪 ({fg_index:.0f})，警惕回调")
            )

        return FactorDetail(
            key="sentiment",
            name="贪恐指数",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class VolumeRatioFactor(BaseFactor):
    """成交量比率因子"""

    def calculate(
        self, volume_ma5: float = 0.0, volume_ma20: float = 0.0, **kwargs
    ) -> FactorDetail:
        """成交量比率因子分析：评估指标：当前成交量 vs 均量"""
        last_row = self.stock.iloc[-1]
        bull, bear = [], []
        current_volume = float(last_row.get("volume", volume_ma5))

        if volume_ma5 > 0:
            short_ratio = current_volume / volume_ma5
        else:
            short_ratio = 1.0

        if short_ratio >= 1.5:
            status = f"量能放大 ({short_ratio:.2f}x)"
            bull.append(self._create_signal("technical", "量能放大到 5 日均量 1.5 倍以上"))
        elif short_ratio <= 0.6:
            status = f"量能萎缩 ({short_ratio:.2f}x)"
            bear.append(self._create_signal("technical", "量能萎缩到 5 日均量 0.6 倍以下"))
        else:
            status = f"量能正常 ({short_ratio:.2f}x)"

        if volume_ma20 > 0:
            mid_ratio = volume_ma5 / volume_ma20
        else:
            mid_ratio = 1.0

        if mid_ratio >= 1.2:
            bull.append(self._create_signal("technical", "短期均量高于中期均量，资金净流入"))
        elif mid_ratio <= 0.8:
            bear.append(self._create_signal("technical", "短期均量低于中期均量，资金趋冷"))

        return FactorDetail(
            key="volume_ratio",
            name="成交量比率",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class VRFactor(BaseFactor):
    """VR 成交量比率因子"""

    def calculate(self, **kwargs) -> FactorDetail:
        """VR 成交量比率因子分析：评估指标：买盘/卖盘力量对比"""
        last_row = self.stock.iloc[-1]
        bull, bear = [], []
        vr = last_row.get("vr", 100.0)

        if vr >= 160:
            status = f"VR 买盘占优 ({vr:.0f})"
            bull.append(self._create_signal("technical", f"VR={vr:.0f}，买盘明显占优"))
        elif vr <= 70:
            status = f"VR 卖压大 ({vr:.0f})"
            bear.append(self._create_signal("technical", f"VR={vr:.0f}，抛压大于买盘"))
        else:
            status = f"VR 正常 ({vr:.0f})"

        return FactorDetail(
            key="vr",
            name="VR成交量比率",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )


class TechnicalFactorLibrary(FactorLibrary):
    """技术面因子库"""

    def get_factors(
        self,
        stock: StockDataFrame,
        raw_df: pd.DataFrame,
        fg_index: float = 50.0,
        volume_ma5: float = 0.0,
        volume_ma20: float = 0.0,
        **kwargs,
    ) -> List[FactorDetail]:
        """
        获取所有技术面因子

        Args:
            stock: StockDataFrame 对象
            raw_df: 原始行情数据 DataFrame
            fg_index: 贪恐指数
            volume_ma5: 5日成交量均线
            volume_ma20: 20日成交量均线
            data_source: 数据源标识
            raw_data: 原始数据
            **kwargs: 其他参数

        Returns:
            List[FactorDetail]: 技术面因子列表
        """
        factors = []

        # 趋势因子
        factors.append(MAFactor(stock, raw_df).calculate())
        factors.append(EMAFactor(stock, raw_df).calculate())
        factors.append(MACDFactor(stock, raw_df).calculate())

        # 动量因子
        factors.append(RSIFactor(stock, raw_df).calculate())
        factors.append(KDJFactor(stock, raw_df).calculate())
        factors.append(WRFactor(stock, raw_df).calculate())

        # 波动率因子
        factors.append(BollingerFactor(stock, raw_df).calculate())
        factors.append(ATRFactor(stock, raw_df).calculate())
        factors.append(SentimentFactor(stock, raw_df).calculate(fg_index=fg_index))

        # 量能因子
        factors.append(
            VolumeRatioFactor(stock, raw_df).calculate(
                volume_ma5=volume_ma5,
                volume_ma20=volume_ma20,
            )
        )
        factors.append(VRFactor(stock, raw_df).calculate())

        return factors
