## Z_MCPServer

基于 MCP 协议的全栈智能旅游助手，集成实时天气、景点酒店查询及智能行程规划功能。

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :------: | :------: | :--: | :--: | 
| 周子闰 | U202414650 | 旅游助手板块框架工具层和核心层板块，组织团队分工开发|  |
|      |      |      |      |
|      |      |      |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|weather_tool|获取一个地点的天气|地点名称，返回格式|返回对应格式、地点的天气信息||
|    search_attractions |  搜索指定城市的真实旅游景点信息 |   keyword: 景点关键词,city: 城市名   | JSON 列表：包含景点名称、地址、类型、评分、价格、电话等。     |      |
| search_hotels   |   搜索指定城市的酒店、宾馆、民宿等住宿信息。       | keyword: 必须包含地点和类型（如“西湖住宿”）,city: 城市名     |  JSON 列表：包含酒店名称、地址、评分、价格、电话、设施等。    |  智能修正：若 keyword 不含“酒店/住宿”等词，自动追加后缀。严格展示：强制列出所有结果，缺失字段显示“暂无”，严禁省略。    |
| get_travel_weather | 查询旅游目的地的实时天气状况。|city: 城市名| SON 对象：包含城市、实时天气、温度、湿度、风力、空气质量等。| 专用于旅游场景的天气查询，数据源为聚合数据 API。|
| plan_trip| 智能旅游规划助手：一键生成目的地综合简报。| destination: 目的地城市| 文本报告：整合了当地天气、3 个推荐景点、2 个推荐住宿及出行建议。| 组合工具：内部串行调用天气、景点、酒店三个 API。高容错：单个子任务失败不影响整体报告生成（显示“暂缺”）。|

### Resource 列表

| 资源名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

### Prompts 列表

| 指令名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

### 项目结构

- `core`: 
  - `weather_api.py`: 获取天气API相关处理
  - `travel_api.py`: 封装高德地图 POI 搜索 API，有一定智能关键词修正与容错机制
- `tools`: 
  - `weather_tool.py`: 定义天气查询工具接口
  - `travel_guide.py`: 定义景点、酒店搜索及智能规划工具接口
- `config.yaml`: 
  - `deepseek`: Deepseek模型相关配置
  - `weather`: 获取天气API相关配置
- `web_app`: 基于Fast API的web应用核心代码
  - `ai_driver.py`: AI驱动模块
  - `main.py`: FastAPI Web应用主模块
  - `mcp_client.py`: MCP客户端模块
- `start.py`: 启动MCP服务器和Web应用
- [XXXX(其他新添加的文件与目录介绍)]

### 如何使用

#### 更新依赖
clone仓库后，更新新增依赖：
```bash
# 更新 pyproject.toml 中的依赖
uv sync
```
#### 用sops读取API key
按文档中`sops.mdx`中的指导生成公钥和私钥，添加`sops`配置文件`.sops.yaml`。接着**在根目录**运行管理密钥文件的脚本（可复制到根目录下运行），在打开的文本编辑器中输入：
```yaml
# 替换原先的默认内容
secrets:
    deepseek_api_key: # 此处填入API key
    # 其它API key……
```
关闭编辑器后，会在根目录下生成新的`env.yaml`文件，API key设置完成。

#### 启动MCP服务器和web应用

```bash
# start.py同时启动MCP服务器和Web应用
uv run start.py
```
启动成功后，打开浏览器，访问 http://localhost:8000/

### 其他需要说明的情况
#### 密钥管理
所有密钥均通过 sops 加密存储于 env.yaml。
- `deepseek_api_key`: 用于调用 DeepSeek 大语言模型，驱动 AI 对话与工具调度。
- `amap_key`: 用于调用高德地图 Web 服务 API，提供景点 (search_attractions) 和酒店 (search_hotels) 数据。
- `juhe_weather_api_key`: 用于调用聚合数据 API，提供实时天气 (get_travel_weather) 信息。
#### 技术栈说明

本项目基于 LLM (Large Language Model) 应用能力开发，核心逻辑为 Rule-based (基于规则) 的 API 编排与 Prompt Engineering (提示词工程)，通过异步 IO (asyncio, httpx) 实现高并发工具调用。未使用 PyTorch、Tensorflow 等深度学习框架和自训练的机器学习或深度学习模型。

#### 架构亮点
- **分层架构**：严格区分 core (业务逻辑) 与 tools (接口定义)，便于维护与测试。
- **异步非阻塞**：全链路采用 async/await，确保多工具并发调用时不阻塞主线程。
- **健壮性设计**：核心工具内置智能关键词修正、局部故障熔断及兜底数据机制。