"""
火车票查询工具
提供列车时刻表查询和对比功能
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from tools import YA_MCPServer_Tool
from core.train_api import train_api
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("train_tool")


@YA_MCPServer_Tool(
    name="query_train_schedule",
    title="Query Train Schedule",
    description="查询两个车站之间的列车时刻表。"
    "\n\n【必填参数】"
    "\n• departure: 出发站，如'北京南'、'上海虹桥'、'武汉'"
    "\n• arrival: 到达站，如'苏州北'、'杭州东'、'广州南'"
    "\n• date: 出发日期，格式'YYYY-MM-DD'，只能查询未来15天内"
    "\n\n【可选参数】"
    "\n• filter: 车次筛选，如'G'高铁、'D'动车，只能输入单个字母，禁止如'GD'的组合，API有问题，该参数建议为空"
    "\n  - G: 高铁/城际"
    "\n  - D: 动车"
    "\n  - Z: 直达特快"
    "\n  - T: 特快"
    "\n  - K: 快速"
    "\n  - F: 复兴号"
    "\n  - S: 智能动车组"
    "\n• format: 返回格式，可选'simple'(简洁文本)或'detailed'(详细数据)，默认为'simple'"
    "\n\n【使用示例】"
    "\n1. 查询高铁：departure='北京南', arrival='上海虹桥', date='2026-03-01', filter='G'"
    "\n2. 查询所有车次：departure='北京', arrival='武汉', date='2026-02-27'"
    "\n3. 获取详细数据：departure='苏州北', arrival='杭州东', date='2026-03-02', format='detailed'"
    "\n4. 查询动车和高速：departure='广州南', arrival='深圳北', date='2026-02-28', filter='GD'",
)
async def query_train_schedule(
    departure: str,
    arrival: str,
    date: str,
    filter: Optional[str] = None,
    format: str = "simple",
) -> Any:
    """
    查询列车时刻表

    Args:
        departure: 出发站名称
        arrival: 到达站名称
        date: 出发日期，格式 YYYY-MM-DD
        filter: 车次筛选，如 "G"(高铁)、"D"(动车)
        format: 返回格式，"simple"或"detailed"

    Returns:
        根据format返回对应格式的列车信息
    """
    logger.info(
        f"查询列车: {departure}→{arrival} ({date}), filter={filter}, format={format}"
    )

    try:
        # 验证日期格式
        try:
            query_date = datetime.strptime(date, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            max_date = today + timedelta(days=15)

            if query_date < today:
                return f"❌ 日期错误：{date} 早于今天 {today.strftime('%Y-%m-%d')}"
            if query_date > max_date:
                return f"❌ 日期错误：只能查询15天内的车次，最晚可查询 {max_date.strftime('%Y-%m-%d')}"
        except ValueError:
            return f"❌ 日期格式错误：'{date}'，应为 YYYY-MM-DD 格式，例如 2026-02-27"

        if format == "detailed":
            result = await train_api.query_trains(
                departure_station=departure,
                arrival_station=arrival,
                date=date,
                filter=filter,
            )
            return result
        else:
            result = await train_api.query_trains_simple(
                departure=departure, arrival=arrival, date=date, filter=filter
            )
            return result

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return f"❌ 参数错误: {str(e)}"
    except Exception as e:
        error_msg = f"查询 {departure}→{arrival} 列车失败: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}"


@YA_MCPServer_Tool(
    name="compare_train_routes",
    title="Compare Train Routes",
    description="对比多个火车路线的车次情况。"
    "\n\n【必填参数】"
    "\n• routes: 路线列表，格式为 [{'departure':'北京','arrival':'上海'}, {'departure':'北京','arrival':'广州'}]"
    "\n• date: 出发日期，格式'YYYY-MM-DD'"
    "\n\n【可选参数】"
    "\n• filter: 车次筛选，如'G'高铁、'D'动车，只能输入单个字母，禁止如'GD'的组合，API有问题，该参数建议为空"
    "\n\n【使用示例】"
    "\n对比京沪和京广：routes=[{'departure':'北京','arrival':'上海'}, {'departure':'北京','arrival':'广州'}], date='2026-03-01'",
)
async def compare_train_routes(
    routes: List[Dict[str, str]], date: str, filter: Optional[str] = None
) -> str:
    """
    对比多个火车路线

    Args:
        routes: 路线列表，每个元素包含 departure 和 arrival
        date: 出发日期
        filter: 车次筛选

    Returns:
        str: 对比结果的文本描述
    """
    logger.info(f"对比路线: {routes}, date={date}")

    try:
        # 验证routes格式
        if not routes or len(routes) < 2:
            return "❌ 请至少提供两个路线进行对比"

        for route in routes:
            if "departure" not in route or "arrival" not in route:
                return "❌ 路线格式错误，每个路线应包含 'departure' 和 'arrival' 字段"

        result = await train_api.compare_routes(routes, date, filter)
        return result

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return f"❌ 参数错误: {str(e)}"
    except Exception as e:
        error_msg = f"路线对比失败: {str(e)}"
        logger.error(error_msg)
        return f"❌ {error_msg}"


@YA_MCPServer_Tool(
    name="get_train_filters",
    title="Get Train Filters",
    description="获取车次筛选条件的说明。"
    "\n\n不需要任何参数，直接调用即可获得所有筛选条件说明。"
    "\n\n【返回内容】"
    "\n• 车次类型筛选码 (G/D/Z/T/K/O/F/S) 的含义"
    "\n• 出发时间段选项 (凌晨/上午/下午/晚上) 的时间范围",
)
async def get_train_filters() -> str:
    """
    获取车次筛选条件说明

    Returns:
        str: 筛选条件说明
    """
    filters = train_api.TRAIN_FILTERS
    time_ranges = train_api.TIME_RANGES

    output = "🚆 **车次筛选说明**\n\n"
    output += "**车次类型筛选 (filter):**\n"
    for code, desc in filters.items():
        output += f"- {code}: {desc}\n"

    output += "\n**出发时间段 (departure_time_range):**\n"
    for name, range_str in time_ranges.items():
        output += f"- {name}: {range_str}\n"

    output += "\n**使用示例:**\n"
    output += "- 查询高铁: filter='G'\n"
    output += "- 查询动车+高铁: filter='GD'\n"
    output += "- 查询上午出发: departure_time_range='上午'"

    return output
