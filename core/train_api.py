"""
火车票查询API核心业务模块
功能：封装聚合数据火车票查询API的调用逻辑
"""

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config
from modules.YA_Secrets.secrets_parser import get_secret

logger = get_logger("train_api")


class TrainAPI:
    """火车票查询API封装类"""

    # 查询方式常量
    SEARCH_TYPE_NAME = "1"  # 通过站点名称查询
    SEARCH_TYPE_CODE = "2"  # 通过站点编码查询

    # 车次筛选标志
    TRAIN_FILTERS = {
        "G": "高铁/城际",
        "D": "动车",
        "Z": "直达特快",
        "T": "特快",
        "K": "快速",
        "O": "其他",
        "F": "复兴号",
        "S": "智能动车组",
    }

    # 出发时间段
    TIME_RANGES = {
        "凌晨": "[0:00-06:00)",
        "上午": "[6:00-12:00)",
        "下午": "[12:00-18:00)",
        "晚上": "[18:00-24:00)",
    }

    def __init__(self):
        """初始化API客户端"""
        self.api_url = get_config(
            "train.api_url", "https://apis.juhe.cn/fapigw/train/query"
        )
        self.api_key = get_secret("juhe_train_api_key")

        if not self.api_key:
            logger.warning("未配置火车票API密钥，请检查环境变量或加密文件")

    async def query_trains(
        self,
        departure_station: str,
        arrival_station: str,
        date: str,
        search_type: str = "1",
        filter: Optional[str] = None,
        enable_booking: str = "2",  # ✅ 默认返回所有班次
        departure_time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        查询列车时刻表

        Args:
            departure_station: 出发站，如"北京南"、"上海虹桥"
            arrival_station: 到达站，如"苏州北"、"杭州东"
            date: 出发日期，格式"YYYY-MM-DD"，仅允许15天内的日期
            search_type: 查询方式，"1"-通过站点名称，"2"-通过站点编码
            filter: 车次筛选条件，如"G"（高铁）、"D"（动车）、多个条件不可组合，默认为全部类型
            enable_booking: 是否可预定，"1"-仅返回可预定的班次，"2"-所有（默认）
            departure_time_range: 出发时间选择，可选"凌晨"/"上午"/"下午"/"晚上"

        Returns:
            Dict: 包含列车时刻表的返回结果集

        Raises:
            ValueError: 参数验证失败时抛出
            RuntimeError: API调用失败或返回错误时抛出
        """
        # 参数验证
        self._validate_params(date, filter, departure_time_range)

        if not self.api_key:
            raise RuntimeError("API密钥未配置，请检查配置")

        # 构建请求参数
        params = {
            "key": self.api_key,
            "search_type": search_type,
            "departure_station": departure_station,
            "arrival_station": arrival_station,
            "date": date,
            "enable_booking": enable_booking,  # ✅ 默认传2
        }

        # 添加可选参数
        if filter:
            params["filter"] = filter
        if departure_time_range:
            params["departure_time_range"] = departure_time_range

        logger.info(f"查询列车: {departure_station} → {arrival_station} ({date})")

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()

                result = response.json()

                # 检查业务状态码
                if result.get("error_code") != 0:
                    error_msg = result.get(
                        "reason", f"未知错误({result.get('error_code')})"
                    )
                    raise RuntimeError(f"API返回错误: {error_msg}")

                return result

        except httpx.TimeoutException:
            raise RuntimeError("API请求超时，请稍后重试")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP请求失败: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"列车查询失败: {str(e)}")

    async def query_trains_simple(
        self, departure: str, arrival: str, date: str, filter: Optional[str] = None
    ) -> str:
        """
        查询列车并返回简化版的文字描述

        Args:
            departure: 出发站
            arrival: 到达站
            date: 出发日期
            filter: 车次筛选条件

        Returns:
            str: 友好格式的列车信息描述
        """
        try:
            result = await self.query_trains(
                departure_station=departure,
                arrival_station=arrival,
                date=date,
                filter=filter,
            )

            trains = result.get("result", [])

            if not trains:
                return f"未找到 {departure} → {arrival} 在 {date} 的列车信息。"

            # 构建友好输出
            output = f"🚆 **{departure} → {arrival}** ({date})\n\n"
            output += f"共找到 {len(trains)} 个车次：\n"
            output += "=" * 50 + "\n\n"

            for i, train in enumerate(trains[:10], 1):
                output += f"**{i}. {train.get('train_no')}**\n"
                output += f"   🕒 {train.get('departure_time')} → {train.get('arrival_time')}  (历时 {train.get('duration')})\n"

                # 显示票价信息
                prices = train.get("prices", [])
                if prices:
                    # 找出有票的座位
                    available = [p for p in prices if p.get("num") not in ["无", "0"]]
                    if available:
                        price_info = []
                        for p in available[:3]:
                            price_info.append(
                                f"{p.get('seat_name')}: ¥{p.get('price')}"
                            )
                        output += f"   💰 有票座位: {' | '.join(price_info)}\n"

                    # 显示所有票价（可选）
                    # all_prices = [f"{p.get('seat_name')}: ¥{p.get('price')}" for p in prices[:5]]
                    # output += f"   💺 票价: {' | '.join(all_prices)}\n"

                # 显示列车标签
                flags = train.get("train_flags", [])
                if flags:
                    output += f"   ✨ 标签: {', '.join(flags)}\n"

                # 显示预定状态
                if train.get("enable_booking") == "Y":
                    output += "   ✅ 可预定\n"
                else:
                    output += "   ❌ 不可预定\n"

                output += "\n"

            return output

        except Exception as e:
            logger.error(f"获取列车信息失败: {e}")
            raise

    async def compare_routes(
        self, routes: List[Dict[str, str]], date: str, filter: Optional[str] = None
    ) -> str:
        """
        对比多个路线的列车信息

        Args:
            routes: 路线列表，每个元素包含 departure 和 arrival
            date: 出发日期
            filter: 车次筛选条件

        Returns:
            str: 多路线对比结果
        """
        if len(routes) > 5:
            raise ValueError("最多支持同时对比5个路线")

        results = []
        errors = []

        for route in routes:
            dep = route.get("departure")
            arr = route.get("arrival")
            try:
                result = await self.query_trains(dep, arr, date, filter=filter)
                trains = result.get("result", [])

                # 提取最早和最晚的车次
                if trains:
                    earliest = min(
                        trains, key=lambda x: x.get("departure_time", "00:00")
                    )
                    latest = max(trains, key=lambda x: x.get("departure_time", "00:00"))

                    # 计算最低票价
                    min_price = float("inf")
                    for train in trains:
                        for price in train.get("prices", []):
                            p = price.get("price")
                            if p and isinstance(p, (int, float)) and p < min_price:
                                min_price = p

                    results.append(
                        {
                            "route": f"{dep}→{arr}",
                            "count": len(trains),
                            "earliest": earliest.get("departure_time"),
                            "latest": latest.get("departure_time"),
                            "min_price": min_price if min_price != float("inf") else 0,
                        }
                    )
            except Exception as e:
                errors.append(f"{dep}→{arr}: {str(e)}")

        # 构建对比结果
        comparison = "📊 **多路线列车对比**\n\n"

        if results:
            comparison += "| 路线 | 车次数量 | 最早出发 | 最晚出发 | 最低票价 |\n"
            comparison += "|------|----------|----------|----------|----------|\n"
            for r in results:
                comparison += f"| {r['route']} | {r['count']} | {r['earliest']} | {r['latest']} | ¥{r['min_price']} |\n"

        if errors:
            comparison += "\n⚠️ 以下路线查询失败：\n"
            comparison += "\n".join(errors)

        return comparison

    def _validate_params(
        self, date: str, filter: Optional[str], time_range: Optional[str]
    ) -> None:
        """
        验证参数有效性

        Args:
            date: 日期字符串
            filter: 车次筛选
            time_range: 时间段

        Raises:
            ValueError: 参数无效时抛出
        """
        # 验证日期格式
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            # ✅ 正确的15天计算方式
            max_date = today + timedelta(days=15)

            logger.debug(
                f"验证日期: {date}, 今天: {today}, 查询日: {query_date}, 最大: {max_date}"
            )

            if query_date < today:
                raise ValueError(f"出发日期不能早于今天 ({today.strftime('%Y-%m-%d')})")
            if query_date > max_date:
                raise ValueError(
                    f"只能查询15天内的车次，最大日期为 {max_date.strftime('%Y-%m-%d')}"
                )

        except ValueError as e:
            if "does not match" in str(e):
                raise ValueError("日期格式错误，应为 YYYY-MM-DD，例如 2026-02-26")
            raise

        # 验证filter
        if filter:
            valid_filters = set(self.TRAIN_FILTERS.keys())
            invalid = set(filter) - valid_filters
            if invalid:
                raise ValueError(
                    f"无效的车次筛选条件: {', '.join(invalid)}，"
                    f"可用条件: {', '.join(valid_filters)}"
                )

        # 验证时间段
        if time_range and time_range not in self.TIME_RANGES:
            raise ValueError(
                f"无效的时间段: {time_range}，"
                f"可用选项: {', '.join(self.TIME_RANGES.keys())}"
            )


# 创建单例实例
train_api = TrainAPI()
