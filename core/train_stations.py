"""
火车站数据处理核心模块
功能：加载和查询车站信息
"""

import json
from typing import Dict, Optional, List
from pathlib import Path

from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config

logger = get_logger("train_stations")


class TrainStations:
    """火车站数据处理类"""

    def __init__(self):
        """初始化车站数据"""
        self.stations: Dict[str, Dict[str, str]] = {}
        self._load_stations()

    def _load_stations(self) -> None:
        """
        从JSON文件加载车站数据

        Raises:
            RuntimeError: 文件加载失败时抛出
        """
        try:
            # 从配置获取文件路径，默认为 data/train_stations.json
            file_path = get_config("train.stations_file", "data/train_stations.json")
            path = Path(file_path)

            if not path.exists():
                logger.error(f"车站数据文件不存在: {path.absolute()}")
                return

            with open(path, "r", encoding="utf-8") as f:
                self.stations = json.load(f)

            logger.info(f"成功加载 {len(self.stations)} 个车站")

        except json.JSONDecodeError as e:
            logger.error(f"车站数据文件格式错误: {e}")
            raise RuntimeError(f"车站数据文件格式错误: {e}")
        except Exception as e:
            logger.error(f"加载车站数据失败: {e}")
            raise RuntimeError(f"加载车站数据失败: {e}")

    def get_all_stations(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有车站数据

        Returns:
            Dict: 所有车站的字典，键为车站名称
        """
        return self.stations.copy()

    def get_station_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """
        根据车站名称查询车站信息

        Args:
            name: 车站名称，如"北京南"

        Returns:
            Optional[Dict]: 车站信息，如果不存在则返回None

        Example:
            {
                "station_code": "VNP",
                "station_name": "北京南",
                "station_pinyin": "beijingnan",
                "station_city": "北京"
            }
        """
        return self.stations.get(name)

    def search_stations(
        self, keyword: str, search_by: str = "name"
    ) -> List[Dict[str, str]]:
        """
        搜索车站

        Args:
            keyword: 搜索关键词
            search_by: 搜索方式，可选：
                - "name": 按车站名称搜索（默认）
                - "code": 按车站编码搜索
                - "pinyin": 按拼音搜索
                - "city": 按城市搜索

        Returns:
            List[Dict]: 匹配的车站列表

        Example:
            search_stations("北京", "city")
            -> 返回北京市所有车站
        """
        results = []
        keyword_lower = keyword.lower()

        for name, info in self.stations.items():
            if search_by == "name":
                if keyword in name or keyword_lower in name.lower():
                    results.append(info)

            elif search_by == "code":
                if keyword.upper() in info.get("station_code", ""):
                    results.append(info)

            elif search_by == "pinyin":
                pinyin = info.get("station_pinyin", "").lower()
                if keyword_lower in pinyin:
                    results.append(info)

            elif search_by == "city":
                city = info.get("station_city", "").lower()
                if keyword_lower in city:
                    results.append(info)

        return results

    def get_stations_by_city(self, city: str) -> List[Dict[str, str]]:
        """
        获取指定城市的所有车站

        Args:
            city: 城市名称，如"北京"

        Returns:
            List[Dict]: 该城市的所有车站列表
        """
        return self.search_stations(city, search_by="city")

    def format_station_info(self, station: Dict[str, str]) -> str:
        """
        格式化车站信息为可读文本

        Args:
            station: 车站信息字典

        Returns:
            str: 格式化后的文本
        """
        return (
            f"🚉 {station.get('station_name')}\n"
            f"  编码: {station.get('station_code')}\n"
            f"  拼音: {station.get('station_pinyin')}\n"
            f"  城市: {station.get('station_city')}"
        )

    def format_station_list(
        self, stations: List[Dict[str, str]], max_items: int = 20
    ) -> str:
        """
        格式化车站列表为可读文本

        Args:
            stations: 车站列表
            max_items: 最大显示数量

        Returns:
            str: 格式化后的文本
        """
        if not stations:
            return "未找到匹配的车站"

        output = f"🚉 **共找到 {len(stations)} 个车站**\n\n"

        for i, station in enumerate(stations[:max_items], 1):
            output += f"{i}. {station.get('station_name')}\n"
            output += f"   编码: {station.get('station_code')} | "
            output += f"城市: {station.get('station_city')}\n"

        if len(stations) > max_items:
            output += f"\n... 还有 {len(stations) - max_items} 个车站"

        return output


# 创建单例实例
train_stations = TrainStations()
