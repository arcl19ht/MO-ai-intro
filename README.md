## Z_MCPServer

基于 MCP 协议的全栈智能旅游助手，集成实时天气、景点酒店查询及智能行程规划功能。

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :------: | :------: | :--: | :--: | 
| 周子闰 | U202414650 | 旅游助手板块框架工具层和核心层板块，组织团队分工开发|  |
| 徐可 | U202414156 | Web应用和MCP客户端、AI驱动框架，天气和火车助手框架工具编写 |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| get_weather | 根据城市名称查询实时天气和未来天气预报 | city: 城市名称(必填), format: 返回格式(simple/detailed, 默认simple) | simple格式返回友好文本（含实时天气、温度、湿度、风向风力、空气质量及未来3天预报）；detailed格式返回完整JSON数据 | 数据源为聚合数据API，支持全国主要城市。simple格式适合直接展示，detailed格式适合二次处理 |
| get_weather_comparison | 对比多个城市的天气情况 | cities: 城市名称列表(必填)，如['北京','上海','广州']，最多支持5个城市 | 文本格式的多城市天气对比报告，包含各城市实时天气、温度、湿度、风力等信息 | 自动并行查询多个城市，单个城市失败不影响其他城市结果展示 |
|    search_attractions |  搜索指定城市的真实旅游景点信息 |   keyword: 景点关键词,city: 城市名   | JSON 列表：包含景点名称、地址、类型、评分、价格、电话等。     |      |
| search_hotels   |   搜索指定城市的酒店、宾馆、民宿等住宿信息。       | keyword: 必须包含地点和类型（如“西湖住宿”）,city: 城市名     |  JSON 列表：包含酒店名称、地址、评分、价格、电话、设施等。    |  智能修正：若 keyword 不含“酒店/住宿”等词，自动追加后缀。严格展示：强制列出所有结果，缺失字段显示“暂无”，严禁省略。    |
| get_travel_weather | 查询旅游目的地的实时天气状况。|city: 城市名| SON 对象：包含城市、实时天气、温度、湿度、风力、空气质量等。| 专用于旅游场景的天气查询，数据源为聚合数据 API。|
| plan_trip| 智能旅游规划助手：一键生成目的地综合简报。| destination: 目的地城市| 文本报告：整合了当地天气、3 个推荐景点、2 个推荐住宿及出行建议。| 组合工具：内部串行调用天气、景点、酒店三个 API。高容错：单个子任务失败不影响整体报告生成（显示“暂缺”）。|
| query_train_schedule | 查询两个车站之间的列车时刻表 | departure: 出发站, arrival: 到达站, date: 日期(YYYY-MM-DD), filter: 车次筛选(可选), format: 返回格式(可选) | simple格式返回友好文本，detailed格式返回详细JSON数据 | 支持车次筛选(G/D/Z/T/K等)，仅可查询未来15天内车次 |
| compare_train_routes | 对比多个火车路线的车次情况 | routes: 路线列表, date: 日期, filter: 车次筛选(可选) | 文本格式的多路线对比结果 | 最多支持同时对比5个路线，包含车次数量、最早最晚出发时间、最低票价等信息 |
| get_train_filters | 获取车次筛选条件的说明 | 无 | 车次类型和出发时间段的说明文本 | 包含车次代码(G/D/Z/T/K等)含义及时间段划分说明 |

### Resource 列表

| 资源名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| all_stations | 获取所有火车站的完整数据 | 无 | JSON格式的所有车站数据 | URI: `data://stations/all` |
| station_by_name | 根据车站名称查询详细信息 | station_name: 车站名称 | JSON格式的车站信息 | URI: `data://stations/name/{station_name}`，支持URL编码 |
| stations_by_city | 获取指定城市的所有车站 | city_name: 城市名称 | JSON格式的城市车站列表 | URI: `data://stations/city/{city_name}`，快捷方式 |
| search_stations | 搜索车站并返回JSON格式结果 | keyword: 搜索关键词, by: 搜索方式(name/code/pinyin/city) | JSON格式的搜索结果列表 | URI: `data://stations/search/{keyword}/{by}` |
| search_stations_text | 搜索车站并返回易读的文本格式 | keyword: 搜索关键词, by: 搜索方式(name/code/pinyin/city) | 格式化的文本结果 | URI: `text://stations/search/{keyword}/{by}` |

