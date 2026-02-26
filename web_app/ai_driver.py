"""
AI驱动模块
功能：连接DeepSeek API，处理用户输入，决策是否调用MCP工具
"""

import json
import re
import asyncio
from typing import List, Dict, Any
from datetime import datetime

import httpx
from modules.YA_Secrets.secrets_parser import get_secret
from modules.YA_Common.utils.logger import get_logger
from modules.YA_Common.utils.config import get_config

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
        self.api_url = get_config(
            "deepseek.api_url", "https://api.deepseek.com/chat/completions"
        )
        self.model = get_config("deepseek.model", "deepseek-chat")
        self.temperature = get_config("deepseek.temperature", 0.7)
        self.timeout = get_config("deepseek.timeout", 60)

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

        prompt = f"""你是一个智能信息聚合助手，可以通过MCP协议调用多个API和读取资源，为用户提供一站式的信息服务。

当前时间：{current_time}

## 📋 可用能力

### ⚠️ 重要区分
- **工具 (Tools)**：执行操作、调用API、修改数据 → 用 `call_tool`
- **资源 (Resources)**：读取静态数据、配置文件、本地文件 → 用 `read_resource`
- **提示词 (Prompts)**：格式化输出、生成模板 → 用 `use_prompt`

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

## 🎯 核心调用规则（必须严格遵守）

### 1. 工具调用（用于操作）
```json
{"action": "call_tool", "tool": "工具名", "arguments": {"参数": "值"}}
```

### 2. 资源读取（用于数据）
```json
{"action": "read_resource", "uri": "资源URI"}
```

### 3. 提示词调用（⚠️ 特别注意参数）
```json
{"action": "use_prompt", "prompt": "模板名", "arguments": {"参数1": "值1", "参数2": "值2"}}
```

**⚠️ 提示词调用的重要规则：**
- **必须传入所有必需的参数**，不能省略
- 参数名必须与函数参数名完全一致
- 例如 `city_comparison` 需要 `cities` 参数，格式为 `["北京", "上海"]`
- 参数值应该是字符串或列表，不要传空对象

## ❗️ 常见错误及纠正

### 错误示例（不要这样做）
```json
{"action": "call_tool", "tool": "search_stations", "arguments": {"keyword": "武汉", "by": "city"}}
```
❌ 错误原因：`search_stations` 是**资源**不是工具，应该用 `read_resource`

```json
{"action": "use_prompt", "prompt": "city_comparison", "arguments": {}}
```
❌ 错误：缺少必需的 `cities` 参数

```json
{"action": "use_prompt", "prompt": "city_comparison", "arguments": {"cities": "武汉"}}
```
❌ 错误：`cities` 应该是列表，不是字符串

### 正确示例
```json
{"action": "read_resource", "uri": "text://stations/search/武汉/city"}
```
✅ 正确：用 `read_resource` 读取文本格式的车站资源

```json
{"action": "read_resource", "uri": "data://stations/city/武汉"}
```
✅ 正确：用 `read_resource` 读取JSON格式的城市车站资源

## 🔄 重要：多步骤调用规则

**当需要生成创意内容时，必须分两步执行：**

### 第一步：调用工具获取数据
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "武汉"}}
```

### 第二步：调用提示词生成创意内容
```json
{"action": "use_prompt", "prompt": "generate_weather_report", "arguments": {
    "city": "武汉",
    "weather_data": "【上一步获取的完整天气数据】"
}}
```

## 📝 具体场景示例

### 场景1：写一首关于城市的诗（两步必须都做）
用户："结合天气，写一首关于武汉的诗"

**你的正确响应（两个JSON块，一个都不能少）：**

```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "武汉", "format": "simple"}}
```

```json
{"action": "use_prompt", "prompt": "write_travel_poem", "arguments": {
    "city": "武汉",
    "weather_info": "【上一步获取的天气数据】"
}}
```

### 场景2：生成天气报告（两步必须都做）
用户："生成详细的，武汉今日天气报告"

**你的正确响应：**

```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "武汉", "format": "detailed"}}
```

```json
{"action": "use_prompt", "prompt": "generate_weather_report", "arguments": {
    "city": "武汉",
    "weather_data": "【上一步获取的天气数据】"
}}
```

### 场景3：只查天气（一步就够了）
用户："北京天气怎么样？"

**你的正确响应（一步就够了）：**

```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "北京"}}
```

## ❌ 常见错误

### 错误示例1：只调用工具，不调用提示词
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "武汉"}}
```
❌ 用户想要的是"诗"，不是天气数据！必须两步都做。

### 错误示例2：直接调用提示词，不先获取数据
```json
{"action": "use_prompt", "prompt": "write_travel_poem", "arguments": {
    "city": "秦皇岛",
    "weather_info": "自己编的天气"
}}
```
❌ 天气信息应该是真实的，不能编造！

## ✅ 正确的做法总结

| 用户需求 | 需要的步骤 | 理由 |
|---------|-----------|------|
| 查天气 | 1步：调用 `get_weather` | 用户要的是数据 |
| 写诗 | **2步**：先 `get_weather` 再 `write_travel_poem` | 诗需要真实天气素材 |
| 天气报告 | **2步**：先 `get_weather` 再 `generate_weather_report` | 报告需要真实数据 |

## ⚠️ 重要提醒

- **当用户要求创作类内容（诗、故事、建议）时，必须两步都做**
- **第一步获取真实数据，第二步基于数据创作**
- **两个JSON块要连续输出，中间不要有文字间隔，系统会依次执行**
- **绝对不要编造数据**

## 📝 其它场景示例

### 场景1：查询车站
用户："北京有哪些火车站？"
你：
```json
{"action": "read_resource", "uri": "text://stations/search/北京/city"}
```

### 场景2：查询天气（需要调用API）
用户："北京天气怎么样？"
你：
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "北京"}}
```

### 场景3：查询车票（需要调用API）
用户："北京到上海的高铁"
你：
```json
{"action": "call_tool", "tool": "query_train_schedule", "arguments": {
    "departure": "北京",
    "arrival": "上海",
    "date": "2025-02-26",
    "filter": "G"
}}

## 🔄 聚合信息工作流程

当用户需要综合多个信息源时，请按以下步骤执行：

1. **识别需求**：分析用户需要哪些方面的信息
2. **调用工具/资源**：依次获取所需数据
3. **组合信息**：将多个来源的信息整合
4. **格式化输出**：使用提示词模板或自然语言呈现

需要调用多个API时，请按以下格式**分多个JSON块输出**：

### 模板：生成武汉的详细天气报告
用户："生成详细的，武汉今日天气报告"

**正确步骤：**
1. 先获取详细的天气数据
```json
{"action": "call_tool", "tool": "get_weather", "arguments": {"city": "武汉", "format": "detailed"}}
```

2. 再用提示词生成报告
```json
{"action": "use_prompt", "prompt": "generate_weather_report", "arguments": {
    "city": "武汉",
    "weather_data": "【上一步获取的天气数据】"
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

### ⚠️ 重要提醒

✅ **工具用 `call_tool`**：查询天气、查询车票、执行操作
✅ **资源用 `read_resource`**：查询车站列表、读取配置文件、获取静态数据
❌ **绝对不要混淆**：资源不是工具，不能用 `call_tool` 调用

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
        """

        if history is None:
            history = []

        # 构建消息列表
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            *history,
            {"role": "user", "content": message},
        ]

        # 调用DeepSeek API - 添加取消保护
        try:
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
                # 如果要在控制台看到带颜色的输出，可以这样：
                print("\n" + "\033[92m" + "=" * 60)
                print("🤖 AI原始响应:")
                print("=" * 60)
                print(ai_response)
                print("=" * 60 + "\033[0m" + "\n")

        except asyncio.CancelledError:
            logger.warning("DeepSeek API请求被取消")
            return {
                "response": "请求被取消，请稍后重试",
                "tool_call": None,
                "raw_ai_response": "",
            }
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return {
                "response": f"AI服务暂时不可用: {str(e)}",
                "tool_call": None,
                "raw_ai_response": "",
            }

        # 改进JSON提取逻辑
        tool_call_result = None
        final_response = ai_response

        # 方法1：尝试匹配完整的JSON对象（从第一个{到最后一个}）
        def extract_json(text: str) -> List[str]:
            """智能提取文本中的所有JSON对象"""
            json_objects = []
            stack = []
            start = -1

            for i, char in enumerate(text):
                if char == "{":
                    if not stack:  # 新的JSON对象开始
                        start = i
                    stack.append(char)
                elif char == "}":
                    if stack:
                        stack.pop()
                        if not stack and start != -1:  # JSON对象结束
                            json_str = text[start : i + 1]
                            json_objects.append(json_str)
                            start = -1
            return json_objects

        # 方法2：先用正则匹配代码块，再用方法1提取完整JSON
        json_blocks = []

        # 先找```json代码块
        code_block_pattern = r"```(?:json)?\s*(.*?)\s*```"
        code_blocks = re.findall(
            code_block_pattern, ai_response, re.DOTALL | re.IGNORECASE
        )

        for block in code_blocks:
            # 从代码块中提取完整JSON
            json_blocks.extend(extract_json(block))

        # 如果没有代码块，直接从整个响应中提取
        if not json_blocks:
            json_blocks = extract_json(ai_response)

        # ✅ 修复：确保所有JSON指令都被执行
        execution_results = []

        if json_blocks:
            logger.info(f"发现 {len(json_blocks)} 个JSON指令")
            logger.info(f"JSON指令: {json_blocks}")

            # 执行所有指令
            for json_str in json_blocks:
                try:
                    # 尝试解析
                    cmd = json.loads(json_str)
                    action = cmd.get("action")

                    if action == "call_tool":
                        tool_name = cmd.get("tool")
                        arguments = cmd.get("arguments", {})
                        logger.info(f"执行工具: {tool_name}, 参数: {arguments}")

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
                        logger.info(f"读取资源: {uri}")

                        result = await self.mcp_client.read_resource(uri)
                        execution_results.append(
                            {"type": "read_resource", "uri": uri, "result": result}
                        )

                    elif action == "use_prompt":
                        prompt_name = cmd.get("prompt")
                        arguments = cmd.get("arguments", {})
                        logger.info(f"使用提示词: {prompt_name}, 参数: {arguments}")

                        try:
                            # 使用 asyncio.wait_for 添加超时，防止无限等待
                            result = await asyncio.wait_for(
                                self.mcp_client.get_prompt(prompt_name, arguments),
                                timeout=10.0,  # 10秒超时
                            )

                            execution_results.append(
                                {
                                    "type": "use_prompt",
                                    "prompt": prompt_name,
                                    "arguments": arguments,
                                    "result": result,
                                }
                            )

                        except asyncio.TimeoutError:
                            logger.error(f"提示词 {prompt_name} 调用超时")
                            execution_results.append(
                                {
                                    "type": "error",
                                    "prompt": prompt_name,
                                    "error": "提示词调用超时",
                                }
                            )

                        except asyncio.CancelledError:
                            logger.warning(f"提示词 {prompt_name} 调用被取消")
                            execution_results.append(
                                {
                                    "type": "error",
                                    "prompt": prompt_name,
                                    "error": "提示词调用被取消",
                                }
                            )

                        except Exception as e:
                            logger.error(f"执行提示词失败: {e}")
                            execution_results.append(
                                {
                                    "type": "error",
                                    "prompt": prompt_name,
                                    "arguments": arguments,
                                    "error": str(e),
                                }
                            )
                    else:
                        logger.warning(f"未知action类型: {action}")

                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    logger.error(f"问题JSON: {json_str}")

                    execution_results.append(
                        {
                            "type": "error",
                            "command": json_str,
                            "error": f"JSON解析错误: {str(e)}",
                        }
                    )
                except Exception as e:
                    logger.error(f"执行指令失败: {e}")
                    execution_results.append(
                        {"type": "error", "command": json_str, "error": str(e)}
                    )

        # 如果有执行结果，生成最终回答
        if execution_results:
            # 如果有多个结果，tool_call 是列表；如果只有一个，是字典
            if len(execution_results) == 1:
                tool_call_result = execution_results[0]
            else:
                tool_call_result = execution_results  # 列表

            # 构建执行结果摘要
            summary_lines = []
            for r in execution_results:
                if r["type"] == "tool_call":
                    summary_lines.append(
                        f"工具 [{r['tool']}] 返回: {r['result'][:200]}"
                    )
                elif r["type"] == "read_resource":
                    summary_lines.append(f"资源 [{r['uri']}] 内容: {r['result'][:200]}")
                elif r["type"] == "use_prompt":
                    summary_lines.append(
                        f"提示词 [{r['prompt']}] 生成: {r['result'][:200]}"
                    )
                else:
                    summary_lines.append(f"错误: {r.get('error', '未知错误')}")

            summary = "\n".join(summary_lines)

            # 将执行结果发给AI，生成最终回答
            messages.append({"role": "assistant", "content": ai_response})
            messages.append(
                {
                    "role": "user",
                    "content": f"我已经执行了你的指令，以下是执行结果：\n\n{summary}\n\n请基于这些结果给用户一个自然、友好的回答。不要提及你调用了什么工具，直接告诉用户他们想知道的信息。",
                }
            )

            final_response = await self._get_final_answer(messages)

            logger.info(f"生成最终回答成功")
        else:
            logger.info("没有发现JSON指令，直接使用AI原始响应")

        return {
            "response": final_response,
            "tool_call": tool_call_result,  # 可以是字典或列表
            "raw_ai_response": ai_response,
        }

    async def _get_final_answer(self, messages: List[Dict]) -> str:
        """获取最终的AI回答 - 增强版"""
        max_retries = 2
        retry_delay = 1

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"正在生成最终回答 (尝试 {attempt + 1}/{max_retries + 1})")

                # 使用更短的超时
                timeout = httpx.Timeout(30.0, connect=5.0, read=20.0)

                async with httpx.AsyncClient(timeout=timeout) as client:
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

                    if response.status_code == 200:
                        result = response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.aread()
                        logger.error(
                            f"API返回错误 (尝试 {attempt + 1}): {response.status_code}"
                        )

                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay * (attempt + 1))
                            continue
                        else:
                            return f"AI服务暂时不可用 (HTTP {response.status_code})"

            except asyncio.CancelledError:
                logger.warning("请求被取消")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return "请求被取消，请稍后重试"

            except httpx.TimeoutException:
                logger.warning(f"请求超时 (尝试 {attempt + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return "请求超时，请稍后重试"

            except httpx.NetworkError as e:
                logger.warning(f"网络错误 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return "网络连接失败，请检查网络"

            except Exception as e:
                logger.error(f"未知错误: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    continue
                return f"处理失败: {str(e)}"

        return "无法生成回答，请稍后重试"
