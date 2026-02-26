"""
MCP连接测试脚本
独立测试MCP服务器是否可连接
"""

import asyncio
import sys
from mcp.client.sse import sse_client
from mcp import ClientSession


async def test_connection():
    """测试MCP服务器连接"""
    url = "http://127.0.0.1:12345"
    print(f"正在测试连接: {url}")

    try:
        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ SSE连接成功")

                # 测试列出工具
                tools = await session.list_tools()
                print(f"✅ 获取工具列表成功，发现 {len(tools.tools)} 个工具")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description}")

                return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("MCP服务器连接测试")
    print("=" * 50)
    print("请确保MCP服务器已在另一个终端运行:")
    print("  uv run python server.py")
    print("=" * 50)

    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
