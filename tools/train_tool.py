"""
火车票查询工具
提供列车时刻表查询和对比功能
"""
from typing import Any, Dict, Optional, List

from tools import YA_MCPServer_Tool
from core.train_api import train_api
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("train_tool")


@YA_MCPServer_Tool(
    name="query_train_schedule",
    title="Query Train Schedule",
    description="查询两个车站之间的列车时刻表。"
                "【必填参数】"
                "departure: 出发站，如'北京南'、'上海虹桥'"
                "arrival: 到达站，如'苏州北'、'杭州东'"
                "date: 出发日期，格式'YYYY-MM-DD'，只能查询未来15天内"
                "【可选参数】"
                "filter: 车次筛选，如'G'高铁、'D'动车，可组合如'GD'"
                "format: 返回格式，可选'simple'(简洁文本)或'detailed'(详细数据)，默认为'simple'"
                "\n\n使用示例："
                "- 查询高铁：departure='北京南', arrival='上海虹桥', date='2025-03-01', filter='G'"
                "- 详细数据：departure='苏州北', arrival='杭州东', date='2025-03-02', format='detailed'",
)
async def query_train_schedule(
    departure: str,
    arrival: str,
    date: str,
    filter: Optional[str] = None,
    format: str = "simple"
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
        
    Raises:
        ValueError: 参数验证失败
        RuntimeError: 查询失败
        
    Example:
        simple格式返回：
        "🚆 北京南 → 上海虹桥 (2025-03-01)
         
         共找到 15 个车次：
         
         1. G1
            🕒 07:00 → 12:23 (历时 05:23)
            💰 商务座: ¥2194 | 一等座: ¥1003 | 二等座: ¥627
            ✨ 标签: 复兴号
            ✅ 可预定"
    """
    logger.info(f"查询列车: {departure}→{arrival} ({date}), filter={filter}, format={format}")
    
    try:
        if format == "detailed":
            # 返回详细JSON数据
            result = await train_api.query_trains(
                departure_station=departure,
                arrival_station=arrival,
                date=date,
                filter=filter
            )
            return result
        else:
            # 返回简洁文本
            result = await train_api.query_trains_simple(
                departure=departure,
                arrival=arrival,
                date=date,
                filter=filter
            )
            return result
            
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise
    except Exception as e:
        error_msg = f"查询 {departure}→{arrival} 列车失败: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@YA_MCPServer_Tool(
    name="compare_train_routes",
    title="Compare Train Routes",
    description="对比多个火车路线的车次情况。"
                "【必填参数】"
                "routes: 路线列表，格式为 [{'departure':'北京','arrival':'上海'}, ...]"
                "date: 出发日期，格式'YYYY-MM-DD'"
                "【可选参数】"
                "filter: 车次筛选，如'G'"
                "\n\n使用示例："
                "- 对比京沪和沪深：routes=[{'departure':'北京','arrival':'上海'}, {'departure':'上海','arrival':'深圳'}], date='2025-03-01'",
)
async def compare_train_routes(
    routes: List[Dict[str, str]],
    date: str,
    filter: Optional[str] = None
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
        result = await train_api.compare_routes(routes, date, filter)
        return result
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise
    except Exception as e:
        error_msg = f"路线对比失败: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@YA_MCPServer_Tool(
    name="get_train_filters",
    title="Get Train Filters",
    description="获取车次筛选条件的说明。不需要任何参数。",
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
    
    return output