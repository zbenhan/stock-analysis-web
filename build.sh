#!/bin/bash
# ��װ Python ����
pip install -r requirements.txt

# ȷ��ǰ��Ŀ¼�ṹ����
echo "=== ����ǰ��Ŀ¼�ṹ ==="
mkdir -p frontend/templates
mkdir -p frontend/static/css
mkdir -p frontend/static/js
mkdir -p frontend/static/images

# ����ļ��Ƿ�����ȷλ��
echo "=== �����Ŀ�ļ� ==="
find . -name "index.html" -type f
ls -la frontend/templates/ 2>/dev/null || echo "frontend/templates/ Ŀ¼������"

# �ռ���̬�ļ�
python manage.py collectstatic --noinput

# �������ݿ�Ǩ�ƣ������Ҫ��
python manage.py migrate

echo "=== ������� ==="