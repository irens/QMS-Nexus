1. 架构守则（Architecture & Structure）
防止 AI 把代码写成一团乱麻。
指令示例：
“始终遵循模块化设计。核心逻辑放在 /core，解析逻辑放在 /parsers，数据库操作放在 /database，接口放在 /api。严禁在 UI 代码（Streamlit）中直接编写数据库查询或复杂的 RAG 逻辑，必须通过 Service 层调用。”
2. 技术栈偏好（Tech Stack & Standards）
明确工具链，防止 AI 随意引入不兼容的库。
指令示例：
“1. 优先使用 Python 3.10+ 的类型提示（Type Hints）。
2. 文档解析必须集成 MinerU 或 Unstructured，Excel 处理必须先转为 Markdown。
3. 向量数据库固定使用 ChromaDB。
4. 所有的 API 必须使用 FastAPI 并遵循异步（async/await）规范。
5. 大模型调用需兼容 OpenAI 协议，支持通过环境变量切换 Base_URL 和 API_Key。”
3. RAG 业务逻辑规范（Domain Specific Logic）
这是 QMS 系统的核心，必须让 AI 记住。
指令示例：
“1. 在处理 QMS 文档时，必须保留元数据（文件名、页码、层级）。
2. 检索结果必须包含来源标注，格式统一为：[来源：文件名, 第X页/表名]。
3. 所有的回答必须基于检索到的 Context，如果 Context 中没有相关信息，必须回答‘知识库中暂无相关记录’，严禁幻觉。”
4. 性能与防御性编程（Performance & Safety）
针对你提到的并发和稳定性需求。
指令示例：
“1. 所有的文件上传和解析必须设计为异步任务，并提供状态回调（Pending, Processing, Completed）。
2. 必须包含完善的错误处理机制，捕获解析失败、向量库连接超时等异常，并返回友好的错误提示。
3. 关键操作必须记录日志，日志格式包含：时间戳、用户标识、操作类型、耗时。”