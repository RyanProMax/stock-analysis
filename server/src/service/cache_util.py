"""
缓存工具模块

提供缓存功能，支持本地文件系统和 Google Cloud Storage
- 股票列表缓存：cache/stock_list/
- 分析报告缓存：cache/reports/
- 自动检测环境：开发环境使用本地文件系统，生产环境使用 GCS（如果配置）
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List
from ..env import is_production


class CacheUtil:
    """缓存工具类"""

    # Google Cloud Storage 配置
    GCS_BUCKET_NAME = os.environ.get("GCS_CACHE_BUCKET", "")
    USE_GCS = bool(GCS_BUCKET_NAME) and is_production()

    # 本地文件系统缓存根目录
    _cache_root = os.environ.get("CACHE_DIR")
    if _cache_root:
        CACHE_ROOT = Path(_cache_root)
    else:
        # 默认使用当前工作目录下的 .cache/ 目录
        CACHE_ROOT = Path(".cache")

    STOCK_LIST_CACHE_DIR = "stock_list"
    REPORTS_CACHE_DIR = "reports"

    # GCS 客户端（懒加载）
    _gcs_client = None

    @classmethod
    def _get_gcs_client(cls):
        """获取 GCS 客户端（懒加载）"""
        if cls._gcs_client is not None:
            return cls._gcs_client

        if not cls.USE_GCS:
            return None

        try:
            # 动态导入，避免在没有安装时出错
            try:
                from google.cloud import storage  # type: ignore
            except ImportError:
                print("⚠️ google-cloud-storage 未安装，将使用本地文件系统缓存")
                return None

            cls._gcs_client = storage.Client()
            print("✓ Google Cloud Storage 客户端初始化成功")
            return cls._gcs_client
        except Exception as e:
            print(f"⚠️ GCS 客户端初始化失败: {e}，将使用本地文件系统缓存")
            return None

    @classmethod
    def _ensure_cache_dir(cls, cache_dir: Path) -> None:
        """确保本地缓存目录存在"""
        if not cls.USE_GCS:
            cache_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _get_date_key(cls) -> str:
        """获取日期键（YYYY-MM-DD）"""
        return datetime.now().strftime("%Y-%m-%d")

    @classmethod
    def _get_gcs_path(cls, cache_dir: str, filename: str) -> str:
        """获取 GCS 对象路径"""
        return f"{cache_dir}/{filename}"

    @classmethod
    def _get_local_cache_file_path(cls, cache_dir: str, filename: str) -> Path:
        """获取本地缓存文件路径"""
        local_dir = cls.CACHE_ROOT / cache_dir
        cls._ensure_cache_dir(local_dir)
        return local_dir / filename

    @classmethod
    def _save_to_gcs(cls, path: str, data: Any) -> bool:
        """保存数据到 GCS"""
        try:
            client = cls._get_gcs_client()
            if client is None:
                return False

            bucket = client.bucket(cls.GCS_BUCKET_NAME)
            blob = bucket.blob(path)

            if isinstance(data, (dict, list)):
                content = json.dumps(data, ensure_ascii=False, indent=2)
                blob.upload_from_string(content, content_type="application/json")
            else:
                blob.upload_from_string(str(data))

            return True
        except Exception as e:
            print(f"⚠️ 保存到 GCS 失败: {e}")
            return False

    @classmethod
    def _load_from_gcs(cls, path: str) -> Optional[Any]:
        """从 GCS 加载数据"""
        try:
            client = cls._get_gcs_client()
            if client is None:
                return None

            bucket = client.bucket(cls.GCS_BUCKET_NAME)
            blob = bucket.blob(path)

            if not blob.exists():
                return None

            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            print(f"⚠️ 从 GCS 加载失败: {e}")
            return None

    @classmethod
    def save_stock_list(
        cls, market: str, data: List[Dict[str, Any]], date: Optional[str] = None
    ) -> bool:
        """
        保存股票列表到缓存（GCS 或本地文件系统）

        Args:
            market: 市场类型（"A股" 或 "美股"）
            data: 股票列表数据
            date: 日期（YYYY-MM-DD），如果为 None 则使用今天

        Returns:
            bool: 是否保存成功
        """
        try:
            if date is None:
                date = cls._get_date_key()

            # 文件名：a_stocks_YYYY-MM-DD.json 或 us_stocks_YYYY-MM-DD.json
            market_prefix = "a_stocks" if market == "A股" else "us_stocks"
            filename = f"{market_prefix}_{date}.json"

            success = False

            # 优先保存到 GCS（如果配置了）
            if cls.USE_GCS:
                gcs_path = cls._get_gcs_path(cls.STOCK_LIST_CACHE_DIR, filename)
                if cls._save_to_gcs(gcs_path, data):
                    print(f"✓ 股票列表已保存到 GCS: gs://{cls.GCS_BUCKET_NAME}/{gcs_path}")
                    success = True

            # 同时保存到本地文件系统（作为备份或开发环境使用）
            try:
                cache_file = cls._get_local_cache_file_path(cls.STOCK_LIST_CACHE_DIR, filename)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                if not cls.USE_GCS:
                    print(f"✓ 股票列表已保存到本地缓存: {cache_file}")
                success = True
            except Exception as e:
                if not cls.USE_GCS:
                    print(f"⚠️ 保存到本地缓存失败: {e}")

            return success
        except Exception as e:
            print(f"⚠️ 保存股票列表缓存失败: {e}")
            return False

    @classmethod
    def load_stock_list(
        cls, market: str, date: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        从缓存加载股票列表（优先从 GCS，其次本地文件系统）

        Args:
            market: 市场类型（"A股" 或 "美股"）
            date: 日期（YYYY-MM-DD），如果为 None 则使用今天

        Returns:
            Optional[List[Dict[str, Any]]]: 股票列表数据，如果不存在则返回 None
        """
        try:
            if date is None:
                date = cls._get_date_key()

            market_prefix = "a_stocks" if market == "A股" else "us_stocks"
            filename = f"{market_prefix}_{date}.json"

            # 优先从 GCS 加载
            if cls.USE_GCS:
                gcs_path = cls._get_gcs_path(cls.STOCK_LIST_CACHE_DIR, filename)
                data = cls._load_from_gcs(gcs_path)
                if data is not None and isinstance(data, list) and len(data) > 0:
                    print(
                        f"✓ 从 GCS 加载股票列表: gs://{cls.GCS_BUCKET_NAME}/{gcs_path}，共 {len(data)} 只股票"
                    )
                    return data

            # 从本地文件系统加载
            cache_file = cls._get_local_cache_file_path(cls.STOCK_LIST_CACHE_DIR, filename)
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list) and len(data) > 0:
                    print(f"✓ 从本地缓存加载股票列表: {cache_file}，共 {len(data)} 只股票")
                    return data
                else:
                    print(f"⚠️ 缓存文件存在但数据为空: {cache_file}")

            return None
        except Exception as e:
            print(f"⚠️ 加载股票列表缓存失败: {e}")
            return None

    @classmethod
    def save_report(cls, symbol: str, report: Dict[str, Any], date: Optional[str] = None) -> bool:
        """
        保存分析报告到缓存（GCS 或本地文件系统）

        Args:
            symbol: 股票代码
            report: 分析报告数据（字典格式）
            date: 日期（YYYY-MM-DD），如果为 None 则使用今天

        Returns:
            bool: 是否保存成功
        """
        try:
            if date is None:
                date = cls._get_date_key()

            filename = f"{symbol.upper()}.json"
            success = False

            # 优先保存到 GCS（如果配置了）
            if cls.USE_GCS:
                # GCS 路径：reports/YYYY-MM-DD/SYMBOL.json
                gcs_path = cls._get_gcs_path(f"{cls.REPORTS_CACHE_DIR}/{date}", filename)
                if cls._save_to_gcs(gcs_path, report):
                    print(f"✓ 分析报告已保存到 GCS: gs://{cls.GCS_BUCKET_NAME}/{gcs_path}")
                    success = True

            # 同时保存到本地文件系统
            try:
                date_dir = cls.CACHE_ROOT / cls.REPORTS_CACHE_DIR / date
                cls._ensure_cache_dir(date_dir)
                cache_file = date_dir / filename

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                if not cls.USE_GCS:
                    print(f"✓ 分析报告已保存到本地缓存: {cache_file}")
                success = True
            except Exception as e:
                if not cls.USE_GCS:
                    print(f"⚠️ 保存到本地缓存失败: {e}")

            return success
        except Exception as e:
            print(f"⚠️ 保存分析报告缓存失败: {e}")
            return False

    @classmethod
    def load_report(cls, symbol: str, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        从缓存加载分析报告（优先从 GCS，其次本地文件系统）

        Args:
            symbol: 股票代码
            date: 日期（YYYY-MM-DD），如果为 None 则使用今天

        Returns:
            Optional[Dict[str, Any]]: 分析报告数据，如果不存在则返回 None
        """
        try:
            if date is None:
                date = cls._get_date_key()

            filename = f"{symbol.upper()}.json"

            # 优先从 GCS 加载
            if cls.USE_GCS:
                gcs_path = cls._get_gcs_path(f"{cls.REPORTS_CACHE_DIR}/{date}", filename)
                data = cls._load_from_gcs(gcs_path)
                if data is not None:
                    print(f"✓ 从 GCS 加载分析报告: gs://{cls.GCS_BUCKET_NAME}/{gcs_path}")
                    return data

            # 从本地文件系统加载
            date_dir = cls.CACHE_ROOT / cls.REPORTS_CACHE_DIR / date
            cache_file = date_dir / filename

            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"✓ 从本地缓存加载分析报告: {cache_file}")
                return data

            return None
        except Exception as e:
            print(f"⚠️ 加载分析报告缓存失败: {e}")
            return None

    @classmethod
    def cleanup_old_cache(cls, days_to_keep: int = 7) -> None:
        """
        清理旧的缓存文件（保留最近 N 天的缓存）
        注意：GCS 清理需要单独配置生命周期策略

        Args:
            days_to_keep: 保留最近几天的缓存，默认 7 天
        """
        try:
            today = datetime.now()

            # 清理本地股票列表缓存
            local_stock_dir = cls.CACHE_ROOT / cls.STOCK_LIST_CACHE_DIR
            if local_stock_dir.exists():
                for cache_file in local_stock_dir.glob("*.json"):
                    try:
                        # 从文件名提取日期：a_stocks_YYYY-MM-DD.json
                        date_str = cache_file.stem.split("_")[-1]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_diff = (today - file_date).days

                        if days_diff > days_to_keep:
                            cache_file.unlink()
                            print(f"✓ 已删除旧缓存: {cache_file}")
                    except Exception:
                        continue

            # 清理本地分析报告缓存
            local_reports_dir = cls.CACHE_ROOT / cls.REPORTS_CACHE_DIR
            if local_reports_dir.exists():
                for date_dir in local_reports_dir.iterdir():
                    if not date_dir.is_dir():
                        continue

                    try:
                        date_str = date_dir.name
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        days_diff = (today - file_date).days

                        if days_diff > days_to_keep:
                            import shutil

                            shutil.rmtree(date_dir)
                            print(f"✓ 已删除旧缓存目录: {date_dir}")
                    except Exception:
                        continue

            # GCS 清理建议：在 GCS Bucket 上配置生命周期策略，自动删除旧文件
            if cls.USE_GCS:
                print("ℹ️ GCS 缓存清理：建议在 GCS Bucket 上配置生命周期策略自动清理")

        except Exception as e:
            print(f"⚠️ 清理旧缓存失败: {e}")
