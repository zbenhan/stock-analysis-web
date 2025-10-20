# stock_analysis/apps.py
from django.apps import AppConfig
import os
from django.conf import settings

class StockAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_analysis'
    
    def ready(self):
        """
        应用启动时自动下载数据文件
        """
        # 只有在主进程中初始化，避免在多个worker中重复初始化
        if os.environ.get('RUN_MAIN') == 'true' or not hasattr(settings, '_data_file_initialized'):
            self.download_data_file()
            settings._data_file_initialized = True
    
    def download_data_file(self):
        """
        下载数据文件
        """
        # 延迟导入 requests
        import requests
        import sys
        
        data_dir = os.path.join(settings.BASE_DIR, 'data')
        data_file = os.path.join(data_dir, 'stock_data.db')
        
        # 如果文件已存在且大小合理，直接返回
        if os.path.exists(data_file) and os.path.getsize(data_file) > 1000000:
            print("数据文件已存在，使用本地缓存")
            return
        
        # 创建 data 目录
        os.makedirs(data_dir, exist_ok=True)
        
        print("开始下载数据文件...")
        
        # GitHub Releases 下载 URL
        download_url = os.environ.get(
            'DATA_FILE_URL',
            'https://github.com/zbenhan/stock-analysis-web/releases/download/v1.0.1/stock_data.db'
        )
        
        try:
            # 下载文件
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
            
        except Exception as e:
            print(f"\n下载数据文件失败: {e}")
            # 创建空的数据库文件作为备用
            open(data_file, 'a').close()
            print("已创建空的数据库文件作为备用")