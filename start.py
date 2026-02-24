"""
MCP + Web 统一启动脚本
同时启动MCP服务器和FastAPI Web应用
"""

import asyncio
import subprocess
import sys

import uvicorn
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("startup")


async def start_mcp_server():
    """启动MCP服务器（SSE模式）- 不捕获输出"""
    logger.info("正在启动MCP服务器...")

    # 检查config.yaml中transport配置
    import yaml

    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    transport_type = config.get("transport", {}).get("type", "sse")
    host = config.get("transport", {}).get("host", "0.0.0.0")
    port = config.get("transport", {}).get("port", 12345)

    logger.info(f"MCP服务器配置: {transport_type}://{host}:{port}")

    # ✅ 关键修改：不捕获输出，直接启动
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=None,  # 不捕获，输出到控制台
        stderr=None,  # 不捕获，输出到控制台
        text=True,
    )

    # 给服务器一点启动时间
    await asyncio.sleep(2)
    logger.info("MCP服务器启动成功 (PID: %d)", process.pid)

    return process


def start_web_server():
    """启动FastAPI Web服务器"""
    logger.info("正在启动Web服务器...")
    uvicorn.run(
        "web_app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )


async def main():
    """主启动函数"""
    logger.info("=" * 50)
    logger.info("启动 MCP + Web 集成系统")
    logger.info("=" * 50)

    # 启动MCP服务器
    mcp_process = await start_mcp_server()

    try:
        # 启动Web服务器
        start_web_server()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    finally:
        # 关闭MCP服务器
        if mcp_process:
            mcp_process.terminate()
            mcp_process.wait(timeout=5)
            logger.info("MCP服务器已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已退出")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        sys.exit(1)
