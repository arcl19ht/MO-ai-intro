"""
FastAPI Web应用主模块
功能：提供Web界面和API接口
"""

from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from modules.YA_Common.utils.logger import get_logger

from .mcp_client import MCPClient
from .ai_driver import AIDriver

logger = get_logger("web_app")

# 全局实例
mcp_client = MCPClient()
ai_driver = AIDriver(mcp_client)


class ChatMessage(BaseModel):
    """聊天消息模型"""

    role: str
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""

    message: str
    history: List[Dict[str, str]] = []


class ChatResponse(BaseModel):
    """聊天响应模型"""

    response: str
    tool_call: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("正在初始化AI驱动...")
    await ai_driver.initialize()
    logger.info("AI驱动初始化完成")
    yield
    # 关闭时清理
    logger.info("正在关闭应用...")


# 创建FastAPI应用
app = FastAPI(
    title="MCP + DeepSeek 聊天界面",
    description="通过Web界面与MCP服务器和DeepSeek AI对话",
    version="1.0.0",
    lifespan=lifespan,
)

# 设置模板
templates = Jinja2Templates(directory="web_app/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """提供聊天界面"""
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "MCP AI 助手"}
    )


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "ok",
        "mcp_connected": len(ai_driver.mcp_tools_info) > 0,
        "tools_count": len(ai_driver.mcp_tools_info),
        "resources_count": len(ai_driver.mcp_resources_info),
        "resource_templates_count": len(ai_driver.mcp_resource_templates), 
        "prompts_count": len(ai_driver.mcp_prompts_info),
        "tools": ai_driver.mcp_tools_info,
        "resources": ai_driver.mcp_resources_info,
        "resource_templates": ai_driver.mcp_resource_templates, 
        "prompts": ai_driver.mcp_prompts_info
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        result = await ai_driver.process_message(
            message=request.message, history=request.history
        )

        return ChatResponse(
            response=result["response"], tool_call=result.get("tool_call")
        )
    except Exception as e:
        logger.error(f"处理聊天请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    """获取可用工具列表"""
    return {"tools": ai_driver.mcp_tools_info}


@app.get("/api/resources")
async def list_resources():
    """获取可用资源列表"""
    return {"resources": ai_driver.mcp_resources_info}


@app.get("/api/prompts")
async def list_prompts():
    """获取可用提示词列表"""
    return {"prompts": ai_driver.mcp_prompts_info}
