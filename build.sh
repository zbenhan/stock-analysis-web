#!/bin/bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确保前端目录结构存在
echo "=== 创建前端目录结构 ==="
mkdir -p frontend/templates
mkdir -p frontend/static/css
mkdir -p frontend/static/js
mkdir -p frontend/static/images

# 检查文件是否在正确位置
echo "=== 检查项目文件 ==="
find . -name "index.html" -type f
ls -la frontend/templates/ 2>/dev/null || echo "frontend/templates/ 目录不存在"

# 收集静态文件
python manage.py collectstatic --noinput

# 进行数据库迁移（如果需要）
python manage.py migrate

echo "=== 构建完成 ==="