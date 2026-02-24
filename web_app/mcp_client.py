"""
MCP客户端模块
功能：封装与MCP Server的通信（SSE模式）
"""

import asyncio
from typing import Any, Dict, Optional, List
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    """MCP服务器客户端封装 - SSE模式"""

    def __init__(self, server_url: str = "http://127.0.0.1:12345"):
        """
        初始化MCP客户端

        Args:
            server_url: MCP服务器的SSE端点URL
        """
        self.server_url = server_url
        self.session: Optional[ClientSession] = None

    @asynccontextmanager
    async def get_session(self):
        """获取MCP会话的上下文管理器（SSE模式）"""
        retry_count = 3
        last_error = None

        for i in range(retry_count):
            try:
                if i > 0:
                    await asyncio.sleep(1)

                async with sse_client(self.server_url) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        yield session
                        return
            except Exception as e:
                last_error = e
                if i < retry_count - 1:
                    continue

        raise ConnectionError(f"无法连接到MCP服务器 {self.server_url}: {last_error}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用工具列表"""
        try:
            async with self.get_session() as session:
                result = await session.list_tools()
                tools = []
                for tool in result.tools:
                    tools.append(
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema,
                        }
                    )
                return tools
        except Exception as e:
            print(f"❌ 列出工具失败: {e}")
            return []

    # ============ 资源相关方法 ============

    async def list_resources(self) -> List[Dict[str, Any]]:
        """获取所有可用静态资源列表"""
        try:
            async with self.get_session() as session:
                result = await session.list_resources()
                resources = []
                for resource in result.resources:
                    resources.append(
                        {
                            "name": resource.name,
                            "uri": resource.uri,
                            "description": getattr(resource, "description", ""),
                            "mimeType": getattr(resource, "mimeType", "text/plain"),
                            "type": "static",  # 标记为静态资源
                        }
                    )
                return resources
        except Exception as e:
            print(f"❌ 列出资源失败: {e}")
            return []

    async def list_resource_templates(self) -> List[Dict[str, Any]]:
        """获取所有可用资源模板列表"""
        try:
            async with self.get_session() as session:
                result = await session.list_resource_templates()
                templates = []
                for template in result.resourceTemplates:
                    templates.append(
                        {
                            "name": getattr(template, "name", ""),
                            "uriTemplate": template.uriTemplate,  # 包含参数的URI模板
                            "description": getattr(template, "description", ""),
                            "mimeType": getattr(template, "mimeType", "text/plain"),
                            "type": "template",  # 标记为模板资源
                        }
                    )
                return templates
        except Exception as e:
            print(f"❌ 列出资源模板失败: {e}")
            return []

    async def read_resource(self, uri: str) -> str:
        """读取资源（支持静态资源和模板资源）"""
        async with self.get_session() as session:
            try:
                result = await session.read_resource(uri)
                if result.contents and len(result.contents) > 0:
                    content = result.contents[0]
                    # 处理不同类型的资源内容
                    if hasattr(content, "text"):
                        return content.text
                    elif hasattr(content, "blob"):
                        return str(content.blob)
                    else:
                        return str(content)
                return "资源读取成功，但无返回内容"
            except Exception as e:
                raise RuntimeError(f"读取资源 {uri} 失败: {str(e)}")

    # ============ 提示词相关方法 ============

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """获取所有可用提示词模板"""
        try:
            async with self.get_session() as session:
                result = await session.list_prompts()
                prompts = []
                for prompt in result.prompts:
                    prompts.append(
                        {
                            "name": prompt.name,
                            "description": getattr(prompt, "description", ""),
                            "arguments": [
                                {
                                    "name": arg.name,
                                    "description": getattr(arg, "description", ""),
                                    "required": getattr(arg, "required", False),
                                }
                                for arg in getattr(prompt, "arguments", [])
                            ],
                        }
                    )
                return prompts
        except Exception as e:
            print(f"❌ 列出提示词失败: {e}")
            return []

    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """获取提示词模板内容"""
        async with self.get_session() as session:
            try:
                result = await session.get_prompt(name, arguments=arguments)
                if result.messages and len(result.messages) > 0:
                    # 返回第一个消息的内容
                    return result.messages[0].content.text
                return "提示词获取成功，但无返回内容"
            except Exception as e:
                raise RuntimeError(f"获取提示词 {name} 失败: {str(e)}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """调用MCP工具"""
        async with self.get_session() as session:
            try:
                result = await session.call_tool(tool_name, arguments=arguments)
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return "工具执行成功，但无返回内容"
            except Exception as e:
                raise RuntimeError(f"调用工具 {tool_name} 失败: {str(e)}")
