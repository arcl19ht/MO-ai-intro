"""
天气预报工具
提供城市天气查询功能
"""

from typing import Any, Dict, Optional

from tools import YA_MCPServer_Tool
from core.weather_api import weather_api
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("weather_tool")


@YA_MCPServer_Tool(
    name="get_weather",
    title="Get Weather",
    description="根据城市名称查询实时天气和未来预报。"
    "【重要参数说明】"
    "city: 必填，城市名称，如'北京'、'上海'、'广州'。"
    "支持中文城市名，不需要加'市'字。"
    "format: 可选，返回格式，可选'simple'(简洁文本)或'detailed'(详细数据)，默认为'simple'。"
    "\n\n使用示例："
    "- 查询北京天气：city='北京'"
    "- 获取详细数据：city='上海', format='detailed'",
)
async def get_weather(city: str, format: str = "simple") -> Any:
    """
    获取指定城市的天气信息

    Args:
        city: 城市名称，例如："北京"、"上海"、"广州"
        format: 返回格式，可选：
            - "simple": 返回友好格式的文本描述（默认）
            - "detailed": 返回详细的JSON数据

    Returns:
        根据format参数返回对应格式的天气信息

    Raises:
        RuntimeError: 查询失败时抛出，包含具体错误原因

    Example:
        simple格式返回：
        "📍 北京 当前天气：
         🌡️ 温度：8°C
         ☁️ 天气：晴
         💧 湿度：45%
         🌬️ 风力：西北风 2级

         📅 未来天气：
           2024-01-15: 晴 -5/8°C
           2024-01-16: 多云 -3/6°C"
    """
    logger.info(f"查询天气: city={city}, format={format}")

    try:
        if format == "detailed":
            # 返回详细JSON数据
            result = await weather_api.query_weather(city)
            return result
        else:
            # 返回简洁文本
            result = await weather_api.query_weather_simple(city)
            return result

    except Exception as e:
        error_msg = f"查询 {city} 天气失败: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
