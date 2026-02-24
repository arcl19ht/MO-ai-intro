"""
AI驱动模块
功能：连接DeepSeek API，处理用户输入，决策是否调用MCP工具
"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

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
        self.mcp_resource_templates = []
        self.mcp_prompts_info = []

    async def initialize(self):
        """初始化：获取MCP服务器信息"""
        try:
            self.mcp_tools_info = await self.mcp_client.list_tools()
            self.mcp_resources_info = await self.mcp_client.list_resources()
            self.mcp_resource_templates = (
                await self.mcp_client.list_resource_templates()
            )
            self.mcp_prompts_info = await self.mcp_client.list_prompts()

            logger.info(f"MCP初始化成功")
            logger.info(f"📦 可用工具: {[t['name'] for t in self.mcp_tools_info]}")
            logger.info(f"📄 静态资源: {[r['name'] for r in self.mcp_resources_info]}")
            logger.info(
                f"🔧 资源模板: {[t['name'] for t in self.mcp_resource_templates]}"
            )
            logger.info(f"💡 提示词模板: {[p['name'] for p in self.mcp_prompts_info]}")
        except Exception as e:
            logger.error(f"MCP初始化失败: {e}")
            self.mcp_tools_info = []
            self.mcp_resources_info = []
            self.mcp_resource_templates = []
            self.mcp_prompts_info = []

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词 - 针对聚合API场景优化
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        prompt = f"""你是一个智能信息聚合助手，可以通过MCP协议调用多个API，为用户提供一站式的信息服务。

当前时间：{current_time}

## 📋 可用能力

### 🔧 工具列表（可执行操作）
"""
        # 添加工具信息
        if self.mcp_tools_info:
            for tool in self.mcp_tools_info:
                prompt += f"\n- **{tool['name']}**: {tool.get('description', '无描述')}"
                if "inputSchema" in tool and "properties" in tool["inputSchema"]:
                    params = []
                    for param_name, param_info in tool["inputSchema"][
                        "properties"
                    ].items():
                        required = param_name in tool["inputSchema"].get("required", [])
                        params.append(f"{param_name}{'*' if required else ''}")
                    prompt += f"\n  参数: {', '.join(params)}"
        else:
            prompt += "\n  (暂无可用工具)"

        # 添加静态资源信息
        if self.mcp_resources_info:
            prompt += "\n\n### 📄 静态资源（可直接读取）"
            for r in self.mcp_resources_info:
                prompt += f"\n- **{r['name']}**: {r.get('description', '')}"
                prompt += f"\n  URI: `{r['uri']}`"

        # 添加资源模板信息
        if hasattr(self, "mcp_resource_templates") and self.mcp_resource_templates:
            prompt += "\n\n### 🔧 资源模板（需传入参数）"
            for t in self.mcp_resource_templates:
                prompt += f"\n- **{t['name']}**: {t.get('description', '')}"
                prompt += f"\n  URI模板: `{t['uriTemplate']}`"

        # 添加提示词模板信息
        if self.mcp_prompts_info:
            prompt += "\n\n### 💡 提示词模板（格式化输出）"
            for p in self.mcp_prompts_info:
                prompt += f"\n- **{p['name']}**: {p.get('description', '无描述')}"

        # ============ 核心调用规则 ============
        prompt += """

## 🎯 核心调用规则

### 1. 工具调用格式
```json
{"action": "call_tool", "tool": "工具名", "arguments": {"参数": "值"}}
```

### 2. 资源读取格式
```json
{"action": "read_resource", "uri": "资源URI（模板资源需填充参数）"}
```

### 3. 提示词调用格式
```json
{"action": "use_prompt", "prompt": "模板名", "arguments": {"参数": "值"}}
```

## 🔄 聚合信息工作流程

当用户需要综合多个信息源时，请按以下步骤执行：

1. **识别需求**：分析用户需要哪些方面的信息
2. **调用工具/资源**：依次获取所需数据
3. **组合信息**：将多个来源的信息整合
4. **格式化输出**：使用提示词模板或自然语言呈现

## 📝 示例场景

### 场景1：每日简报
用户："给我今天的简报"

你的内部思考：
- 需要天气 → 调用天气工具
- 需要新闻 → 调用新闻工具
- 需要日程 → 读取用户日历资源
- 需要模板 → 使用日报模板

