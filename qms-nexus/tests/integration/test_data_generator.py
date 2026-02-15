"""
QMS-Nexus 系统测试数据管理工具
用于生成、管理和清理测试数据
"""
import json
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import io


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self):
        self.test_data_dir = Path(__file__).parent / "data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # 医疗器械相关关键词库
        self.medical_keywords = [
            "ISO 13485", "医疗器械", "质量管理", "风险控制", "临床评价",
            "生物相容性", "灭菌验证", "包装验证", "标签要求", "使用说明",
            "不良事件", "召回管理", "CAPA", "SOP文件", "检验规范",
            "设备维护", "校准管理", "供应商管理", "文件控制", "培训记录"
        ]
        
        # 测试文档模板
        self.document_templates = {
            "quality_manual": {
                "title": "质量管理手册",
                "content": """
                本质量管理手册依据ISO 13485:2016标准制定，适用于医疗器械的设计、开发、生产和销售。
                
                1. 质量方针和目标
                2. 组织架构和职责
                3. 文件控制程序
                4. 记录控制程序
                5. 管理评审程序
                6. 内部审核程序
                7. 不合格品控制程序
                8. 纠正和预防措施程序
                """,
                "type": "pdf"
            },
            "sop_document": {
                "title": "标准操作程序",
                "content": """
                标准操作程序(SOP) - 医疗器械检验规范
                
                目的：建立医疗器械产品的检验标准和操作程序
                
                适用范围：适用于所有医疗器械产品的进货检验、过程检验和最终检验
                
                职责：
                - 质量部负责制定和更新检验规范
                - 检验员负责按规范执行检验
                - 质量经理负责审核和批准
                
                检验项目：
                1. 外观检验
                2. 尺寸检验  
                3. 功能检验
                4. 包装检验
                5. 标识检验
                """,
                "type": "docx"
            },
            "inspection_record": {
                "title": "检验记录表",
                "content": """
                医疗器械检验记录表
                
                产品名称：[产品名称]
                规格型号：[规格型号]
                批号：[批号]
                数量：[数量]
                
                检验项目及结果：
                1. 外观检验：□合格 □不合格
                2. 尺寸检验：□合格 □不合格
                3. 功能检验：□合格 □不合格
                4. 包装检验：□合格 □不合格
                5. 标识检验：□合格 □不合格
                
                检验结论：□合格 □不合格
                检验员：[签名]
                检验日期：[日期]
                """,
                "type": "xlsx"
            },
            "training_material": {
                "title": "员工培训材料",
                "content": """
                医疗器械法规培训
                
                培训目标：
                - 了解医疗器械法规要求
                - 掌握质量管理基本原则
                - 熟悉产品安全要求
                
                培训内容：
                1. 医疗器械监督管理条例
                2. ISO 13485质量管理体系
                3. 风险管理(ISO 14971)
                4. 临床评价要求
                5. 不良事件监测和报告
                
                考核要求：
                - 理论考试80分以上
                - 实际操作考核合格
                - 培训记录存档
                """,
                "type": "pptx"
            }
        }
    
    def generate_pdf_content(self, title: str, content: str) -> bytes:
        """生成PDF文件内容"""
        # 简化的PDF内容生成
        pdf_header = b"%PDF-1.4\n"
        pdf_content = f"""
        {title}
        
        {content}
        
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        关键词: {', '.join(random.sample(self.medical_keywords, 3))}
        """.encode('utf-8')
        
        return pdf_header + pdf_content * random.randint(50, 200)
    
    def generate_docx_content(self, title: str, content: str) -> bytes:
        """生成Word文档内容"""
        # 简化的DOCX内容生成
        docx_header = b"PK"  # DOCX文件头
        docx_content = f"""
        {title}
        
        {content}
        
        文档信息:
        - 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - 版本: 1.0
        - 状态: 正式版本
        
        审批记录:
        编制: [签名] 日期: [日期]
        审核: [签名] 日期: [日期]  
        批准: [签名] 日期: [日期]
        """.encode('utf-8')
        
        return docx_header + docx_content * random.randint(30, 100)
    
    def generate_xlsx_content(self, title: str, content: str) -> bytes:
        """生成Excel表格内容"""
        # 简化的XLSX内容生成
        xlsx_header = b"PK"  # XLSX文件头
        xlsx_content = f"""
        {title}
        
        {content}
        
        数据记录:
        序号|检验项目|标准要求|检验结果|结论
        1|外观|无明显缺陷|合格|通过
        2|尺寸|±0.5mm|合格|通过
        3|功能|正常工作|合格|通过
        4|包装|完好无损|合格|通过
        
        统计信息:
        总检验项: 4
        合格项: 4
        不合格项: 0
        合格率: 100%
        """.encode('utf-8')
        
        return xlsx_header + xlsx_content * random.randint(20, 80)
    
    def generate_pptx_content(self, title: str, content: str) -> bytes:
        """生成PPT演示文稿内容"""
        # 简化的PPTX内容生成
        pptx_header = b"PK"  # PPTX文件头
        pptx_content = f"""
        {title}
        
        {content}
        
        幻灯片1: 封面
        - 标题: {title}
        - 副标题: 医疗器械培训
        - 日期: {datetime.now().strftime('%Y-%m-%d')}
        
        幻灯片2: 目录
        - 培训目标
        - 培训内容
        - 考核要求
        
        幻灯片3: 培训目标
        - 了解法规要求
        - 掌握管理原则
        - 熟悉安全要求
        """.encode('utf-8')
        
        return pptx_header + pptx_content * random.randint(25, 90)
    
    def create_test_document(self, template_name: str, custom_content: str = None) -> Dict[str, Any]:
        """创建测试文档"""
        if template_name not in self.document_templates:
            raise ValueError(f"未知的模板: {template_name}")
        
        template = self.document_templates[template_name]
        title = template["title"]
        content = custom_content or template["content"]
        doc_type = template["type"]
        
        # 添加随机变化使内容更真实
        content += f"\n\n随机信息: {random.randint(1000, 9999)}"
        content += f"\n版本: V{random.randint(1, 5)}.{random.randint(0, 9)}"
        
        # 生成文件内容
        if doc_type == "pdf":
            file_content = self.generate_pdf_content(title, content)
            mime_type = "application/pdf"
            file_extension = "pdf"
        elif doc_type == "docx":
            file_content = self.generate_docx_content(title, content)
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_extension = "docx"
        elif doc_type == "xlsx":
            file_content = self.generate_xlsx_content(title, content)
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            file_extension = "xlsx"
        elif doc_type == "pptx":
            file_content = self.generate_pptx_content(title, content)
            mime_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            file_extension = "pptx"
        else:
            raise ValueError(f"不支持的文档类型: {doc_type}")
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title.replace(' ', '_')}_{timestamp}.{file_extension}"
        
        return {
            "filename": filename,
            "content": file_content,
            "mime_type": mime_type,
            "title": title,
            "type": doc_type,
            "size": len(file_content),
            "keywords": random.sample(self.medical_keywords, 3)
        }
    
    def create_test_batch(self, count: int = 10) -> List[Dict[str, Any]]:
        """创建一批测试文档"""
        documents = []
        templates = list(self.document_templates.keys())
        
        for i in range(count):
            template_name = random.choice(templates)
            doc = self.create_test_document(template_name)
            documents.append(doc)
        
        return documents
    
    def create_edge_case_files(self) -> Dict[str, bytes]:
        """创建边界条件测试文件"""
        edge_cases = {
            "empty_pdf": b"%PDF-1.4\n",  # 空PDF
            "small_pdf": b"%PDF-1.4\n" + b"small file test" * 10,  # 小文件
            "medium_pdf": b"%PDF-1.4\n" + b"medium file test content with medical device quality management info" * 500,  # 中等文件
            "large_pdf": b"%PDF-1.4\n" + b"large file test content contains ISO13485 medical device quality management system requirements" * 2000,  # 大文件
            "oversized_pdf": b"%PDF-1.4\n" + b"oversized file test" * 10000,  # 超大文件(约50MB+)
            "invalid_pdf": b"This is not a valid PDF file content",  # 无效PDF
            "corrupted_pdf": b"%PDF-1.4\n" + b"corrupted file" * 100 + b"\x00\xFF\x00\xFF",  # 损坏的PDF
            "txt_file": b"This is a text file that should not be allowed to upload",  # TXT文件
            "exe_file": b"MZ" + b"executable file simulation content" * 100,  # 模拟EXE文件
            "script_file": b"#!/bin/bash\necho 'malicious script'",  # 脚本文件
        }
        
        return edge_cases
    
    def save_test_files(self, documents: List[Dict[str, Any]], output_dir: Path = None) -> List[Path]:
        """保存测试文件到本地"""
        if output_dir is None:
            output_dir = self.test_data_dir
        
        output_dir.mkdir(exist_ok=True)
        saved_files = []
        
        for doc in documents:
            file_path = output_dir / doc["filename"]
            with open(file_path, "wb") as f:
                f.write(doc["content"])
            saved_files.append(file_path)
        
        return saved_files


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self):
        self.generator = TestDataGenerator()
        self.test_data_file = Path(__file__).parent / "system_test_data.json"
        
    def generate_and_save_test_data(self, count: int = 20):
        """生成并保存测试数据"""
        print(f"生成 {count} 个测试文档...")
        
        # 生成正常测试文档
        normal_docs = self.generator.create_test_batch(count)
        
        # 生成边界条件测试文件
        edge_case_files = self.generator.create_edge_case_files()
        
        # 保存测试数据信息
        test_data_info = {
            "generated_at": datetime.now().isoformat(),
            "normal_documents": [
                {
                    "filename": doc["filename"],
                    "type": doc["type"],
                    "size": doc["size"],
                    "keywords": doc["keywords"],
                    "title": doc["title"]
                }
                for doc in normal_docs
            ],
            "edge_case_files": list(edge_case_files.keys()),
            "test_scenarios": [
                "正常文件上传测试",
                "大文件上传测试", 
                "不支持格式上传测试",
                "网络中断重试测试",
                "并发上传测试",
                "文件解析测试",
                "搜索功能测试",
                "问答功能测试"
            ]
        }
        
        # 保存文件
        saved_files = self.generator.save_test_files(normal_docs)
        
        # 保存边界条件文件
        edge_case_dir = self.generator.test_data_dir / "edge_cases"
        edge_case_dir.mkdir(exist_ok=True)
        
        for name, content in edge_case_files.items():
            file_path = edge_case_dir / f"{name}.bin"
            with open(file_path, "wb") as f:
                f.write(content)
        
        # 保存测试数据信息
        with open(self.test_data_file, "w", encoding="utf-8") as f:
            json.dump(test_data_info, f, ensure_ascii=False, indent=2)
        
        print(f"测试数据生成完成!")
        print(f"正常文档: {len(normal_docs)} 个")
        print(f"边界条件文件: {len(edge_case_files)} 个")
        print(f"文件保存目录: {self.generator.test_data_dir}")
        print(f"测试数据信息: {self.test_data_file}")
        
        return saved_files
    
    def load_test_data_info(self) -> Dict[str, Any]:
        """加载测试数据信息"""
        if self.test_data_file.exists():
            with open(self.test_data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("清理测试数据...")
        
        # 清理测试文件
        if self.generator.test_data_dir.exists():
            import shutil
            shutil.rmtree(self.generator.test_data_dir)
            print(f"已清理测试数据目录: {self.generator.test_data_dir}")
        
        # 清理测试数据信息文件
        if self.test_data_file.exists():
            self.test_data_file.unlink()
            print(f"已清理测试数据信息文件: {self.test_data_file}")
    
    def get_test_file_path(self, filename: str) -> Optional[Path]:
        """获取测试文件路径"""
        file_path = self.generator.test_data_dir / filename
        if file_path.exists():
            return file_path
        
        # 检查边界条件文件
        edge_case_path = self.generator.test_data_dir / "edge_cases" / f"{filename}.bin"
        if edge_case_path.exists():
            return edge_case_path
            
        return None


def main():
    """主函数：生成系统测试数据"""
    print("=== QMS-Nexus 系统测试数据生成工具 ===")
    
    manager = TestDataManager()
    
    # 生成测试数据
    saved_files = manager.generate_and_save_test_data(count=15)
    
    print(f"\n生成了 {len(saved_files)} 个测试文件:")
    for file_path in saved_files:
        print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
    
    # 显示测试数据信息
    test_data_info = manager.load_test_data_info()
    print(f"\n测试数据信息:")
    print(f"  生成时间: {test_data_info.get('generated_at', 'N/A')}")
    print(f"  测试场景: {len(test_data_info.get('test_scenarios', []))} 个")
    print(f"  边界条件: {len(test_data_info.get('edge_case_files', []))} 个")
    
    return saved_files


if __name__ == "__main__":
    main()