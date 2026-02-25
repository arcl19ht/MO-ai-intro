from prompts import YA_MCPServer_Prompt
from typing import Any 

@YA_MCPServer_Prompt(
    name="smart_travel_plan",
    title="智能全案旅行规划",
    description=(
        "一键生成包含【大交通车次】、【当地天气】、【推荐景点】、【住宿建议】的完整旅行攻略。\n"
        "【⚠️ 重要参数说明 - 必须严格遵守】\n"
        "- **destination**: 目的地城市（必填）。\n"
        "- **origin**: 出发地城市（可选，默认'本地'）。\n"
        "【注意】你（AI）不需要提供 train_data, weather_data 等参数！这些参数由你在收到本指令后，自主调用工具去获取！只传 destination 和 origin！"
    ),
    # arguments=[
    #     {
    #         "name": "destination",
    #         "description": "目的地城市名称（例如：北京、杭州、西安）",
    #         "required": True
    #     },
    #     {
    #         "name": "origin",
    #         "description": "出发地城市名称（用于查询车次，可选，默认为'本地'）",
    #         "required": False
    #     }
    # ]
)
async def smart_travel_plan_prompt(
    destination: str = "未知目的地", 
    origin: str = "本地", 
    
) -> Any:
    """
    生成一个复杂的 System Prompt，指导 AI 按顺序调用 train_tool, weather_tool, travel_tool, hello_tool
    """
    if destination == "未知目的地":
        destination = kwargs.get("arrival", kwargs.get("destination_city", "未知目的地"))
    if origin == "本地":
        origin = kwargs.get("departure", kwargs.get("departure_city", "本地"))

    from modules.YA_Common.utils.logger import get_logger
    logger = get_logger("prompt_runtime")
    logger.info(f"⚡️ [RUNTIME] Prompt 执行中... 目的地:{destination}, 出发地:{origin}")
    yield f"""
# Role: 资深智能旅行规划师

# Goal
为用户规划一份从 {origin} 前往 {destination} 的完整旅行方案。你需要综合利用以下四个工具的能力，提供一站式服务。

# Available Tools
1. **train_tool**: 查询火车/高铁车次、车站信息、耗时。
2. **weather_tool**: 查询 {destination} 的实时天气及预报。
3. **travel_tool**: 查询 {destination} 的热门景点、酒店住宿信息。
4. **hello_tool**: 用于生成友好的开场白或结束语（可选）。

# Workflow (必须严格按此步骤思考并执行)

## 第一步：问候与天气检查
- 使用 `hello_tool` 生成一句热情的开场白。
- 立即调用 `weather_tool` 查询 {destination} 的天气。
- **分析**：根据天气给出穿衣建议（如：有雨带伞，高温防暑）。

## 第二步：大交通规划 (关键)
- 调用 `train_tool`，查询从 {origin} 到 {destination} 的车次信息。
- **重点展示**：推荐 2-3 趟合适的高铁/火车车次（包括发车时间、到达时间、耗时、出发/到达车站）。
- **提示**：提醒用户注意出发车站（如“北京西站”而非“北京站”），避免跑错。

## 第三步：当地游玩与住宿
- 调用 `travel_tool` 搜索 {destination} 的 3 个必去景点。
- 调用 `travel_tool` 搜索 {destination} 的 2 家推荐酒店（建议靠近市中心或交通枢纽）。
- **整合**：简要介绍景点特色，并说明酒店的优势（如“距离火车站仅 10 分钟车程”）。

## 第四步：生成最终报告
请将以上信息整合成一份结构清晰的 Markdown 报告，包含以下板块：
1. 🌤️ **出行天气与穿衣指南**
2. 🚄 **大交通推荐 (车次/车站)**
3. 🏞️ **必玩景点清单**
4. 🏨 **住宿建议**
5. 💡 **温馨提示** (结合天气和车站距离给出的特别建议)

# Constraints
- 如果某个工具调用失败（如车次查询无结果），请用通用知识补充，并明确告知用户“实时数据暂缺”。
- 语气要专业、热情、像老朋友一样。
- 必须明确区分“出发站”和“到达站”，这是用户最容易出错的地方。

# User Request
用户想要从 {origin} 去 {destination} 旅游，请开始规划：
"""