"""
Prometheus 指标定义
"""
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 接口请求量
upload_counter = Counter("qms_upload_total", "文件上传次数", ["status"])
search_counter = Counter("qms_search_total", "语义检索次数", ["status"])

# 接口延迟
upload_duration = Histogram("qms_upload_duration_seconds", "上传接口耗时")
search_duration = Histogram("qms_search_duration_seconds", "检索接口耗时")