### Prompts 列表

| 指令名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| greet_user | 生成个性化的欢迎问候消息，用于会话初始化或用户互动。 | name (str): 用户的名字或称呼。 | 字符串：包含用户名字的欢迎语（例如：“你好，张三！欢迎使用 YA MCP Server。”）|  最简单的 Prompt 示例，演示了 MCP Prompt 的基本结构和 yield 返回机制。 |
| smart_travel_plan| 智能全案旅行规划师：一键生成包含【车次查询】、【天气预警】、【景点推荐】、【住宿建议】的完整旅行攻略。| destination (str): 目的地城市（必填）。origin (str): 出发地城市（可选，默认“本地”）。(兼容参数：arrival, departure)|  结构化 Markdown 报告，包含：天气与穿衣指南，大交通车次与车站提醒，必玩景点清单，住宿建议，综合温馨提示| 组合型 Prompt：内部定义了严格的工作流（Workflow），强制 AI 串行调用 4 个工具。|
|          |          |      |      |      |

### 项目结构

- `core`: 
  - `weather_api.py`: 获取天气API相关处理，包含实时天气查询和未来预报解析
  - `travel_api.py`: 封装高德地图 POI 搜索 API，有一定智能关键词修正与容错机制
  - `train_api.py`: 封装聚合数据火车票查询 API，提供列车时刻表查询功能
  - `train_stations.py`: 火车站数据处理核心模块，加载和查询车站信息
- `tools`: 
  - `weather_tool.py`: 定义天气查询工具接口，包含单城市查询和多城市对比功能
  - `travel_tool.py`: 定义景点、酒店查询工具接口，包含旅游规划功能
  - `train_tool.py`: 定义列车时刻表查询、路线对比等工具接口
- `resources`:
  - `train_stations.py`: 定义车站数据资源接口，提供多种查询方式
- `data`:
  - `train_stations.json`: 火车站静态数据文件，包含站名、编码、拼音、城市等信息
- `config.yaml`: 
  - `deepseek`: Deepseek模型相关配置
  - `weather`: 获取天气API相关配置
  - `train`: 获取火车API相关配置
  - `amap`: 获取高德地图API相关配置
- `web_app`: 基于FastAPI的web应用核心代码
  - `ai_driver.py`: AI驱动模块
  - `main.py`: FastAPI Web应用主模块
  - `mcp_client.py`: MCP客户端模块
- `start.py`: 启动MCP服务器和Web应用

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
secrets:
    deepseek_api_key: 您的api
    juhe_weather_api_key: 聚合天气api
    juhe_train_api_key: 聚合火车查询api
    amap_key: 高德地图web端服务api
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
- `juhe_weather_api_key`: 用于调用聚合数据天气预报 API，提供实时天气 (get_weather) 信息。
- `juhe_train_api_key`: 用于调用聚合数据火车订票查询 API，提供实时列车 (query_train_schedule) 信息。
- `amap_key`: 用于调用高德地图 Web 服务 API，提供景点 (search_attractions) 和酒店 (search_hotels) 数据。

 
#### 技术栈说明

本项目基于 LLM (Large Language Model) 应用能力开发，核心逻辑为 Rule-based (基于规则) 的 API 编排与 Prompt Engineering (提示词工程)，通过异步 IO (asyncio, httpx) 实现高并发工具调用。未使用 PyTorch、Tensorflow 等深度学习框架和自训练的机器学习或深度学习模型。

#### 架构亮点
- **分层架构**：严格区分 core (业务逻辑) 与 tools (接口定义)，便于维护与测试。
- **异步非阻塞**：全链路采用 async/await，确保多工具并发调用时不阻塞主线程。
- **健壮性设计**：核心工具内置智能关键词修正、局部故障熔断及兜底数据机制。