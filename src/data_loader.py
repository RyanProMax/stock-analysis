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
            # 1. 获取数据
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")

            if df.empty:
                print(f"❌ 未找到股票 {symbol} 的数据，请检查代码。")
                return None

            df_slice = df.iloc[:, :11].copy()

            # 2. 命名列
            df_slice.columns = [
                "date",
                "open",
                "close",
                "high",
                "low",
                "volume",
                "turnover",
                "amplitude",
                "chg_pct",
                "chg_amt",
                "turnover_rate",
            ]

            # 3. 格式化日期索引
            df_slice["date"] = pd.to_datetime(df_slice["date"])
            df_slice.set_index("date", inplace=True)

            return df_slice
        except Exception as e:
            print(f"❌ 数据获取发生异常: {e}")
            return None
