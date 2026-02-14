"""
单元测试：Task 2.6 提示词模板渲染
"""
from services.prompt_service import PromptService


def test_default_template():
    """默认模板渲染。"""
    svc = PromptService()
    prompt = svc.render({"context": "ISO13485 内容", "question": "核心？"})
    assert "ISO13485 内容" in prompt
    assert "核心？" in prompt
    assert "医疗器械质量管理体系" in prompt


def test_custom_template():
    """自定义模板。"""
    tpl = "用户：{{ user }}\n问题：{{ question }}"
    svc = PromptService(template_str=tpl)
    prompt = svc.render({"user": "张三", "question": "如何上传？"})
    assert "用户：张三" in prompt
    assert "问题：如何上传？" in prompt