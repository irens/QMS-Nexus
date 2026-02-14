"""
基础数据模型，全局无业务硬编码。
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# -----------------------
# 配置模型
# -----------------------
class CompanyConfig(BaseModel):
    name: str = Field(..., description="公司名称")
    product: str = Field(..., description="产品名称")
    industry: str = Field(..., description="行业领域")

class EmbeddingConfig(BaseModel):
    model: str = "BAAI/bge-small-zh-v1.5"
    dim: int = 512
    chunk_size: int = 800
    overlap: int = 100

class ParserRule(BaseModel):
    mime: str
    engine: str
    options: Optional[Dict[str, Any]] = None

class ParserConfig(BaseModel):
    rules: List[ParserRule]

class GlobalConfig(BaseModel):
    company: CompanyConfig
    tag_pool: List[str] = Field(default_factory=list)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    parser: ParserConfig

# -----------------------
# 文档模型
# -----------------------
class Chunk(BaseModel):
    id: Optional[str] = None
    text: str
    page: Optional[int] = None
    table: Optional[str] = None  # Markdown 表格
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Document(BaseModel):
    id: Optional[str] = None
    filename: str
    mime: str
    chunks: List[Chunk] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# -----------------------
# 检索模型
# -----------------------
class SearchResult(BaseModel):
    text: str
    score: float
    source: str  # [来源：文件名, 第X页]
    tags: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1)
    filter_tags: List[str] = Field(default_factory=list)
    top_k: int = Field(5, ge=1, le=100)

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int