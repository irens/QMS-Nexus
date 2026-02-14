"""
系统提示词模板渲染服务（Jinja2）
"""
from typing import Dict, Any
from jinja2 import Template, Environment, BaseLoader


class PromptService:
    """线程安全，支持自定义模板字符串或文件。"""

    def __init__(self, template_str: str = None):
        """
        template_str: 默认模板，若为空则使用内置默认。
        """
        if template_str is None:
            template_str = self.default_template()
        self.env = Environment(loader=BaseLoader())
        self.template = self.env.from_string(template_str)

    @staticmethod
    def default_template() -> str:
        """内置默认系统提示词模板。"""
        return """
你是医疗器械质量管理体系（QMS）专家，请根据以下上下文简要、准确地回答问题。
上下文：
{{ context }}

问题：{{ question }}
""".strip()

    def render(self, variables: Dict[str, Any]) -> str:
        """变量渲染，返回最终系统提示词。"""
        return self.template.render(**variables)