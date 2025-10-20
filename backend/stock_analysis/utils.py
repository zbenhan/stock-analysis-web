# stock_analysis/utils.py
import pandas as pd
import io
import base64
import sqlite3
import os
from django.conf import settings
from .models import SecurityInfo, ClosingPrice, FinancialReport

def check_database_available():
    """
    检查数据库是否可用
    """
    try:
        db_path = os.path.join(settings.BASE_DIR, 'data', 'stock_data.db')
        
        # 检查文件是否存在且大小合理
        if not os.path.exists(db_path) or os.path.getsize(db_path) < 1000000:  # < 1MB
            return False
        
        # 进一步验证数据库是否可以正常连接和查询
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查必要的表是否存在
        required_tables = ['security_info', 'closing_price', 'financial_report']
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                conn.close()
                return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"数据库检查失败: {e}")
        return False

def get_random_stock_codes(count=10):
    """使用 Django ORM 从数据库随机获取股票代码"""
    try:
        # 检查数据库是否可用
        if not check_database_available():
            return None, "数据库文件不可用，请确保数据文件已正确下载。如果这是首次部署，请稍等片刻让数据文件下载完成。"
        
        print(f"从数据库随机获取 {count} 个股票代码")
        
        # 使用 Django ORM 的随机排序
        random_stocks = SecurityInfo.objects.order_by('?')[:count]
        
        if not random_stocks:
            return None, "数据库中未找到股票数据"
        
        stock_codes = [stock.security_code[:6] for stock in random_stocks]
        print(f"成功获取随机股票代码: {stock_codes}")
        return stock_codes, "成功"
        
    except Exception as e:
        error_msg = f"获取随机股票代码失败: {str(e)}"
        print(error_msg)
        return None, error_msg

def get_stock_data(stock_number):
    """获取股票数据"""
    try:
        # 检查数据库是否可用
        if not check_database_available():
            return None, "数据库文件不可用，请确保数据文件已正确下载。如果这是首次部署，请稍等片刻让数据文件下载完成。"
        
        print(f"开始获取股票数据: {stock_number}")
        
        # 获取股票基本信息
        stock_info = SecurityInfo.objects.filter(
            security_code__startswith=stock_number
        ).first()
        
        if not stock_info:
            return None, f"未找到匹配的股票代码: {stock_number}"
        
        print(f"找到股票信息: {stock_info.security_name} ({stock_info.security_code})")
        
        # 获取价格数据
        price_data = ClosingPrice.objects.filter(
            security_code=stock_info.security_code
        ).order_by('trade_date')
        
        # 获取财务数据 - 明确指定字段
        financial_data = FinancialReport.objects.filter(
            security_code=stock_info.security_code
        ).order_by('report_period')
        
        # 转换为DataFrame
        price_df = pd.DataFrame(list(price_data.values()))
        financial_df = pd.DataFrame(list(financial_data.values()))
        
        # 检查数据是否为空
        if price_df.empty:
            return None, f"股票 {stock_number} 的价格数据为空"
        
        if financial_df.empty:
            return None, f"股票 {stock_number} 的财务数据为空"
        
        print(f"成功获取数据 - 价格记录: {len(price_df)}, 财务记录: {len(financial_df)}")
        
        return {
            'stock_info': stock_info,
            'price_data': price_df,
            'financial_data': financial_df
        }, "成功"
        
    except Exception as e:
        error_msg = f"数据获取失败: {str(e)}"
        print(error_msg)
        return None, error_msg

def process_data(price_df, financial_df):
    """数据处理函数"""
    try:
        print("开始处理数据...")
        
        # 检查必要的列是否存在
        required_price_columns = ['total_share_capital', 'closing_price', 'trade_date']
        for col in required_price_columns:
            if col not in price_df.columns:
                return None, None, f"价格数据中缺少必要列: {col}"
        
        # 转换数据类型
        price_df['total_share_capital'] = pd.to_numeric(price_df['total_share_capital'], errors='coerce')
        price_df['closing_price'] = pd.to_numeric(price_df['closing_price'], errors='coerce')
        
        # 计算市值
        price_df['market_capitalization'] = (
            price_df['total_share_capital'] * price_df['closing_price']
        )
        
        # 转换为日期格式
        price_df['trade_date'] = pd.to_datetime(price_df['trade_date'], errors='coerce')
        financial_df['report_period'] = pd.to_datetime(financial_df['report_period'], errors='coerce')
        
        # 月度数据处理
        price_df['year_month'] = price_df['trade_date'].dt.to_period('M')
        last_trading_days = price_df.groupby('year_month')['trade_date'].max().reset_index()
        
        monthly_last_data = pd.merge(
            price_df, last_trading_days, on=['year_month', 'trade_date'], how='inner'
        )
        
        monthly_last_data = monthly_last_data.drop('year_month', axis=1)
        monthly_last_data = monthly_last_data.sort_values('trade_date')
        monthly_last_data['data_date'] = monthly_last_data['trade_date'].dt.to_period('M').dt.end_time
        monthly_last_data['data_date'] = monthly_last_data['data_date'].dt.strftime('%Y-%m-%d')
        
        # 财务数据处理
        financial_df = financial_df.sort_values(by=['security_code', 'report_period'])
        
        # 检查净利润列是否存在
        if 'net_profit_parent_chareholders' not in financial_df.columns:
            return None, None, "财务数据中缺少净利润列"
        
        financial_df['net_profit_parent_quarterly'] = financial_df.groupby('security_code')['net_profit_parent_chareholders'].diff()
        
        mask = financial_df['report_period'].dt.month == 3
        financial_df.loc[mask, 'net_profit_parent_quarterly'] = financial_df.loc[mask, 'net_profit_parent_chareholders']
        financial_df['data_date'] = financial_df['report_period'].dt.strftime('%Y-%m-%d')
        
        print("数据处理完成")
        return monthly_last_data, financial_df, "成功"
        
    except Exception as e:
        error_msg = f"数据处理失败: {str(e)}"
        print(error_msg)
        return None, None, error_msg

def get_database_status():
    """
    获取数据库状态信息
    """
    try:
        db_path = os.path.join(settings.BASE_DIR, 'data', 'stock_data.db')
        
        if not os.path.exists(db_path):
            return {
                'available': False,
                'message': '数据库文件不存在',
                'file_size': 0,
                'file_path': db_path
            }
        
        file_size = os.path.getsize(db_path)
        
        if file_size < 1000000:  # < 1MB
            return {
                'available': False,
                'message': '数据库文件大小异常，可能未正确下载',
                'file_size': file_size,
                'file_path': db_path
            }
        
        # 检查表是否存在
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['security_info', 'closing_price', 'financial_report']
        existing_tables = []
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                existing_tables.append(table)
        
        conn.close()
        
        if len(existing_tables) == len(tables):
            return {
                'available': True,
                'message': '数据库正常',
                'file_size': file_size,
                'file_path': db_path,
                'tables': existing_tables
            }
        else:
            missing_tables = set(tables) - set(existing_tables)
            return {
                'available': False,
                'message': f'数据库表不完整，缺少: {missing_tables}',
                'file_size': file_size,
                'file_path': db_path,
                'tables': existing_tables
            }
            
    except Exception as e:
        return {
            'available': False,
            'message': f'数据库状态检查失败: {str(e)}',
            'file_size': 0,
            'file_path': ''
        }