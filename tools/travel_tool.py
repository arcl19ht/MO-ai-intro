"""
旅游助手工具定义
提供景点搜索、酒店查询、天气查询和智能行程规划功能
"""

from typing import Any, Dict, List, Optional

from tools import YA_MCPServer_Tool
from core.travel_api import travel_api
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("travel_tool")


@YA_MCPServer_Tool(
    name="search_attractions",
    title="Search Tourist Attractions",
    description="根据关键词和城市搜索真实的旅游景点信息。"
    "\n【重要参数说明】"
    "\n- keyword: 必填，景点名称或关键词，如'故宫'、'西湖'、'博物馆'"
    "\n- city: 可选，城市名称，如'北京'、'上海'，默认为'全国'（在全国范围搜索）"
    "\n\n【返回数据说明】"
    "\n- 每个景点包含：名称、地址、类型、评分、参考价格、电话、经纬度"
    "\n- 如果某个字段缺失，会显示'暂无评分'、'价格面议'等默认值"
    "\n\n【使用示例】"
    "\n- 搜索北京故宫：keyword='故宫', city='北京'"
    "\n- 搜索杭州西湖：keyword='西湖', city='杭州'"
    "\n- 全国搜索博物馆：keyword='博物馆'",
)
async def search_attractions(keyword: str, city: str = "全国") -> Dict[str, Any]:
    """
    搜索指定城市的旅游景点信息

    Args:
        keyword: 景点名称或关键词，例如："故宫"、"西湖"、"博物馆"
        city: 城市名称，例如："北京"、"上海"、"杭州"，默认为"全国"（在全国范围搜索）

    Returns:
        Dict[str, Any]: 包含搜索结果的字典，格式为：
            {
                "success": bool,  # 是否成功
                "count": int,     # 找到的景点数量（成功时存在）
                "data": list,     # 景点列表（成功时存在），每个景点包含：
                    - name: 景点名称
                    - address: 详细地址
                    - type: 景点类型
                    - rating: 评分（如"4.8"或"暂无评分"）
                    - cost: 参考价格（如"60元"或"价格面议"）
                    - tel: 联系电话（如"010-12345678"或"无电话"）
                    - location: 经纬度坐标
                "message": str,   # 提示信息（如未找到景点时）
                "error": str      # 错误信息（失败时存在）
            }

    Raises:
        不会直接抛出异常，所有错误都会包装在返回字典的 error 字段中

    Example:
        成功示例：
        {
            "success": True,
            "count": 2,
            "data": [
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
        }
        
        失败示例：
        {
            "success": False,
            "error": "配置错误：未在 env.yaml 中配置 'amap_key'，无法调用高德地图 API。"
        }
    """
    logger.info(f"收到工具调用：search_attractions(keyword={keyword}, city={city})")

    try:
        data = await travel_api.search_attractions(keyword, city)

        if not data:
            return {
                "success": True,
                "count": 0,
                "message": f"未找到关于 '{keyword}' 的景点信息，请尝试更换关键词或城市。",
                "data": [],
            }

        return {"success": True, "count": len(data), "data": data}

    except RuntimeError as e:
        # 捕获核心层抛出的具体错误，返回给 AI
        error_msg = str(e)
        logger.error(f"工具执行失败: {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return {"success": False, "error": f"发生未知错误: {str(e)}"}


@YA_MCPServer_Tool(
    name="search_hotels",
    title="Search Hotels",
    description="搜索指定城市的酒店、宾馆、民宿等住宿信息。"
    "\n【重要参数说明】"
    "\n- keyword: 必填，酒店名称或关键词，如'如家'、'希尔顿'、'民宿'"
    "\n- city: 可选，城市名称，如'北京'、'上海'，默认为'全国'"
    "\n\n【自动优化】"
    "\n- 如果关键词不包含'酒店'、'宾馆'等词语，系统会自动添加'酒店'后缀"
    "\n\n【返回数据说明】"
    "\n- 每个酒店包含：名称、地址、评分、参考价格、电话、设施信息"
    "\n- 如果某个字段缺失，会显示'暂无评分'、'价格面议'等默认值"
    "\n\n【展示规则】"
    "\n- **必须列出所有搜索结果**，即使有10家也要全部列出，严禁省略"
    "\n- 如果某家酒店缺少信息，直接显示'暂无'，**不要**因此隐藏该酒店"
    "\n- **不要**添加'系统返回信息有限'等解释性文字"
    "\n- **直接输出清晰列表**，推荐使用序号和分隔符"
    "\n\n【示例输出格式】"
    "\n1. **如家酒店** | 地址：北京朝阳区XX路 | 评分：4.2 | 电话：010-12345678 | 价格：300元起"
    "\n2. **XX民宿** | 地址：杭州西湖区XX路 | 评分：暂无 | 电话：暂无 | 价格：500元起",
)
async def search_hotels(keyword: str, city: str = "全国") -> Dict[str, Any]:
    """
    搜索指定城市的酒店住宿信息

    Args:
        keyword: 酒店名称或关键词，例如："如家"、"希尔顿"、"民宿"
        city: 城市名称，例如："北京"、"上海"、"杭州"，默认为"全国"

    Returns:
        Dict[str, Any]: 包含搜索结果的字典，格式为：
            {
                "success": bool,  # 是否成功
                "count": int,     # 找到的酒店数量（成功时存在）
                "data": list,     # 酒店列表（成功时存在），每个酒店包含：
                    - name: 酒店名称
                    - address: 详细地址
                    - rating: 评分（如"4.5"或"暂无评分"）
                    - cost: 参考价格（如"300元"或"价格面议"）
                    - tel: 联系电话（如"010-12345678"或"无电话"）
                    - facility: 设施信息
                "error": str      # 错误信息（失败时存在）
            }

    Raises:
        不会直接抛出异常，所有错误都会包装在返回字典的 error 字段中

    Example:
        成功示例：
        {
            "success": True,
            "count": 2,
            "data": [
                {
                    "name": "如家酒店",
                    "address": "北京市朝阳区XX路",
                    "rating": "4.2",
                    "cost": "300元",
                    "tel": "010-12345678",
                    "facility": "免费WiFi;停车场"
                }
            ]
        }
    """
    logger.info(f"收到工具调用：search_hotels(keyword={keyword}, city={city})")

    try:
        data = await travel_api.search_hotels(keyword, city)

        if not data:
            return {
                "success": True,
                "count": 0,
                "message": f"未找到关于 '{keyword}' 的酒店信息，请尝试更换关键词或城市。",
                "data": [],
            }

        return {"success": True, "count": len(data), "data": data}

    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"工具执行失败: {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return {"success": False, "error": f"发生未知错误: {str(e)}"}


@YA_MCPServer_Tool(
    name="get_travel_weather",
    title="Get Travel Weather",
    description="查询旅游目的地的实时天气信息。"
    "\n【重要参数说明】"
    "\n- city: 必填，城市名称，如'北京'、'上海'、'杭州'"
    "\n\n【返回数据说明】"
    "\n- 包含实时天气：温度、天气状况、湿度、风向风力、空气质量"
    "\n- 如果某个字段缺失，会显示默认值"
    "\n\n【使用示例】"
    "\n- 查询杭州天气：city='杭州'",
)
async def get_travel_weather(city: str) -> Dict[str, Any]:
    """
    查询旅游目的地的实时天气信息

    Args:
        city: 城市名称，例如："北京"、"上海"、"杭州"

    Returns:
        Dict[str, Any]: 包含天气信息的字典，格式为：
            {
                "success": bool,      # 是否成功
                "data": {             # 成功时存在
                    "city": str,      # 城市名称
                    "realtime": {     # 实时天气
                        "temperature": str,  # 温度
                        "info": str,        # 天气状况
                        "humidity": str,    # 湿度
                        "direct": str,      # 风向
                        "power": str,       # 风力
                        "aqi": str          # 空气质量
                    },
                    "future": list     # 未来几天预报
                },
                "error": str          # 错误信息（失败时存在）
            }

    Raises:
        不会直接抛出异常，所有错误都会包装在返回字典的 error 字段中

    Example:
        成功示例：
        {
            "success": True,
            "data": {
                "city": "杭州",
                "realtime": {
                    "temperature": "18",
                    "info": "多云",
                    "humidity": "65",
                    "direct": "东风",
                    "power": "2级",
                    "aqi": "72"
                }
            }
        }
    """
    logger.info(f"收到工具调用：get_travel_weather(city={city})")

    try:
        data = await travel_api.get_weather_simple(city)

        if "error" in data:
            return {"success": False, "error": data["error"]}

        return {"success": True, "data": data}

    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"工具执行失败: {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        logger.error(f"发生未知错误: {e}")
        return {"success": False, "error": f"发生未知错误: {str(e)}"}


@YA_MCPServer_Tool(
    name="plan_trip",
    title="Smart Trip Planner",
    description="智能旅游规划助手：一键获取目的地的天气、热门景点和住宿建议，生成完整行程简报。"
    "\n【重要参数说明】"
    "\n- destination: 必填，目的地城市名称，如'杭州'、'北京'、'成都'"
    "\n\n【功能说明】"
    "\n- 自动组合三个维度的信息：天气、景点、酒店"
    "\n- 每个维度都有容错机制，某个维度失败不影响整体"
    "\n- 根据天气情况给出贴心提示（如下雨提醒带伞）"
    "\n\n【返回数据说明】"
    "\n- 返回格式化的文本简报，包含："
    "\n  * 目的地和当前天气"
    "\n  * 推荐景点列表（含评分）"
    "\n  * 推荐住宿列表（含价格参考）"
    "\n  * 旅途祝福"
    "\n\n【使用示例】"
    "\n- 规划杭州行程：destination='杭州'"
    "\n- 规划北京行程：destination='北京'"
    "\n\n【注意】"
    "\n- 景点默认返回前3个，酒店默认返回前2个"
    "\n- 如果某个维度获取失败，会显示'暂未找到'，不影响其他维度",
)
async def plan_trip(destination: str) -> Dict[str, Any]:
    """
    智能旅游规划：整合天气、景点、酒店信息生成行程简报

    Args:
        destination: 目的地城市名称，例如："杭州"、"北京"、"成都"

    Returns:
        Dict[str, Any]: 包含行程简报的字典，格式为：
            {
                "success": bool,         # 是否成功
                "destination": str,      # 目的地（成功时存在）
                "summary": str,          # 格式化的行程简报文本（成功时存在）
                "error": str             # 错误信息（失败时存在）
            }

    Raises:
        不会直接抛出异常，所有错误都会包装在返回字典的 error 字段中

    Example:
        成功示例：
        {
            "success": True,
            "destination": "杭州",
            "summary": "🗺️ **杭州 智能行程简报**\n\n"
                      "🌤️ **当前天气**: 多云 (18°C)\n"
                      "   💡 *提示：天气不错，适合户外活动！*\n\n"
                      "🏞️ **推荐景点** (3个):\n"
                      "   - **西湖** (评分:4.9)\n"
                      "   - **灵隐寺** (评分:4.7)\n"
                      "   - **宋城** (评分:4.5)\n\n"
                      "🏨 **推荐住宿** (2个):\n"
                      "   - **西湖国宾馆** (800元起)\n"
                      "   - **如家酒店** (300元起)\n\n"
                      "💡 **祝您旅途愉快！**"
        }
        
        失败示例：
        {
            "success": False,
            "error": "行程规划失败: API密钥未配置"
        }
    """
    logger.info(f"收到工具调用：plan_trip(destination={destination})")

    try:
        # --- 1. 获取天气 (带容错) ---
        weather_data = {}
        try:
            weather_data = await travel_api.get_weather_simple(destination)
            if not isinstance(weather_data, dict) or "error" in weather_data:
                weather_data = {"realtime": {"info": "未知", "temperature": "?"}}
        except Exception as e:
            logger.warning(f"天气获取失败: {e}")
            weather_data = {"realtime": {"info": "未知", "temperature": "?"}}

        # --- 2. 获取景点 (带容错) ---
        spots_data = []
        try:
            spots_data = await travel_api.search_attractions(
                destination, destination, limit=3
            )
        except Exception as e:
            logger.warning(f"景点获取失败: {e}")
            spots_data = []

        # --- 3. 获取酒店 (带容错) ---
        hotels_data = []
        try:
            hotels_data = await travel_api.search_hotels(
                destination, destination, limit=2
            )
        except Exception as e:
            logger.warning(f"酒店获取失败: {e}")
            hotels_data = []

        # --- 4. 生成自然语言报告 ---
        report = f"🗺️ **{destination} 智能行程简报**\n\n"

        # 天气部分
        w = weather_data.get("realtime", {})
        weather_info = w.get("info", "未知")
        weather_temp = w.get("temperature", "?")
        report += f"🌤️ **当前天气**: {weather_info} ({weather_temp}°C)\n"

        # 根据天气给出贴心提示
        if "雨" in str(weather_info):
            report += "   💡 *提示：有雨，记得带伞哦！*\n"
        elif "雪" in str(weather_info):
            report += "   💡 *提示：有雪，注意保暖和防滑！*\n"
        elif int(weather_temp) > 30 if weather_temp != "?" else False:
            report += "   💡 *提示：天气较热，注意防晒补水！*\n"
        elif int(weather_temp) < 5 if weather_temp != "?" else False:
            report += "   💡 *提示：天气寒冷，注意保暖！*\n"
        else:
            report += "   💡 *提示：天气不错，适合户外活动！*\n"
        report += "\n"

        # 景点部分
        report += f"🏞️ **推荐景点** ({len(spots_data)}个):\n"
        if spots_data:
            for i, spot in enumerate(spots_data, 1):
                name = spot.get("name", "未知")
                rating = spot.get("rating", "暂无")
                report += f"   {i}. **{name}** (评分:{rating})\n"
        else:
            report += "   - 暂未找到热门景点，建议尝试其他关键词\n"
        report += "\n"

        # 酒店部分
        report += f"🏨 **推荐住宿** ({len(hotels_data)}个):\n"
        if hotels_data:
            for i, hotel in enumerate(hotels_data, 1):
                name = hotel.get("name", "未知")
                cost = hotel.get("cost", "价格面议")
                report += f"   {i}. **{name}** ({cost})\n"
        else:
            report += "   - 暂未找到合适住宿，建议尝试其他关键词\n"

        report += "\n💡 **祝您旅途愉快！**"

        # --- 5. 返回结果 ---
        return {"success": True, "destination": destination, "summary": report}

    except Exception as e:
        logger.error(f"规划任务彻底失败: {e}")
        return {"success": False, "error": f"行程规划失败: {str(e)}"}