执行序列：
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "北京"}}
```
```json
{"action": "call_tool", "tool": "get_news", "arguments": {"category": "technology"}}
```
```json
{"action": "read_resource", "uri": "user://current/schedule"}
```
```json
{"action": "use_prompt", "prompt": "daily_briefing", "arguments": {
    "weather": "...",
    "news": "...",
    "schedule": "..."
}}
```

最终回复用户格式化的简报。

### 场景2：出行建议
用户："明天去上海，有什么建议？"

执行序列：
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "上海", "date": "明天"}}
```
```json
{"action": "read_resource", "uri": "knowledge://city/info/上海"}
```
```json
{"action": "use_prompt", "prompt": "travel_advice", "arguments": {
    "city": "上海",
    "weather": "...",
    "city_info": "..."
}}
```

### 场景3：个性化提醒
用户："提醒我明天带伞"

执行序列：
```json
{"action": "read_resource", "uri": "user://123/preferences"}
```
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "北京", "date": "明天"}}
```
```json
{"action": "use_prompt", "prompt": "reminder_message", "arguments": {
    "weather": "...",
    "user_name": "张三"
}}
```

## ⚠️ 重要规则

### ✅ 必须遵守
- **用户看不到JSON**：所有JSON指令都不可见
- **分步执行**：如需多个信息，分多次调用
- **错误处理**：如果某个API失败，用已有信息尽量回答
- **个性化**：优先使用用户偏好资源

### ❌ 绝对禁止
- 直接把JSON显示给用户
- 在回复中提及"我调用了XX工具"
- 返回技术细节或原始数据

### 💡 信息组合技巧
- **天气+新闻+日程** = 每日简报
- **天气+城市知识+交通** = 出行建议
- **用户偏好+实时数据+模板** = 个性化提醒
- **历史数据+当前数据+预测** = 趋势分析

记住：你的目标是让用户感觉在和一个全能助手对话，所有信息都应该是自然、整合的。"""

        return prompt

    async def process_message(
        self, message: str, history: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        处理用户消息 - 支持多步骤信息聚合

        Args:
            message: 用户输入的消息
            history: 对话历史

        Returns:
            Dict: 包含响应内容和工具调用结果
        """
        if history is None:
            history = []

        # 构建消息列表
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *history,
            {"role": "user", "content": message},
        ]

        # 调用DeepSeek API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False,
                },
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API调用失败: {response.text}")

            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]

        # 解析并执行所有JSON指令（支持多个）
        tool_call_result = None
        final_response = ai_response

        # 查找所有JSON代码块
        json_blocks = re.findall(r"```json\n(.*?)\n```", ai_response, re.DOTALL)

        if json_blocks:
            # 执行所有指令
            execution_results = []
            for json_str in json_blocks:
                try:
                    cmd = json.loads(json_str)
                    action = cmd.get("action")

                    if action == "call_tool":
                        tool_name = cmd.get("tool")
                        arguments = cmd.get("arguments", {})
                        result = await self.mcp_client.call_tool(tool_name, arguments)
                        execution_results.append(
                            {
                                "type": "tool_call",
                                "tool": tool_name,
                                "arguments": arguments,
                                "result": result,
                            }
                        )

                    elif action == "read_resource":
                        uri = cmd.get("uri")
                        result = await self.mcp_client.read_resource(uri)
                        execution_results.append(
                            {"type": "read_resource", "uri": uri, "result": result}
                        )

                    elif action == "use_prompt":
                        prompt_name = cmd.get("prompt")
                        arguments = cmd.get("arguments", {})
                        result = await self.mcp_client.get_prompt(
                            prompt_name, arguments
                        )
                        execution_results.append(
                            {
                                "type": "use_prompt",
                                "prompt": prompt_name,
                                "arguments": arguments,
                                "result": result,
                            }
                        )

                except Exception as e:
                    logger.error(f"执行指令失败: {e}")
                    execution_results.append(
                        {"type": "error", "command": json_str, "error": str(e)}
                    )

            # 如果有多个执行结果，将它们汇总
            if execution_results:
                tool_call_result = (
                    execution_results
                    if len(execution_results) > 1
                    else execution_results[0]
                )

                # 将执行结果发给AI，生成最终回答
                summary = "\n".join(
                    [
                        f"{r.get('type', 'unknown')}: {r.get('result', str(r))[:200]}"
                        for r in execution_results
                    ]
                )

                messages.append({"role": "assistant", "content": ai_response})
                messages.append(
                    {
                        "role": "user",
                        "content": f"所有指令执行结果汇总：\n{summary}\n请基于这些结果给用户一个整合后的友好回答。",
                    }
                )

                final_response = await self._get_final_answer(messages)

        return {
            "response": final_response,
            "tool_call": tool_call_result,
            "raw_ai_response": ai_response,
        }

    async def _get_final_answer(self, messages: List[Dict]) -> str:
        """获取最终的AI回答"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False,
                },
            )
            result = response.json()
            return result["choices"][0]["message"]["content"]
