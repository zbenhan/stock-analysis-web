import pandas as pd
import io
import base64
import sqlite3
import os
from django.conf import settings
from .models import SecurityInfo, ClosingPrice, FinancialReport

def get_random_stock_codes(count=10):
    """使用 Django ORM 从数据库随机获取股票代码"""
    try:
        # 使用 Django ORM 的随机排序
        from django.db.models import Subquery, OuterRef
        import random
        
        random_stocks = SecurityInfo.objects.order_by('?')[:count]
        
        stock_codes = [stock.security_code[:6] for stock in random_stocks]
        return stock_codes, "成功"
        
    except Exception as e:
        return None, f"获取随机股票代码失败: {str(e)}"

def get_stock_data(stock_number):
    """获取股票数据"""

    try:
        # 获取股票基本信息
        stock_info = SecurityInfo.objects.filter(
            security_code__startswith=stock_number
        ).first()
        
        if not stock_info:
            return None, f"未找到匹配的股票代码: {stock_number}"
        
        # 获取价格数据
        price_data = ClosingPrice.objects.filter(
            security_code=stock_info.security_code
        ).order_by('trade_date')
        
        # 获取财务数据 - 明确指定字段
        financial_data = FinancialReport.objects.filter(
            security_code=stock_info.security_code
        ).order_by('report_period')
        
        # 转换为DataFrame - 指定需要的字段
        price_df = pd.DataFrame(list(price_data.values()))
        
        # 明确列出 FinancialReport 的实际字段
        financial_fields = ['security_code', 'report_period', 'net_profit_parent_chareholders']  # 根据你的实际字段调整
        financial_df = pd.DataFrame(list(financial_data.values(*financial_fields)))
        
        # 检查数据是否为空
        if price_df.empty:
            return None, f"股票 {stock_number} 的价格数据为空"
        if financial_df.empty:
            return None, f"股票 {stock_number} 的财务数据为空"
        
        return {
            'stock_info': stock_info,
            'price_data': price_df,
            'financial_data': financial_df
        }, "成功"
        
    except Exception as e:
        return None, f"数据获取失败: {str(e)}"

def process_data(price_df, financial_df):
    """数据处理函数"""
    try:
        # 转换数据类型
        price_df['total_share_capital'] = pd.to_numeric(price_df['total_share_capital'], errors='coerce')
        price_df['closing_price'] = pd.to_numeric(price_df['closing_price'], errors='coerce')
        
        # 检查必要字段是否存在
        required_columns = ['total_share_capital', 'closing_price', 'trade_date']
        for col in required_columns:
            if col not in price_df.columns:
                return None, None, f"缺少必要列: {col}"
        
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
        
        return monthly_last_data, financial_df, "成功"
        
    except Exception as e:
        return None, None, f"数据处理失败: {str(e)}"
