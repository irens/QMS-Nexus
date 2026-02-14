"""
LLM Mock 配置模块
提供确定性的LLM响应用于集成测试
"""
from typing import Any, Dict, Optional
from unittest.mock import Mock


class LLMResponseMock:
    """LLM响应Mock类"""
    
    def __init__(self):
        self.call_count = 0
        self.responses = {
            "default": {
                "choices": [{
                    "message": {
                        "content": "根据文档内容，这是一个关于质量管理体系的测试文档。主要内容包括质量方针、目标和管理职责。",
                        "role": "assistant"
                    }
                }],
                "usage": {
                    "total_tokens": 150,
                    "prompt_tokens": 50,
                    "completion_tokens": 100
                }
            },
            "quality_management": {
                "choices": [{
                    "message": {
                        "content": "该文档主要描述了质量管理体系的要求，包括质量方针、质量目标、管理职责、资源管理、产品实现以及测量、分析和改进等方面。",
                        "role": "assistant"
                    }
                }],
                "usage": {
                    "total_tokens": 200,
                    "prompt_tokens": 80,
                    "completion_tokens": 120
                }
            },
            "test_feedback": {
                "choices": [{
                    "message": {
                        "content": "这是一个测试回答，用于验证反馈功能是否正常工作。",
                        "role": "assistant"
                    }
                }],
                "usage": {
                    "total_tokens": 50,
                    "prompt_tokens": 20,
                    "completion_tokens": 30
                }
            }
        }
    
    def get_response(self, prompt: str = "", response_type: str = "default") -> Dict[str, Any]:
        """获取Mock响应"""
        self.call_count += 1
        
        # 根据prompt内容选择响应类型
        if "质量" in prompt or "管理" in prompt:
            response_type = "quality_management"
        elif "测试" in prompt or "反馈" in prompt:
            response_type = "test_feedback"
        
        return self.responses.get(response_type, self.responses["default"])
    
    def reset(self):
        """重置调用计数"""
        self.call_count = 0


def create_llm_mock() -> Mock:
    """创建LLM Mock对象"""
    llm_mock = LLMResponseMock()
    
    mock_obj = Mock()
    mock_obj.create = Mock(side_effect=lambda **kwargs: llm_mock.get_response(
        kwargs.get("messages", [{}])[0].get("content", "")
    ))
    
    return mock_obj


def create_embeddings_mock() -> Mock:
    """创建向量嵌入Mock对象"""
    mock_obj = Mock()
    
    # 返回768维的测试向量
    def mock_embeddings(texts, **kwargs):
        return [[0.1] * 768 for _ in texts]
    
    mock_obj.create = Mock(side_effect=mock_embeddings)
    return mock_obj


# 全局Mock实例
llm_response_mock = LLMResponseMock()


def mock_llm_response(prompt: str = "") -> Dict[str, Any]:
    """全局Mock响应函数"""
    return llm_response_mock.get_response(prompt)