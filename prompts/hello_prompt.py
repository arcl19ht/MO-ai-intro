from typing import Any

from prompts import YA_MCPServer_Prompt

@YA_MCPServer_Prompt(
    name="greet_user",
    title="Greeting Prompt",
    description="生成一个问候消息",
)
async def hello_prompt(name: str) -> Any:  
    
    yield f"你好，{name}！欢迎使用 YA MCP Server。"