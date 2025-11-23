import akshare as ak
import pandas as pd
from typing import Optional


class DataLoader:
    # 东方财富列名映射
    EASTMONEY_MAP = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
    }

    @staticmethod
    def get_stock_daily(symbol: str) -> Optional[pd.DataFrame]:
        """
        获取指定股票的日线数据 (前复权)
        具备自动切换源功能：东方财富 -> 新浪财经
        :param symbol: 股票代码 (如 "600519")
        :return: 清洗后的 DataFrame 或 None
        """

        # --- 策略 1: 尝试从 [东方财富] 获取 ---
        try:
            print(f"📡 [1/2] 正在尝试从 东方财富 获取 [{symbol}] 数据...")
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")

            if not df.empty:
                return DataLoader._standardize_df(
                    df, DataLoader.EASTMONEY_MAP, source="EastMoney"
                )
            else:
                print("⚠️ 东方财富返回数据为空，尝试备用源...")

        except Exception as e:
            print(f"⚠️ 东方财富接口连接失败 ({e})，准备切换备用源...")

        # --- 策略 2: 尝试从 [新浪财经] 获取 (作为灾备) ---
        try:
            print(f"📡 [2/2] 正在切换至 新浪财经 获取 [{symbol}] 数据...")

            # 新浪接口通常需要区分 sh/sz 前缀
            # 简单判断逻辑: 6开头为sh, 其他(0/3)为sz
            sina_symbol = f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"

            df = ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq")

            if not df.empty:
                # 新浪返回的列名通常已经是 open/close 等英文，不需要复杂的中文映射
                # 但为了保险，我们只转换 date 列并设置索引
                return DataLoader._standardize_df(df, {}, source="Sina")
            else:
                print("❌ 新浪财经也未找到数据，请检查股票代码是否正确。")

        except Exception as e:
            print(f"❌ 所有数据源均获取失败。最后错误: {e}")

        return None

    @staticmethod
    def _standardize_df(
        df: pd.DataFrame, rename_map: dict, source: str
    ) -> pd.DataFrame:
        """
        内部工具方法：标准化 DataFrame 格式
        1. 重命名列
        2. 转换日期格式
        3. 设置日期为索引
        """
        # 1. 重命名列 (如果提供了映射)
        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        # 2. 确保包含必要的列 (防止后续 stockstats 计算报错)
        required_cols = ["open", "close", "high", "low", "volume"]

        # 针对新浪等已经是英文列名的情况，确保列名都是小写
        df.columns = [c.lower() for c in df.columns]

        # 检查必要列是否存在
        if not all(col in df.columns for col in required_cols):
            # 这种情况下可能是源数据列名非常特殊，打印出来方便调试
            print(f"⚠️ {source} 返回的列名不符合预期: {df.columns.tolist()}")

        # 3. 处理日期索引
        # 不同的接口日期的列名可能叫 'date' 或者 '日期'
        date_col = None
        if "date" in df.columns:
            date_col = "date"
        elif "日期" in df.columns:
            date_col = "日期"

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
            df.index.name = "date"  # 统一索引名称
        else:
            # 如果没有日期列，但索引本身就是日期（某些接口特性）
            if not isinstance(df.index, pd.DatetimeIndex):
                print(f"⚠️ 警告: 无法在 {source} 数据中找到日期列，数据可能不准确。")

        print(f"✅ 成功从 [{source}] 获取并清洗数据 ({len(df)} 条)")
        return df
