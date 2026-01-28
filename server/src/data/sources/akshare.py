"""
AkShare 数据源

使用 AkShare 获取 A 股股票列表、财务数据
"""

from typing import List, Dict, Any, Optional, cast
import pandas as pd
import akshare as ak

from .base import BaseStockDataSource


class AkShareDataSource(BaseStockDataSource):
    """AkShare 数据源"""

    SOURCE_NAME: str = "AkShare"

    def fetch_a_stocks(self) -> List[Dict[str, Any]]:
        """获取 A 股股票列表"""
        df = ak.stock_info_a_code_name()
        stocks = []

        for _, row in df.iterrows():
            symbol = str(row["code"]).strip()
            name = str(row["name"]).strip()

            # 根据代码判断交易所
            if symbol.startswith("6"):
                ts_code = f"{symbol}.SH"
                market = "主板"
            elif symbol.startswith("0"):
                ts_code = f"{symbol}.SZ"
                market = "主板"
            elif symbol.startswith("3"):
                ts_code = f"{symbol}.SZ"
                market = "创业板"
            else:
                ts_code = f"{symbol}.SZ"
                market = "主板"

            stocks.append(
                {
                    "ts_code": ts_code,
                    "symbol": symbol,
                    "name": name,
                    "area": None,
                    "industry": None,
                    "market": market,
                    "list_date": None,
                }
            )

        return stocks

    def fetch_us_stocks(self) -> List[Dict[str, Any]]:
        """AkShare 不支持美股"""
        return []

    def is_available(self, market: str) -> bool:
        """AkShare 仅支持 A 股"""
        return market == "A股"

    @classmethod
    def get_cn_financial_data(cls, symbol: str) -> tuple[Optional[dict], dict]:
        """
        使用 AkShare 获取A股财务数据（备用方案）

        Args:
            symbol: A股代码（6位，如 600519）

        Returns:
            (财务数据字典, 原始数据字典)
        """
        financial_data = {}
        raw_data = {}

        try:
            # 使用东方财富个股信息获取基本信息
            df_info = ak.stock_individual_info_em(symbol=symbol)
            if df_info is not None and not df_info.empty:
                raw_data["individual_info"] = df_info.to_dict()

            # 使用财务摘要获取ROE、资产负债率等
            try:
                df_abstract = ak.stock_financial_abstract(symbol=symbol)
                if df_abstract is not None and not df_abstract.empty:
                    raw_data["financial_abstract"] = df_abstract.to_dict()
                    # 从常用指标中提取数据
                    common = cast(pd.DataFrame, df_abstract[df_abstract["选项"] == "常用指标"])
                    if not common.empty:
                        # ROE（净资产收益率）
                        roe_row = cast(pd.DataFrame, common[common["指标"] == "净资产收益率(ROE)"])
                        if len(roe_row) > 0:
                            # 获取最新一期数据（第二列是指标名，第三列开始是各期数据）
                            latest_value = roe_row.iloc[0, 2]  # 20250930列
                            if pd.notna(latest_value):
                                financial_data["roe"] = float(latest_value)

                        # 资产负债率
                        debt_row = cast(pd.DataFrame, common[common["指标"] == "资产负债率"])
                        if len(debt_row) > 0:
                            latest_value = debt_row.iloc[0, 2]
                            if pd.notna(latest_value):
                                financial_data["debt_ratio"] = float(latest_value)

                        # 营收增长率 - 从成长能力中获取
                    growth = cast(pd.DataFrame, df_abstract[df_abstract["选项"] == "成长能力"])
                    if len(growth) > 0:
                        # 查找营业收入增长率
                        revenue_row = cast(
                            pd.DataFrame,
                            growth[growth["指标"].str.contains("营业收入", na=False)],
                        )
                        if len(revenue_row) > 0:
                            latest_value = revenue_row.iloc[0, 2]
                            if pd.notna(latest_value):
                                financial_data["revenue_growth"] = float(latest_value)

            except Exception as e:
                print(f"⚠️ 获取财务摘要失败: {e}")

        except Exception as e:
            import traceback

            print(f"❌ AkShare获取A股财务数据失败: {e}")
            traceback.print_exc()

        return financial_data if financial_data else None, raw_data
