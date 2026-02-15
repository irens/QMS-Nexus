# 检查文件大小
test_content = b'%PDF-1.4\n' + b'oversized file test' * 10000
print(f'文件大小: {len(test_content)} bytes')
print(f'文件大小: {len(test_content) / 1024 / 1024:.2f} MB')
if len(test_content) > 50 * 1024 * 1024:
    print('超过50MB限制')
else:
    print('未超过50MB限制')