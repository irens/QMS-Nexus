# QMS-Nexus API 文档

## 在线文档
启动后访问：http://localhost:8000/docs

## 接口清单

### 1. 健康检查
```http
GET /health
```
响应：
```json
{"status": "ok"}
```

### 2. 文件上传
```http
POST /upload
Content-Type: multipart/form-data
```
参数：
- file：≤50 MB，支持 PDF/Word/Excel/PPT

响应：
```json
{
  "task_id": "uuid",
  "status": "Pending"
}
```
错误码：
- 400：不支持的文件类型
- 413：文件过大

### 3. 任务状态
```http
GET /upload/status/{task_id}
```
响应：
```json
{
  "task_id": "uuid",
  "status": "Completed"
}
```

### 4. 语义检索
```http
GET /search?q=关键词&filter_tags=标签1,标签2&top_k=5
```
响应：
```json
[
  {
    "text": "...",
    "source": "文件名, 第1页",
    "tags": [],
    "score": 0.87
  }
]
```

### 5. RAG 问答
```http
POST /ask
Content-Type: application/json

{
  "question": "客户投诉如何处理？"
}
```
响应：
```json
{
  "answer": "根据知识库...",
  "sources": ["文件名, 第1页"]
}
```

### 6. 动态标签 CRUD
```http
GET    /tags
POST   /tags
PUT    /tags/{name}
DELETE /tags/{name}
```

### 7. 系统指标
```http
GET /metrics
```
Prometheus 格式，含上传/检索 QPS、延迟

## 调用示例

curl 上传：
```bash
curl -F "file=@sample.pdf" http://localhost:8000/upload
```

Python 检索：
```python
import requests
r = requests.get("http://localhost:8000/search", params={"q": "质量风险"})
print(r.json())
```