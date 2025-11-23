import akshare as ak
import pandas as pd
from typing import Optional


class DataLoader:
    @staticmethod
    def get_stock_daily(symbol: str) -> Optional[pd.DataFrame]:
        """
        获取指定股票的日线数据 (前复权)
        :param symbol: 股票代码 (如 "600519")
        :return: 清洗后的 DataFrame 或 None
        """
        print(f"📡 正在从 AkShare 获取 [{symbol}] 数据...")
        try:
            # fetch data
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")

            if df.empty:
                print(f"❌ 未找到股票 {symbol} 的数据，请检查代码。")
                return None

            # stockstats 需要特定的列名，所以在这里进行重命名
            df.rename(
                columns={
                    "日期": "date",
                    "股票代码": "symbol",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "振幅": "amplitude",
                    "涨跌幅": "chg_pct",
                    "涨跌额": "chg_amt",
                    "换手率": "turnover_rate",
                },
                inplace=True,
            )

            # 格式化日期索引
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            return df
        except Exception as e:
            print(f"❌ 数据获取发生异常: {e}")
            return None
