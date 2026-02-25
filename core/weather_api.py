"""
天气预报API核心业务模块
功能：封装聚合数据天气预报API的调用逻辑
"""

import httpx
from typing import Dict, Any, List

from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config
from modules.YA_Secrets.secrets_parser import get_secret

logger = get_logger("weather_api")


class WeatherAPI:
    """天气预报API封装类"""

    def __init__(self):
        """初始化API客户端"""
        # 从配置读取API信息
        self.api_url = get_config("weather.api_url", "http://apis.juhe.cn/simpleWeather/query")
        self.api_key = get_secret("juhe_weather_api_key")

        if not self.api_key:
            logger.warning("未配置天气API密钥，请检查环境变量或加密文件")

    async def query_weather(self, city: str) -> Dict[str, Any]:
        """
        根据城市名称查询天气

        Args:
            city: 城市名称，如"北京"、"上海"

        Returns:
            Dict: 包含实时天气和未来天气的完整响应

        Raises:
            RuntimeError: API调用失败或返回错误时抛出

        Example:
            {
                "city": "苏州",
                "realtime": {
                    "temperature": "4",
                    "humidity": "82",
                    "info": "阴",
                    "wid": "02",
                    "direct": "西北风",
                    "power": "3级",
                    "aqi": "80"
                },
                "future": [...]
            }
        """
        if not self.api_key:
            raise RuntimeError("API密钥未配置，请检查配置")

        params = {"key": self.api_key, "city": city}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()

                result = response.json()

                # 检查业务状态码
                if result.get("error_code") != 0:
                    error_msg = self._get_error_message(result.get("error_code"))
                    raise RuntimeError(f"API返回错误: {error_msg}")

                return result.get("result", {})

        except httpx.TimeoutException:
            raise RuntimeError("API请求超时")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP请求失败: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"天气查询失败: {str(e)}")

    async def query_weather_simple(self, city: str) -> str:
        """
        查询天气并返回简化版的文字描述

        Args:
            city: 城市名称

        Returns:
            str: 友好格式的天气描述
        """
        try:
            data = await self.query_weather(city)

            realtime = data.get("realtime", {})
            future = data.get("future", [])

            # 构建友好输出
            current = f"📍 {data.get('city', city)} 当前天气：\n"
            current += f"🌡️ 温度：{realtime.get('temperature', 'N/A')}°C\n"
            current += f"☁️ 天气：{realtime.get('info', 'N/A')}\n"
            current += f"💧 湿度：{realtime.get('humidity', 'N/A')}%\n"
            current += f"🌬️ 风力：{realtime.get('direct', 'N/A')} {realtime.get('power', 'N/A')}\n"

            if realtime.get("aqi"):
                current += f"🍃 空气质量：{realtime.get('aqi')}\n"

            # 添加未来几天预报
            if future:
                current += "\n📅 未来天气：\n"
                for day in future[:3]:  # 只显示3天
                    current += f"  {day.get('date')}: {day.get('weather')} {day.get('temperature')}\n"

            return current

        except Exception as e:
            logger.error(f"获取天气描述失败: {e}")
            raise

    def _get_error_message(self, error_code: int) -> str:
        """
        根据错误码获取错误信息

        Args:
            error_code: API返回的错误码

        Returns:
            str: 错误描述
        """
        error_messages = {
            207301: "错误的查询城市名",
            207302: "查询不到该城市的相关信息",
            207303: "网络错误，请重试",
            10001: "错误的请求KEY",
            10002: "该KEY无请求权限",
            10003: "KEY过期",
            10004: "错误的OPENID",
            10005: "应用未审核超时",
            10007: "未知的请求源",
            10008: "被禁止的IP",
            10009: "被禁止的KEY",
            10011: "当前IP请求超过限制",
            10012: "请求超过次数限制",
            10013: "测试KEY超过请求限制",
            10014: "系统内部异常",
        }
        return error_messages.get(error_code, f"未知错误({error_code})")

    async def get_supported_cities(self) -> List[Dict[str, Any]]:
        """
        获取支持的城市列表
        实际应用中可以从Excel下载并缓存

        Returns:
            List[Dict]: 城市列表
        """
        # 这里可以读取缓存的Excel文件
        # 示例返回
        return [
            {"id": "101010100", "name": "北京", "province": "北京"},
            {"id": "101020100", "name": "上海", "province": "上海"},
            {"id": "101280101", "name": "广州", "province": "广东"},
        ]


# 创建单例实例
weather_api = WeatherAPI()
