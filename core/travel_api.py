"""
旅游助手 API 核心业务模块
功能：封装高德地图API的调用逻辑，提供景点、酒店搜索功能
依赖：httpx
"""
import httpx
from typing import Dict, Any, List

from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config
from modules.YA_Secrets.secrets_parser import get_secret

logger = get_logger("travel_api")


class TravelAPI:
    """高德地图API封装类"""

    def __init__(self):
        """初始化API客户端"""
        # 从配置读取API信息
        self.api_key = get_secret("amap_key")
        self.api_url = get_config(
            "amap.api_url", "https://restapi.amap.com/v3/place/text"
        )

        if not self.api_key:
            logger.warning("未配置高德地图API密钥，请检查环境变量或加密文件")

    async def search_attractions(
        self, keyword: str, city: str = "全国", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索景点信息

        Args:
            keyword: 搜索关键词，如"故宫"、"西湖"
            city: 城市名称，如"北京"、"上海"，默认为"全国"
            limit: 返回结果数量限制，默认5条

        Returns:
            List[Dict[str, Any]]: 景点信息列表，每个景点包含：
                - name: 景点名称
                - address: 详细地址
                - type: 景点类型
                - rating: 评分
                - cost: 参考价格
                - tel: 联系电话
                - location: 经纬度坐标

        Raises:
            RuntimeError: API调用失败或返回错误时抛出

        Example:
            [
                {
                    "name": "故宫博物院",
                    "address": "北京市东城区景山前街4号",
                    "type": "风景名胜;旅游景点;博物馆",
                    "rating": "4.8",
                    "cost": "60元",
                    "tel": "010-85007421",
                    "location": "116.397027,39.917908"
                }
            ]
        """
        if not self.api_key:
            raise RuntimeError("配置错误：未在 env.yaml 中配置 'amap_key'，无法调用高德地图 API。")

        params = {
            "key": self.api_key,
            "keywords": keyword,
            "city": city,
            "types": "风景名胜|公园广场|旅游景点|历史文化",
            "offset": limit,
            "extensions": "all",
        }

        try:
            logger.info(f"正在请求高德 API: {keyword} @ {city}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()

                result = response.json()

                # 检查高德业务状态码
                if result.get("status") == "0":
                    error_info = result.get("info", "未知错误")
                    error_code = result.get("infocode", "")
                    raise RuntimeError(f"高德 API 返回错误 [{error_code}]: {error_info}")

                if result.get("info") != "OK":
                    raise RuntimeError(f"高德 API 响应异常: {result.get('info')}")

                pois = result.get("pois", [])

                if not pois:
                    logger.warning(f"API 返回成功，但未找到关于 '{keyword}' 的景点。")
                    return []

                # 格式化数据
                attractions = []
                for poi in pois:
                    biz_ext = poi.get("biz_ext", {})
                    attraction = {
                        "name": poi.get("name", ""),
                        "address": poi.get("address", ""),
                        "type": poi.get("type", ""),
                        "rating": biz_ext.get("rating", "暂无评分"),
                        "cost": biz_ext.get("cost", "价格面议"),
                        "tel": poi.get("tel", "无电话"),
                        "location": poi.get("location", ""),
                    }
                    attractions.append(attraction)

                logger.info(f"成功获取 {len(attractions)} 个景点数据")
                return attractions

        except httpx.TimeoutException:
            raise RuntimeError("网络请求超时：高德地图 API 响应过慢，请检查网络连接。")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP 请求失败：状态码 {e.response.status_code}")
        except Exception as e:
            logger.error(f"发生未知错误: {e}")
            raise RuntimeError(f"景点查询失败: {str(e)}")

    async def search_hotels(
        self, keyword: str, city: str = "全国", limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索酒店/住宿信息

        Args:
            keyword: 搜索关键词，如"北京酒店"、"如家"
            city: 城市名称，如"北京"、"上海"，默认为"全国"
            limit: 返回结果数量限制，默认5条

        Returns:
            List[Dict[str, Any]]: 酒店信息列表，每个酒店包含：
                - name: 酒店名称
                - address: 详细地址
                - rating: 评分
                - cost: 参考价格
                - tel: 联系电话
                - facility: 设施信息

        Raises:
            RuntimeError: API调用失败或返回错误时抛出

        Example:
            [
                {
                    "name": "北京饭店",
                    "address": "北京市东城区东长安街33号",
                    "rating": "4.5",
                    "cost": "800元",
                    "tel": "010-65137788",
                    "facility": "免费WiFi;停车场;餐厅"
                }
            ]
        """
        if not self.api_key:
            raise RuntimeError("配置错误：未在 env.yaml 中配置 'amap_key'，无法调用高德地图 API。")

        # 自动补全关键词
        hotel_keywords = ["酒店", "宾馆", "民宿", "住宿", "客栈"]
        if not any(k in keyword for k in hotel_keywords):
            keyword = f"{keyword} 酒店"
            logger.info(f"检测到关键词非酒店类，自动修正为：{keyword}")

        params = {
            "key": self.api_key,
            "keywords": keyword,
            "city": city,
            "types": "住宿服务|宾馆|酒店|民宿",
            "offset": limit,
            "extensions": "all",
        }

        try:
            logger.info(f"正在搜索酒店: {keyword} @ {city}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()

                result = response.json()

                # 检查高德业务状态码
                if result.get("status") == "0":
                    error_info = result.get("info", "未知错误")
                    raise RuntimeError(f"高德 API 返回错误: {error_info}")

                pois = result.get("pois", [])

                if not pois:
                    logger.warning(f"未找到关于 '{keyword}' 的酒店信息。")
                    return []

                hotels = []
                for poi in pois:
                    biz_ext = poi.get("biz_ext", {})
                    hotel = {
                        "name": poi.get("name", ""),
                        "address": poi.get("address", ""),
                        "rating": biz_ext.get("rating", "暂无评分"),
                        "cost": biz_ext.get("cost", "价格面议"),
                        "tel": poi.get("tel", "无电话"),
                        "facility": poi.get("facility", ""),
                    }
                    hotels.append(hotel)

                logger.info(f"成功获取 {len(hotels)} 个酒店数据")
                return hotels

        except httpx.TimeoutException:
            raise RuntimeError("网络请求超时：高德地图 API 响应过慢，请检查网络连接。")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP 请求失败：状态码 {e.response.status_code}")
        except Exception as e:
            logger.error(f"发生未知错误: {e}")
            raise RuntimeError(f"酒店查询失败: {str(e)}")

    async def get_weather_simple(self, city: str) -> Dict[str, Any]:
        """
        获取城市天气信息（复用天气API）

        Args:
            city: 城市名称，如"北京"、"上海"

        Returns:
            Dict[str, Any]: 天气信息，包含实时天气和预报

        Raises:
            RuntimeError: 天气查询失败时抛出

        Note:
            此方法依赖 juhe_weather_api_key 配置
        """
        from modules.YA_Secrets.secrets_parser import get_secret

        weather_key = get_secret("juhe_weather_api_key")

        if not weather_key:
            raise RuntimeError("未配置天气 API Key，请在 env.yaml 中配置 'juhe_weather_api_key'")

        url = get_config("weather.api_url", "http://apis.juhe.cn/simpleWeather/query")
        params = {"city": city, "key": weather_key}

        try:
            logger.info(f"正在查询天气: {city}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("error_code") == 0:
                    result = data.get("result", {})
                    return result
                else:
                    error_msg = data.get("reason", "未知错误")
                    raise RuntimeError(f"天气查询失败: {error_msg}")

        except httpx.TimeoutException:
            raise RuntimeError("天气 API 请求超时")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"天气 API HTTP 请求失败: {e.response.status_code}")
        except Exception as e:
            logger.error(f"天气查询失败: {e}")
            raise RuntimeError(f"天气查询失败: {str(e)}")


# 创建单例实例
travel_api = TravelAPI()