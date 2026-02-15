# 创建真正的超大文件测试数据
oversized_content = b'%PDF-1.4\n' + b'oversized file test content for medical device quality management system testing and ISO13485 standard compliance verification' * 1000000
print(f'超大文件大小: {len(oversized_content)} bytes')
print(f'超大文件大小: {len(oversized_content) / 1024 / 1024:.2f} MB')
if len(oversized_content) > 50 * 1024 * 1024:
    print('✅ 超过50MB限制')
else:
    print('❌ 未超过50MB限制')