"""
旅游助手 API 核心业务模块 
依赖：httpx
"""

import httpx
from typing import Dict, Any, List
from modules.YA_Common.utils.logger import get_logger
from modules.YA_Secrets.secrets_parser import get_secret

logger = get_logger("travel_api")


class TravelAPI:
    """旅游 API 封装类 """

    def __init__(self):
        
        self.api_key = get_secret("amap_key")
        self.base_url = "https://restapi.amap.com/v3/place/text"

        if not self.api_key:
            # 如果没有 Key，记录严重错误
            logger.error("❌ 致命错误：未配置高德地图 API Key (amap_key)")

    async def search_attractions(self, keyword: str, city: str = "全国", limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索景点。失败抛出异常。
        """
        if not self.api_key:
            raise RuntimeError("配置错误：未在 env.yaml 中配置 'amap_key'，无法调用高德地图 API。")

        params = {
            "key": self.api_key,
            "keywords": keyword,
            "city": city,
            "types": "风景名胜|公园广场|旅游景点|历史文化",
            "offset": limit,
            "extensions": "all"
        }

        try:
            logger.info(f"正在请求高德 API: {keyword} @ {city}")
            
            # 纯异步请求
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                
                # 检查 HTTP 状态码 
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
                    attractions.append({
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "type": poi.get("type"),
                        "rating": biz_ext.get("rating", "暂无评分"),
                        "cost": biz_ext.get("cost", "价格面议"),
                        "tel": poi.get("tel", "无电话"),
                        "location": poi.get("location")
                    })
                
                logger.info(f"成功获取 {len(attractions)} 个景点数据")
                return attractions

        except httpx.TimeoutException:
            raise RuntimeError("网络请求超时：高德地图 API 响应过慢，请检查网络连接。")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP 请求失败：状态码 {e.response.status_code}")
        except Exception as e:
            # 捕获其他未知错误并透传
            logger.error(f"发生未知错误: {e}")
            raise RuntimeError(f"景点查询失败: {str(e)}")

    async def search_hotels(self, keyword: str, city: str = "全国", limit: int = 5) -> List[Dict[str, Any]]:
        """
        搜索酒店/住宿信息
        """
        hotel_keywords = ["酒店", "宾馆", "民宿", "住宿", "客栈"]
        if not any(k in keyword for k in hotel_keywords):
            keyword = f"{keyword} 酒店"
            logger.info(f"检测到关键词非酒店类，自动修正为：{keyword}")

        params = {
            "key": self.api_key,
            "keywords": keyword,  # 使用修正后的关键词
            "city": city,
            "types": "住宿服务|宾馆|酒店|民宿", # 扩大一点范围，包含民宿
            "offset": limit,
            "extensions": "all"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                result = response.json()

                if result.get("status") == "0":
                    raise RuntimeError(f"高德 API 错误: {result.get('info')}")

                pois = result.get("pois", [])
                hotels = []
                for poi in pois:
                    biz_ext = poi.get("biz_ext", {})
                    hotels.append({
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "rating": biz_ext.get("rating", "暂无评分"),
                        "cost": biz_ext.get("cost", "价格面议"),
                        "tel": poi.get("tel", "无电话"),
                        "facility": poi.get("facility", "") # 设施信息
                    })
                return hotels

        except Exception as e:
            logger.error(f"搜索酒店失败: {e}")
            raise RuntimeError(f"酒店查询失败: {str(e)}")

    async def get_weather_simple(self, city: str) -> Dict[str, Any]:
        """
        复用您已有的天气 API (假设您之前写好了 weather_api)
        这里做一个简单的封装，或者直接调用之前的逻辑
        为了演示，这里假设您有一个 juhe_weather_key
        """
        from modules.YA_Secrets.secrets_parser import get_secret
        weather_key = get_secret("juhe_weather_api_key")
        
        if not weather_key:
            return {"error": "未配置天气 API Key"}

        url = "http://apis.juhe.cn/simpleWeather/query"
        params = {"city": city, "key": weather_key}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                data = response.json()
                if data.get("error_code") == 0:
                    return data.get("result", {})
                else:
                    raise RuntimeError(data.get("reason", "天气查询失败"))
        except Exception as e:
            raise RuntimeError(f"天气查询失败: {str(e)}")
# 单例
travel_api = TravelAPI()