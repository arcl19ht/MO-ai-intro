## Z_MCPServer

[一句话功能简介]

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :--: | :--: | :--: | :--: |
|      |      |      |      |
|      |      |      |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
|          |          |      |      |      |
|          |          |      |      |      |
|          |          |      |      |      |

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

- `core`: [XXXX]
- `tools`: [XXXX]
- `config.yaml`: [XXXX(添加 XX 额外配置)]
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
按文档中`sops.mdx`中的指导生成公钥和私钥，添加`sops`配置文件。接着**在根目录**运行管理密钥文件的脚本，在打开的文本编辑器中输入：
```yaml
# 替换原先的默认内容
secrets:
    deepseek_api_key: # 此处填入API key
```
关闭编辑器后，会在根目录下生成新的`env.yaml`文件，API key设置完成。

#### 启动MCP服务器和web应用

```bash
# start.py同时启动MCP服务器和Web应用
uv run start.py
```
启动成功后，打开浏览器，访问 http://localhost:8000/

### 其他需要说明的情况

- `sops` 模块中`deepseek_api_key`变量为deepseek模型的API key
- 在 `sops` 模块中添加的密钥变量分别用于什么功能
- 是否使用了 PyTorch、Tensorflow 等深度学习框架
- 是否使用了机器学习、深度学习模型
