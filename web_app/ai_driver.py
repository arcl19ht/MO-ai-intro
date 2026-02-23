"""
AI驱动模块
功能：连接DeepSeek API，处理用户输入，决策是否调用MCP工具
"""

import json
from typing import List, Dict, Any, Optional

import httpx
from modules.YA_Secrets.secrets_parser import get_secret
from modules.YA_Common.utils.logger import get_logger

from .mcp_client import MCPClient

logger = get_logger("ai_driver")


class AIDriver:
    """AI驱动核心类"""

    def __init__(self, mcp_client: MCPClient):
        """
        初始化AI驱动

        Args:
            mcp_client: MCP客户端实例
        """
        self.mcp_client = mcp_client
        self.api_key = get_secret("deepseek_api_key")
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-chat"

        # 初始化时获取MCP服务器信息
        self.mcp_tools_info = []
        self.mcp_resources_info = []
        self.mcp_prompts_info = []

    async def initialize(self):
        """初始化：获取MCP服务器信息"""
        try:
            self.mcp_tools_info = await self.mcp_client.list_tools()
            self.mcp_resources_info = await self.mcp_client.list_resources()
            # ✅ 新增：获取资源模板
            self.mcp_resource_templates = await self.mcp_client.list_resource_templates()
            self.mcp_prompts_info = await self.mcp_client.list_prompts()
            logger.info(f"MCP初始化成功，可用工具: {[t['name'] for t in self.mcp_tools_info]}")
            logger.info(f"可用静态资源: {[r['name'] for r in self.mcp_resources_info]}")
            logger.info(f"可用资源模板: {[t['name'] for t in self.mcp_resource_templates]}")
        except Exception as e:
            logger.error(f"MCP初始化失败: {e}")
            self.mcp_tools_info = []
            self.mcp_resources_info = []
            self.mcp_resource_templates = []  # ✅ 新增
            self.mcp_prompts_info = []

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词，告诉AI它可以使用的MCP能力
        """
        prompt = """你是一个智能助手，可以通过MCP协议调用外部工具来帮助用户。

    当前MCP服务器的可用能力："""

        # 添加工具信息
        if self.mcp_tools_info:
            prompt += "\n\n## 可用工具"
            for tool in self.mcp_tools_info:
                prompt += f"\n- {tool['name']}: {tool.get('description', '无描述')}"
                if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                    params = list(tool['inputSchema']['properties'].keys())
                    prompt += f" 参数: {', '.join(params)}"
        
        # 添加静态资源信息
        if self.mcp_resources_info:
            prompt += "\n\n## 可用静态资源（直接读取）"
            for r in self.mcp_resources_info:
                prompt += f"\n- {r['name']}: {r.get('description', '')}"
                prompt += f"\n  URI: {r['uri']}"

        # 添加资源模板信息
        if hasattr(self, 'mcp_resource_templates') and self.mcp_resource_templates:
            prompt += "\n\n## 可用资源模板（需要参数）"
            for t in self.mcp_resource_templates:
                prompt += f"\n- {t['name']}: {t.get('description', '')}"
                prompt += f"\n  URI模板: {t['uriTemplate']}"
                prompt += "\n  使用时需将 {path} 替换为实际路径"
        
        # 添加提示词模板信息
        if self.mcp_prompts_info:
            prompt += "\n\n## 可用提示词模板（对话模板）"
            for p in self.mcp_prompts_info[:3]:
                prompt += f"\n- {p['name']}: {p.get('description', '无描述')}"
        
        # ============ 核心调用规则 ============
        prompt += """

    ## 调用规则（严格遵循）

    ### 1. 工具调用格式
    ```json
    {"action": "call_tool", "tool": "工具名", "arguments": {"参数": "值"}}
    ```

    ### 2. 资源读取格式
    ```json
    {"action": "read_resource", "uri": "资源URI"}
    ```

    ### 3. 提示词调用格式
    ```json
    {"action": "use_prompt", "prompt": "模板名", "arguments": {"参数": "值"}}
    ```

    ## 执行流程
    1. **用户不可见**：输出上述JSON代码块
    2. **系统执行**：自动调用工具/资源/提示词
    3. **用户可见**：基于执行结果，用自然语言回复

    ## 示例

    用户：你好
    你：
    ```json
    {"action": "call_tool", "tool": "greeting_tool", "arguments": {"name": "用户"}}
    ```
    系统返回："Hello, 用户！"
    你回复："你好！很高兴见到你！"

    用户：读取服务器配置
    你：
    ```json
    {"action": "read_resource", "uri": "config://server/info"}
    ```
    系统返回：配置信息
    你回复："当前服务器配置为..."

    用户：帮我写个生日祝福
    你：
    ```json
    {"action": "use_prompt", "prompt": "birthday", "arguments": {"name": "张三"}}
    ```
    系统返回：祝福语模板
    你回复："祝张三生日快乐..."

    ## 绝对禁止
    ❌ 直接把JSON显示给用户
    ❌ 在回复中包含技术细节
    ❌ 解释你调用了什么工具

    ✅ 只用自然语言回复最终结果"""
        
        return prompt
    
    async def process_message(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            message: 用户输入的消息
            history: 对话历史
            
        Returns:
            Dict: 包含响应内容和可能的工具调用结果
        """
        if history is None:
            history = []
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *history,
            {"role": "user", "content": message}
        ]
        
        # 调用DeepSeek API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"DeepSeek API调用失败: {response.text}")
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
        
        # 解析AI响应，检查是否是工具调用指令
        tool_call_result = None
        final_response = ai_response
        
        # 尝试解析JSON格式的工具调用
        import re
        json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
        if json_match:
            try:
                cmd = json.loads(json_match.group(1))
                action = cmd.get("action")
                
                if action == "call_tool":
                    tool_name = cmd.get("tool")
                    arguments = cmd.get("arguments", {})
                    
                    # 调用MCP工具
                    tool_result = await self.mcp_client.call_tool(tool_name, arguments)
                    tool_call_result = {
                        "type": "tool_call",
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": tool_result
                    }
                    
                    # 将工具调用结果发给AI，生成最终回答
                    messages.append({"role": "assistant", "content": ai_response})
                    messages.append({
                        "role": "user", 
                        "content": f"工具调用结果：{tool_result}\n请基于这个结果给用户一个友好的回答。"
                    })
                    
                    # 再次调用API获取最终回答
                    final_response = await self._get_final_answer(messages)
                    
                elif action == "read_resource":
                    uri = cmd.get("uri")
                    resource_content = await self.mcp_client.read_resource(uri)
                    tool_call_result = {
                        "type": "read_resource",
                        "uri": uri,
                        "result": resource_content
                    }
                    
                    # 类似地处理资源读取结果
                    messages.append({"role": "assistant", "content": ai_response})
                    messages.append({
                        "role": "user",
                        "content": f"资源内容：{resource_content}\n请基于这个内容给用户一个友好的回答。"
                    })
                    final_response = await self._get_final_answer(messages)
                    
            except json.JSONDecodeError as e:
                logger.error(f"解析工具调用JSON失败: {e}")
            except Exception as e:
                logger.error(f"执行工具调用失败: {e}")
                tool_call_result = {"type": "error", "message": str(e)}
        
        return {
            "response": final_response,
            "tool_call": tool_call_result,
            "raw_ai_response": ai_response
        }

    async def _get_final_answer(self, messages: List[Dict]) -> str:
        """获取最终的AI回答"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False
                }
            )
            result = response.json()
            return result["choices"][0]["message"]["content"]
