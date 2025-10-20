from django.apps import AppConfig


class StockAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_analysis'

#以下是为从github release下载数据库添加代码
# stock_analysis/apps.py
#from django.apps import AppConfig

class StockAnalysisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_analysis'
    
    def ready(self):
        """
        应用启动时自动初始化数据
        """
        import os
        from django.conf import settings
        
        # 只有在主进程中初始化，避免在多个worker中重复初始化
        if os.environ.get('RUN_MAIN') == 'true' or not hasattr(settings, 'DATA_FILE_AVAILABLE'):
            from .data_manager import init_data
            init_data()