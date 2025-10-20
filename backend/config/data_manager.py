# stock_analysis/data_manager.py
import os
import requests
from django.conf import settings
import sqlite3
import sys

def ensure_data_file():
    """
    确保数据文件存在，如果不存在则从 GitHub Releases 下载
    """
    data_dir = os.path.join(settings.BASE_DIR, 'data')
    data_file = os.path.join(data_dir, 'stock_data.db')
    
    # 如果文件已存在且大小合理，直接返回路径
    if os.path.exists(data_file) and os.path.getsize(data_file) > 1000000:  # > 1MB
        print("数据文件已存在，使用本地缓存")
        return data_file
    
    # 创建 data 目录
    os.makedirs(data_dir, exist_ok=True)
    
    print("开始下载数据文件...")
    
    # GitHub Releases 下载 URL
    download_url = os.environ.get(
        'DATA_FILE_URL',
        'https://github.com/zbenhan/stock-analysis-web/releases/download/v1.0.1/stock_data.db'
    )
    
    try:
        # 下载文件（设置超时时间）
        response = requests.get(download_url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        # 写入文件并显示进度
        with open(data_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        sys.stdout.write(f"\r下载进度: {progress:.1f}%")
                        sys.stdout.flush()
        
        print("\n数据文件下载完成")
        
        # 验证文件完整性
        if validate_database(data_file):
            print("数据库文件验证成功")
            return data_file
        else:
            print("数据库文件验证失败，删除无效文件")
            os.remove(data_file)
            return None
            
    except Exception as e:
        print(f"\n下载数据文件失败: {e}")
        # 创建空的数据库文件作为备用
        open(data_file, 'a').close()
        print("已创建空的数据库文件作为备用")
        return data_file

def validate_database(db_path):
    """
    验证 SQLite 数据库文件是否有效
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查必要的表是否存在
        tables = ['security_info', 'closing_price', 'financial_report']
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                print(f"缺少必要的表: {table}")
                conn.close()
                return False
        
        conn.close()
        return True
    except Exception as e:
        print(f"数据库验证失败: {e}")
        return False

def init_data():
    """
    初始化数据文件，在应用启动时调用
    """
    data_file = ensure_data_file()
    if data_file and os.path.exists(data_file):
        print(f"数据文件就绪: {data_file}")
        return True
    else:
        print("警告: 数据文件不可用，应用将以降级模式运行")
        return False