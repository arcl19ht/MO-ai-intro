"""
旅游助手工具定义 
"""

from typing import Any
from tools import YA_MCPServer_Tool
from core.travel_api import travel_api
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("travel_tool")


@YA_MCPServer_Tool(
    name="search_attractions",
    title="Search Tourist Attractions",
    description="搜索指定城市的真实旅游景点信息。"
    "\n【参数】keyword: 景点名; city: 城市名。"
    "\n【注意】如果 API Key 未配置或网络错误，将返回错误信息。",
)
async def search_attractions(keyword: str, city: str = "全国") -> Any:
    """搜索景点入口"""
    logger.info(f"收到工具调用：search_attractions({keyword}, {city})")
    
    try:
        data = await travel_api.search_attractions(keyword, city)
        
        if not data:
            return {"success": True, "message": f"未找到关于 '{keyword}' 的景点信息，请尝试更换关键词。", "data": []}
        
        return {"success": True, "count": len(data), "data": data}
        
    except RuntimeError as e:
        # 捕获核心层抛出的具体错误，返回给 AI
        error_msg = str(e)
        logger.error(f"工具执行失败: {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        return {"success": False, "error": f"发生未知错误: {str(e)}"}


@YA_MCPServer_Tool(
    name="search_hotels",
    title="Search Hotels",
        description="搜索指定城市的酒店、宾馆、民宿等住宿信息。"
    "\n\n【【📢 返回数据展示规则 - 必须遵守】"
    "- **必须列出所有搜索结果**，哪怕有 5 家就列 5 家，**严禁省略**！"
    "- 如果某家酒店缺少评分、电话或价格，**请直接显示‘暂无’或‘未知’**，**绝对不要**因此隐藏该酒店或只展示部分酒店。"
    "- **不要**添加‘系统返回信息有限’、‘建议去其他平台查看’等多余的道歉或解释性文字。"
    "- **直接输出表格或清晰列表**，包含：名称、地址、评分（若无则填暂无）、电话（若无则填暂无）。"
    "\n【示例输出格式】"
    "1. **XX 酒店** | 地址：XXX | 评分：4.5 | 电话：010-xxx (若暂无则写：评分：暂无)"
    "2. **YY 宾馆** | 地址：XXX | 评分：暂无 | 电话：暂无"

)
async def search_hotels_tool(keyword: str, city: str = "全国") -> Any:
    """搜索酒店入口"""
    logger.info(f"搜索酒店: {keyword} @ {city}")
    try:
        data = await travel_api.search_hotels(keyword, city)
        return {"success": True, "count": len(data), "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@YA_MCPServer_Tool(
    name="get_travel_weather",
    title="Get Travel Weather",
    description="查询旅游目的地的实时天气。参数：city(城市名)。",
)
async def get_travel_weather_tool(city: str) -> Any:
    """查询天气入口"""
    logger.info(f"查询天气: {city}")
    try:
        data = await travel_api.get_weather_simple(city)
        if "error" in data:
            return {"success": False, "error": data["error"]}
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# @YA_MCPServer_Tool(
#     name="plan_trip",
#     title="Plan Trip Smartly",
#     description="智能旅游规划：一键获取目的地的天气、热门景点和住宿建议。参数：destination(目的地城市)。",
# )
# async def plan_trip_tool(destination: str) -> Any:
#     """智能规划入口：组合调用多个 API"""
#     logger.info(f"智能规划行程: {destination}")
#     try:
#         # 1. 并行获取天气和景点 (异步优势！)
#         import asyncio
#         weather_task = travel_api.get_weather_simple(destination)
#         spots_task = travel_api.search_attractions(destination, destination, limit=3)
#         hotels_task = travel_api.search_hotels("酒店", destination, limit=2)
        
#         weather_res, spots_res, hotels_res = await asyncio.gather(
#             weather_task, spots_task, hotels_task, return_exceptions=True
#         )

#         # 2. 处理结果
#         weather_info = weather_res if not isinstance(weather_res, Exception) else "天气数据暂缺"
#         spots_info = spots_res if not isinstance(spots_res, Exception) else []
#         hotels_info = hotels_res if not isinstance(hotels_res, Exception) else []

#         # 3. 生成综合建议
#         suggestion = f"🗺️ **{destination} 智能行程简报**:\n\n"
        
#         if isinstance(weather_info, dict):
#             w = weather_info.get("realtime", {})
#             suggestion += f"🌤️ **天气**: {w.get('info', '未知')} ({w.get('temperature', '?')}°C)\n"
#             if "雨" in str(w.get('info', '')):
#                 suggestion += "   💡 提示: 有雨，记得带伞!\n"
        
#         suggestion += f"\n🏞️ **推荐景点** ({len(spots_info)}个):\n"
#         for spot in spots_info:
#             suggestion += f"   - {spot['name']} ({spot.get('rating', '?')})\n"
            
#         suggestion += f"\n🏨 **推荐住宿** ({len(hotels_info)}个):\n"
#         for hotel in hotels_info:
#             suggestion += f"   - {hotel['name']} ({hotel.get('cost', '?')})\n"
            
#         return {"success": True, "plan": suggestion}

#     except Exception as e:
#         return {"success": False, "error": f"规划失败: {str(e)}"}