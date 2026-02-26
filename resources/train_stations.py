"""
火车站信息资源
提供车站数据的读取功能
"""

import json
from urllib.parse import unquote

from resources import YA_MCPServer_Resource
from core.train_stations import train_stations
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("train_stations_resource")


@YA_MCPServer_Resource(
    "data://stations/all",
    name="all_stations",
    title="All Train Stations",
    description="获取所有火车站的完整数据",
    mime_type="application/json",
)
async def get_all_stations() -> str:
    """获取所有车站数据"""
    try:
        stations = train_stations.get_all_stations()
        return json.dumps(stations, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@YA_MCPServer_Resource(
    "data://stations/name/{station_name}",
    name="station_by_name",
    title="Station by Name",
    description="根据车站名称查询详细信息。参数station_name: 车站名称，如'北京南'、'上海虹桥'",
    mime_type="application/json",
)
async def get_station_by_name(station_name: str) -> str:
    """根据车站名称查询车站信息"""
    # 解码URL编码的参数
    decoded_name = unquote(station_name)
    logger.info(f"🔍 按名称查询: {station_name} -> 解码后: {decoded_name}")

    try:
        station = train_stations.get_station_by_name(decoded_name)
        if station:
            return json.dumps(station, ensure_ascii=False, indent=2)
        else:
            return json.dumps(
                {
                    "error": f"未找到车站: {decoded_name}",
                    "suggestion": "请尝试使用搜索功能 text://stations/search/关键词/name 查找类似车站",
                },
                ensure_ascii=False,
                indent=2,
            )
    except Exception as e:
        logger.error(f"查询车站失败: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@YA_MCPServer_Resource(
    "data://stations/city/{city_name}",
    name="stations_by_city",
    title="Stations by City",
    description="获取指定城市的所有车站（快捷方式）。参数city_name: 城市名称",
    mime_type="application/json",
)
async def get_stations_by_city(city_name: str) -> str:
    """
    获取指定城市的所有车站（快捷方式）

    Args:
        city_name: 城市名称（可能包含URL编码）
    """
    # 解码URL编码的参数
    decoded_city = unquote(city_name)
    logger.info(f"🔍 收到城市请求: {city_name} -> 解码后: {decoded_city}")

    try:
        stations = train_stations.get_stations_by_city(decoded_city)
        logger.info(f"找到 {len(stations)} 个车站")

        return json.dumps(
            {"city": decoded_city, "count": len(stations), "stations": stations},
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        logger.error(f"获取车站失败: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@YA_MCPServer_Resource(
    "data://stations/search/{keyword}/{by}",
    name="search_stations",
    title="Search Stations (JSON)",
    description="搜索车站并返回JSON格式结果。支持按名称、编码、拼音、城市搜索。"
    "URI格式: data://stations/search/{keyword}/{by}"
    "参数说明:"
    "- keyword: 搜索关键词，如'北京'、'VNP'、'shanghai'"
    "- by: 搜索方式，可选 name/code/pinyin/city"
    "\n\n使用示例："
    "- 按名称搜索: data://stations/search/北京南/name"
    "- 按编码搜索: data://stations/search/VNP/code"
    "- 按拼音搜索: data://stations/search/beijing/pinyin"
    "- 按城市搜索: data://stations/search/上海/city",
    mime_type="application/json",
)
async def search_stations(keyword: str, by: str) -> str:
    """
    搜索车站，返回JSON格式

    Args:
        keyword: 搜索关键词
        by: 搜索方式

    Returns:
        JSON格式的搜索结果
    """
    # 解码URL编码的参数
    decoded_keyword = unquote(keyword)
    logger.info(f"🔍 JSON搜索: {keyword} -> 解码后: {decoded_keyword}, by={by}")

    try:
        # 验证by参数是否有效
        valid_by = ["name", "code", "pinyin", "city"]
        if by not in valid_by:
            return json.dumps(
                {"error": f"无效的搜索方式: {by}", "valid_options": valid_by},
                ensure_ascii=False,
                indent=2,
            )

        results = train_stations.search_stations(decoded_keyword, search_by=by)

        return json.dumps(
            {
                "keyword": decoded_keyword,
                "search_by": by,
                "count": len(results),
                "results": results[:50],  # 限制返回数量
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"搜索车站失败: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@YA_MCPServer_Resource(
    "text://stations/search/{keyword}/{by}",
    name="search_stations_text",
    title="Search Stations (Text)",
    description="搜索车站并返回易读的文本格式。"
    "URI格式: text://stations/search/{keyword}/{by}"
    "参数说明同JSON版本",
    mime_type="text/plain",
)
async def search_stations_text(keyword: str, by: str) -> str:
    """
    搜索车站并返回易读的文本格式

    Args:
        keyword: 搜索关键词
        by: 搜索方式

    Returns:
        格式化的文本结果
    """
    # 解码URL编码的参数
    decoded_keyword = unquote(keyword)
    logger.info(f"🔍 文本搜索: {keyword} -> 解码后: {decoded_keyword}, by={by}")

    try:
        valid_by = ["name", "code", "pinyin", "city"]
        if by not in valid_by:
            return f"❌ 无效的搜索方式: {by}，可用选项: {', '.join(valid_by)}"

        results = train_stations.search_stations(decoded_keyword, search_by=by)
        return train_stations.format_station_list(results)

    except Exception as e:
        logger.error(f"搜索车站失败: {e}")
        return f"❌ 搜索失败: {e}"
