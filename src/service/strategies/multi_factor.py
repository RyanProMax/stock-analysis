from stockstats import StockDataFrame
import pandas as pd

from ..model import cfg, AnalysisReport, FactorDetail
from ..report import print_report
from ..data_loader import DataLoader
from .base import BaseStockAnalyzer


class MultiFactorAnalyzer(BaseStockAnalyzer):
    """
    多因子股票分析策略（继承自 BaseStockAnalyzer）

    核心设计理念：
    1. 多因子分类：将指标分为趋势、波动率、动量、量能、基本面五大类
    2. 因子分类：技术面因子（趋势、波动率、动量、量能）和基本面因子（价值投资）
    3. 信号输出：每个因子独立输出多/空信号，便于理解分析来源

    技术面因子包括：
    - 趋势因子：MA/EMA/MACD 等趋势指标
    - 波动率因子：布林带、ATR、情绪指标等
    - 动量因子：RSI、KDJ、WR、MACD 等动量指标
    - 量能因子：成交量比率、均量等量能指标

    基本面因子包括：
    - 营收增长率：反映公司成长性
    - 资产负债率：反映财务健康度
    - 市盈率（PE）：反映估值水平
    - 市净率（PB）：反映资产价值
    - ROE（净资产收益率）：反映盈利能力

    这是默认的策略实现，后续可以扩展其他策略类（如机器学习策略、量化策略等）
    """

    # 需要计算的技术指标列表（按因子分类）
    INDICATORS_TO_CALCULATE = [
        # 趋势指标
        "macd",  # MACD 主线
        "macdh",  # MACD 柱线（用于趋势判断）
        "macds",  # MACD 信号线
        "close_12_ema",  # 12日指数均线
        "close_26_ema",  # 26日指数均线
        "close_5_sma",  # 5日简单均线
        "close_10_sma",  # 10日简单均线
        "close_20_sma",  # 20日简单均线
        "close_60_sma",  # 60日简单均线
        # 动量指标
        "rsi_14",  # 14日 RSI 相对强弱指标
        "kdjk",  # KDJ 指标 K 值
        "kdjd",  # KDJ 指标 D 值
        "kdjj",  # KDJ 指标 J 值
        "wr_14",  # 14日威廉指标
        # 波动率指标
        "boll",  # 布林带中轨
        "boll_ub",  # 布林带上轨
        "boll_lb",  # 布林带下轨
        "atr",  # 真实波动幅度（用于止损计算）
        # 量能指标
        "vr",  # 成交量比率
        "volume",  # 成交量
    ]

    def __init__(self, df: pd.DataFrame, symbol: str, stock_name: str):
        """
        初始化多因子分析器

        Args:
            df: 股票行情数据 DataFrame
            symbol: 股票代码
            stock_name: 股票名称
        """
        # 调用父类初始化，进行输入验证
        super().__init__(df, symbol, stock_name)

        # 初始化技术指标计算引擎
        self.stock = StockDataFrame.retype(self.raw_df.copy())

        # 计算所需的技术指标
        for indicator in self.INDICATORS_TO_CALCULATE:
            self.stock.get(indicator)

    @staticmethod
    def _create_signal(signal_type: str, message: str) -> dict:
        """
        创建信号字典

        Args:
            signal_type: 信号类型，"fundamental"（基本面）或 "technical"（技术面）
            message: 信号内容

        Returns:
            包含 type 和 message 的字典
        """
        return {"type": signal_type, "message": message}

    def _analyze_trend(self, last_row, prev_row, close: float) -> FactorDetail:
        """
        趋势因子分析

        评估指标：
        - MA 均线系统：MA5/MA20/MA60 多头/空头排列
        - EMA 指数均线：12日/26日 EMA 交叉信号
        - MACD 动能：柱线（MACDH）方向与强度
        """
        bull, bear = [], []
        ma5 = last_row.get("close_5_sma", close)
        ma20 = last_row.get("close_20_sma", close)
        ma60 = last_row.get("close_60_sma", close)

        trend_status = "震荡/不明确"

        if close > ma20 and ma20 > ma60:
            trend_status = "📈 多头趋势 (中期看涨)"
            bull.append(
                self._create_signal("technical", "价格站上 MA20/MA60，趋势排列良好")
            )
        elif close < ma20 and ma20 < ma60:
            trend_status = "📉 空头趋势 (中期看跌)"
            bear.append(
                self._create_signal("technical", "价格跌破 MA20/MA60，趋势走弱")
            )

        if close > ma5:
            bull.append(self._create_signal("technical", "价格站上 MA5"))
        else:
            bear.append(self._create_signal("technical", "价格跌破 MA5"))

        ema12 = last_row.get("close_12_ema", close)
        ema26 = last_row.get("close_26_ema", close)
        if ema12 > ema26 * 1.01:
            bull.append(self._create_signal("technical", "12 日 EMA 上穿 26 日 EMA"))
        elif ema12 < ema26 * 0.99:
            bear.append(self._create_signal("technical", "12 日 EMA 跌破 26 日 EMA"))

        macd_h = last_row.get("macdh", 0.0)
        prev_macd_h = prev_row.get("macdh", macd_h)
        if macd_h > 0 and macd_h >= prev_macd_h:
            bull.append(self._create_signal("technical", "MACD 柱线抬升，动能增强"))
        elif macd_h < 0 and macd_h <= prev_macd_h:
            bear.append(self._create_signal("technical", "MACD 柱线走弱，动能衰减"))

        factor_detail = FactorDetail(
            name="趋势因子",
            category="技术面",
            status=trend_status,
            bullish_signals=bull,
            bearish_signals=bear,
        )
        return factor_detail

    def _analyze_volatility(
        self, last_row, close: float, fg_index: float
    ) -> FactorDetail:
        """
        波动率因子分析

        评估指标：
        - 布林带宽度：衡量波动率健康度（5%-18% 为理想区间）
        - 布林带位置（%B）：价格在通道内的相对位置（下轨支撑/上轨压力）
        - ATR 真实波动幅度：评估波动剧烈程度
        - 贪恐指数：逆向情绪指标（恐慌买入/贪婪卖出）
        """
        bull, bear = [], []
        lb = last_row.get("boll_lb", close * 0.9)
        ub = last_row.get("boll_ub", close * 1.1)

        band_width = (ub - lb) / close if close > 0 and ub > lb else 0.0
        if 0.05 <= band_width <= 0.18:
            bull.append(self._create_signal("technical", "布林带宽度处于健康波动区间"))
        elif band_width < 0.05:
            bear.append(self._create_signal("technical", "波动率偏低，方向感不足"))
        else:
            bear.append(self._create_signal("technical", "波动率过高，短期风险放大"))

        if ub > lb:
            pct_b = self._clamp_ratio((close - lb) / (ub - lb))
        else:
            pct_b = 0.5
        if pct_b <= 0.2:
            bull.append(self._create_signal("technical", "价格贴近布林下轨，存在支撑"))
        elif pct_b >= 0.8:
            bear.append(self._create_signal("technical", "价格逼近布林上轨，压力较大"))

        atr = last_row.get("atr", 0.0)
        atr_ratio = atr / close if close > 0 else 0.0
        if atr_ratio > 0.08:
            bear.append(self._create_signal("technical", "ATR 显示波动剧烈，注意风险"))

        if fg_index <= 20:
            bull.append(
                self._create_signal(
                    "technical", f"情绪极度恐慌 ({fg_index:.0f})，具备逆向价值"
                )
            )
        elif fg_index >= 80:
            bear.append(
                self._create_signal(
                    "technical", f"情绪极度贪婪 ({fg_index:.0f})，警惕回调"
                )
            )

        status = "波动率正常" if 0.05 <= band_width <= 0.18 else "波动率异常"
        return FactorDetail(
            name="波动率因子",
            category="技术面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )

    def _analyze_momentum(self, last_row) -> FactorDetail:
        """
        动量因子分析

        评估指标：
        - RSI 相对强弱指标：超买超卖判断（45-60 为最佳区间）
        - KDJ 随机指标：J 线形态与 K/D 交叉信号
        - WR 威廉指标：短期超买超卖灵敏度高
        - MACD 主线：趋势动能方向（正值看多/负值看空）
        """
        bull, bear = [], []

        rsi = last_row.get("rsi_14", 50.0)
        if 45 <= rsi <= 60:
            status = f"RSI 处于健康区间 ({rsi:.1f})"
        elif rsi < cfg.RSI_OVERSOLD:
            status = f"RSI 超卖 ({rsi:.1f})"
            bull.append(
                self._create_signal("technical", f"RSI 超卖 ({rsi:.1f})，反弹概率高")
            )
        elif rsi > cfg.RSI_OVERBOUGHT:
            status = f"RSI 超买 ({rsi:.1f})"
            bear.append(
                self._create_signal("technical", f"RSI 超买 ({rsi:.1f})，易回调")
            )
        else:
            status = f"RSI 正常 ({rsi:.1f})"

        kdjk = last_row.get("kdjk", 50.0)
        kdjd = last_row.get("kdjd", 50.0)
        kdjj = last_row.get("kdjj", 50.0)
        if kdjk > kdjd and kdjj > kdjk:
            bull.append(self._create_signal("technical", "KDJ 多头形态，J 线上穿"))
        elif kdjk < kdjd and kdjj < kdjd:
            bear.append(self._create_signal("technical", "KDJ 空头形态，J 下穿"))

        wr = last_row.get("wr_14", -50.0)
        if wr <= -80:
            bull.append(self._create_signal("technical", f"WR 进入底部区域 ({wr:.1f})"))
        elif wr >= -20:
            bear.append(self._create_signal("technical", f"WR 逼近顶部区域 ({wr:.1f})"))

        macd = last_row.get("macd", 0.0)
        if macd > 0:
            bull.append(self._create_signal("technical", "MACD 主线为正，动能向上"))
        elif macd < 0:
            bear.append(self._create_signal("technical", "MACD 主线为负，动能向下"))

        return FactorDetail(
            name="动量因子",
            category="技术面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )

    def _analyze_volume(
        self, last_row, volume_ma5: float, volume_ma20: float
    ) -> FactorDetail:
        """
        量能因子分析

        评估指标：
        - 短期量能比：当前成交量 vs 5日均量（1.5倍以上为放量）
        - 中期量能比：5日均量 vs 20日均量（判断资金流入趋势）
        - VR 成交量比率：买盘/卖盘力量对比（>160 买盘占优，<70 卖压大）
        """
        bull, bear = [], []

        current_volume = float(last_row.get("volume", volume_ma5))
        if volume_ma5 > 0:
            short_ratio = current_volume / volume_ma5
        else:
            short_ratio = 1.0

        if short_ratio >= 1.5:
            status = f"量能放大 ({short_ratio:.2f}x)"
            bull.append(
                self._create_signal("technical", "量能放大到 5 日均量 1.5 倍以上")
            )
        elif short_ratio <= 0.6:
            status = f"量能萎缩 ({short_ratio:.2f}x)"
            bear.append(
                self._create_signal("technical", "量能萎缩到 5 日均量 0.6 倍以下")
            )
        else:
            status = f"量能正常 ({short_ratio:.2f}x)"

        if volume_ma20 > 0:
            mid_ratio = volume_ma5 / volume_ma20
        else:
            mid_ratio = 1.0

        if mid_ratio >= 1.2:
            bull.append(
                self._create_signal("technical", "短期均量高于中期均量，资金净流入")
            )
        elif mid_ratio <= 0.8:
            bear.append(
                self._create_signal("technical", "短期均量低于中期均量，资金趋冷")
            )

        vr = last_row.get("vr", 100.0)
        if vr >= 160:
            bull.append(self._create_signal("technical", f"VR={vr:.0f}，买盘明显占优"))
        elif vr <= 70:
            bear.append(self._create_signal("technical", f"VR={vr:.0f}，抛压大于买盘"))

        return FactorDetail(
            name="量能因子",
            category="技术面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )

    def _analyze_fundamental(self, financial_data: dict | None) -> FactorDetail:
        """
        价值投资因子分析（基本面分析）

        评估指标：
        - 营收增长率：反映公司成长性（>20% 优秀，<0% 衰退）
        - 资产负债率：反映财务健康度（<50% 健康，>70% 风险高）
        - 市盈率（PE）：反映估值水平（<15 低估，>30 高估）
        - 市净率（PB）：反映资产价值（<1 低估，>3 高估）
        - ROE（净资产收益率）：反映盈利能力（>15% 优秀，<5% 较差）
        """
        bull, bear = [], []
        status_parts = []

        if financial_data is None or not financial_data:
            # 财务数据不可用时，返回空因子详情
            return FactorDetail(
                name="价值投资因子",
                category="基本面",
                status="财务数据不可用",
                bullish_signals=[],
                bearish_signals=[],
            )

        # 1. 营收增长率
        revenue_growth = financial_data.get("revenue_growth")
        if revenue_growth is not None:
            if revenue_growth > 20:
                bull.append(
                    self._create_signal(
                        "fundamental",
                        f"营收增长强劲 ({revenue_growth:.1f}%)，成长性优秀",
                    )
                )
                status_parts.append(f"营收增长{revenue_growth:.1f}%")
            elif revenue_growth > 10:
                bull.append(
                    self._create_signal(
                        "fundamental", f"营收稳定增长 ({revenue_growth:.1f}%)"
                    )
                )
                status_parts.append(f"营收增长{revenue_growth:.1f}%")
            elif revenue_growth > 0:
                status_parts.append(f"营收增长{revenue_growth:.1f}%")
            elif revenue_growth > -10:
                bear.append(
                    self._create_signal(
                        "fundamental", f"营收增长放缓 ({revenue_growth:.1f}%)"
                    )
                )
                status_parts.append(f"营收增长{revenue_growth:.1f}%")
            else:
                bear.append(
                    self._create_signal(
                        "fundamental", f"营收负增长 ({revenue_growth:.1f}%)，经营承压"
                    )
                )
                status_parts.append(f"营收增长{revenue_growth:.1f}%")

        # 2. 资产负债率（越低越好）
        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is not None:
            if debt_ratio < 30:
                bull.append(
                    self._create_signal(
                        "fundamental", f"负债率低 ({debt_ratio:.1f}%)，财务结构健康"
                    )
                )
                status_parts.append(f"负债率{debt_ratio:.1f}%")
            elif debt_ratio < 50:
                bull.append(
                    self._create_signal(
                        "fundamental", f"负债率适中 ({debt_ratio:.1f}%)"
                    )
                )
                status_parts.append(f"负债率{debt_ratio:.1f}%")
            elif debt_ratio < 70:
                status_parts.append(f"负债率{debt_ratio:.1f}%")
            else:
                bear.append(
                    self._create_signal(
                        "fundamental", f"负债率偏高 ({debt_ratio:.1f}%)，财务风险需关注"
                    )
                )
                status_parts.append(f"负债率{debt_ratio:.1f}%")

        # 3. 市盈率（越低越好，但需结合行业）
        pe_ratio = financial_data.get("pe_ratio")
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < 10:
                bull.append(
                    self._create_signal(
                        "fundamental", f"PE={pe_ratio:.1f}，估值偏低，合理范围是 10-20"
                    )
                )
                status_parts.append(f"PE={pe_ratio:.1f}")
            elif pe_ratio < 20:
                bull.append(
                    self._create_signal(
                        "fundamental", f"PE={pe_ratio:.1f}，估值合理，合理范围是 10-20"
                    )
                )
                status_parts.append(f"PE={pe_ratio:.1f}")
            elif pe_ratio < 30:
                status_parts.append(f"PE={pe_ratio:.1f}")
            elif pe_ratio < 50:
                bear.append(
                    self._create_signal(
                        "fundamental", f"PE={pe_ratio:.1f}，估值偏高，合理范围是 10-20"
                    )
                )
                status_parts.append(f"PE={pe_ratio:.1f}")
            else:
                bear.append(
                    self._create_signal(
                        "fundamental", f"PE={pe_ratio:.1f}，估值过高，合理范围是 10-20"
                    )
                )
                status_parts.append(f"PE={pe_ratio:.1f}")

        # 4. 市净率（越低越好）
        pb_ratio = financial_data.get("pb_ratio")
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio < 1:
                bull.append(
                    self._create_signal(
                        "fundamental", f"PB={pb_ratio:.2f}，估值偏低，合理范围是 1-2"
                    )
                )
                status_parts.append(f"PB={pb_ratio:.2f}")
            elif pb_ratio < 2:
                bull.append(
                    self._create_signal(
                        "fundamental", f"PB={pb_ratio:.2f}，估值合理，合理范围是 1-2"
                    )
                )
                status_parts.append(f"PB={pb_ratio:.2f}")
            elif pb_ratio < 3:
                status_parts.append(f"PB={pb_ratio:.2f}")
            else:
                bear.append(
                    self._create_signal(
                        "fundamental", f"PB={pb_ratio:.2f}，估值偏高，合理范围是 1-2"
                    )
                )
                status_parts.append(f"PB={pb_ratio:.2f}")

        # 5. ROE（越高越好）
        roe = financial_data.get("roe")
        if roe is not None:
            if roe > 20:
                bull.append(
                    self._create_signal(
                        "fundamental", f"ROE优秀 ({roe:.1f}%)，盈利能力强劲"
                    )
                )
                status_parts.append(f"ROE={roe:.1f}%")
            elif roe > 15:
                bull.append(self._create_signal("fundamental", f"ROE良好 ({roe:.1f}%)"))
                status_parts.append(f"ROE={roe:.1f}%")
            elif roe > 10:
                status_parts.append(f"ROE={roe:.1f}%")
            elif roe > 5:
                status_parts.append(f"ROE={roe:.1f}%")
            else:
                bear.append(
                    self._create_signal(
                        "fundamental", f"ROE偏低 ({roe:.1f}%)，盈利能力较弱"
                    )
                )
                status_parts.append(f"ROE={roe:.1f}%")

        status = " | ".join(status_parts) if status_parts else "数据完整"
        return FactorDetail(
            name="价值投资因子",
            category="基本面",
            status=status,
            bullish_signals=bull,
            bearish_signals=bear,
        )

    def _calculate_fear_greed(self, row, close) -> tuple[float, str]:
        """
        计算个股贪恐指数（Fear & Greed Index）

        用途：衡量市场情绪，用于逆向策略（恐慌买入/贪婪卖出）
        范围：0-100（0=极度恐慌，100=极度贪婪）

        合成逻辑：
        - RSI 相对强弱指标（40%）：反映超买超卖状态
        - 布林带位置 %B（40%）：价格在通道内的相对位置
        - WR 威廉指标（20%）：短期超买超卖灵敏度

        注意：该指数用于波动率因子评分，而非独立因子
        """
        try:
            # 1. RSI (0-100)
            rsi = float(row.get("rsi_14", 50) or 50)

            # 2. 布林带位置 %B (归一化到 0-100)
            lb = float(row.get("boll_lb", close * 0.9) or (close * 0.9))
            ub = float(row.get("boll_ub", close * 1.1) or (close * 1.1))
            if ub != lb:
                pct_b = (close - lb) / (ub - lb) * 100
            else:
                pct_b = 50
            pct_b = max(0, min(100, pct_b))  # 截断极端值

            # 3. 威廉指标 WR (-100 到 0) -> 映射为 (0 到 100)
            wr = float(row.get("wr_14", -50) or -50)
            wr_score = wr + 100

            # 合成指数
            fg_index = (rsi * 0.4) + (pct_b * 0.4) + (wr_score * 0.2)

            # 生成标签
            if fg_index <= 20:
                label = "🥶 极度恐慌"
            elif fg_index <= 40:
                label = "😨 恐慌"
            elif fg_index <= 60:
                label = "😐 中性"
            elif fg_index <= 80:
                label = "🤤 贪婪"
            else:
                label = "🔥 极度贪婪"

            return fg_index, label
        except Exception as e:
            # 如果计算失败，返回默认值
            print(f"⚠️ 计算贪恐指数失败: {e}")
            return 50.0, "😐 中性"

    def analyze(self) -> AnalysisReport | None:
        """
        执行完整的股票技术分析流程

        核心流程：
        1. 提取最新行情数据和技术指标
        2. 获取财务数据（营收、负债、市盈率等）
        3. 计算贪恐指数（用于波动率因子）
        4. 分别分析五大因子（趋势/波动率/动量/量能/价值投资）
        5. 汇总各因子的多/空信号
        """
        last_row = self.stock.iloc[-1]
        prev_row = self.stock.iloc[-2] if len(self.stock) > 1 else last_row

        close = float(last_row.get("close", 0.0))
        if close == 0.0:
            return None

        # 计算贪恐指数（用于波动率因子）
        fg_index, fg_label = self._calculate_fear_greed(last_row, close)

        # 计算成交量均线（用于量能因子）
        volume_series = (
            self.raw_df["volume"]
            if "volume" in self.raw_df.columns
            else pd.Series([last_row.get("volume", 0)])
        )
        # 使用 ffill() 替代已弃用的 fillna(method="ffill")
        volume_series = volume_series.ffill().fillna(0)
        volume_ma5 = float(volume_series.tail(5).mean())
        volume_ma20 = (
            float(volume_series.tail(20).mean())
            if len(volume_series) >= 20
            else volume_ma5
        )

        # --- 获取财务数据（价值投资因子）---
        financial_data = None
        try:
            financial_data = DataLoader.get_financial_data(self.symbol)
        except Exception as e:
            import traceback

            print(f"⚠️ 获取财务数据失败: {e}")
            print("财务数据获取错误堆栈:")
            traceback.print_exc()

        # --- 五大因子分析 ---
        trend_factor = self._analyze_trend(last_row, prev_row, close)
        volatility_factor = self._analyze_volatility(last_row, close, fg_index)
        momentum_factor = self._analyze_momentum(last_row)
        volume_factor = self._analyze_volume(last_row, volume_ma5, volume_ma20)
        fundamental_factor = self._analyze_fundamental(financial_data)

        # --- 汇总多/空信号 ---
        bull_signals = (
            trend_factor.bullish_signals
            + volatility_factor.bullish_signals
            + momentum_factor.bullish_signals
            + volume_factor.bullish_signals
            + fundamental_factor.bullish_signals
        )
        bear_signals = (
            trend_factor.bearish_signals
            + volatility_factor.bearish_signals
            + momentum_factor.bearish_signals
            + volume_factor.bearish_signals
            + fundamental_factor.bearish_signals
        )

        final_cols = [
            c
            for c in ["open", "close", "high", "low", "volume"]
            + self.INDICATORS_TO_CALCULATE
            if c in self.stock.columns
        ]

        report = AnalysisReport(
            symbol=self.symbol,
            stock_name=self.stock_name,
            price=close,
            trend_status=trend_factor.status,
            data_and_indicators=self.stock[final_cols],
            trend_factor=trend_factor,
            volatility_factor=volatility_factor,
            momentum_factor=momentum_factor,
            volume_factor=volume_factor,
            fundamental_factor=fundamental_factor,
            bullish_signals=bull_signals,
            bearish_signals=bear_signals,
            fear_greed_index=fg_index,
            fear_greed_label=fg_label,
        )

        print_report(report)
        return report
