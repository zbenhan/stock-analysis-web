import pandas as pd
import io
import base64
import sqlite3
import os
from django.conf import settings
from .models import SecurityInfo, ClosingPrice, FinancialReport
import matplotlib
matplotlib.use("Agg")  # 必须在任何 pyplot 之前
import matplotlib.pyplot as plt

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

def generate_chart(monthly_last_data, financial_df, stock_info):
    """生成图表"""
    try:
        # 明确设置matplotlib配置，避免使用系统字体
        import matplotlib
        matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        
        # 设置中文字体 - 尝试多种方案
        plt.rcParams['font.sans-serif'] = [
            'DejaVu Sans',        # Linux 系统常见字体
            'Arial',              # 跨平台字体
            'Liberation Sans',    # 开源字体
            'Bitstream Vera Sans' # 开源字体
        ]
        plt.rcParams['axes.unicode_minus'] = False
        
        # 强制重新生成字体缓存
        import matplotlib.font_manager as fm
        fm._rebuild()
        
        # 打印可用字体用于调试
        available_fonts = [f.name for f in fm.fontManager.ttflist]
        print(f"可用字体数量: {len(available_fonts)}")
        
        # 检查是否有支持中文的字体
        chinese_support_fonts = [f for f in available_fonts if any(char in f for char in ['CJK', 'Chinese', 'Unicode'])]
        print(f"可能支持中文的字体: {chinese_support_fonts}")
        
        # 创建图表
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 其余代码保持不变...
        # 合并数据
        merged_df = pd.merge(monthly_last_data, financial_df, on='data_date', how='outer')
        merged_df['data_date'] = pd.to_datetime(merged_df['data_date'])
        merged_df = merged_df.sort_values('data_date')
        
        merged_df['market_capitalization'] = pd.to_numeric(merged_df['market_capitalization'], errors='coerce')
        merged_df['net_profit_parent_quarterly'] = pd.to_numeric(merged_df['net_profit_parent_quarterly'], errors='coerce')
        
        # 检查是否有有效数据
        if merged_df['market_capitalization'].isna().all() or merged_df['net_profit_parent_quarterly'].isna().all():
            return None
        
        # 将日期减1年用于显示
        market_data = merged_df.dropna(subset=['market_capitalization']).sort_values('data_date')
        profit_data = merged_df.dropna(subset=['net_profit_parent_quarterly']).sort_values('data_date')
        
        # 创建减1年后的日期用于x轴标签
        market_dates_display = market_data['data_date'] - pd.DateOffset(years=1)
        profit_dates_display = profit_data['data_date'] - pd.DateOffset(years=1)
        
        # 市值图表 - 使用中文
        color = 'darkblue'
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('市值', color=color, fontsize=12)
        
        if market_data.empty:
            return None
            
        line1 = ax1.plot(market_dates_display, market_data['market_capitalization'],
                        color=color, marker='o', linewidth=2, label='市值', markersize=4)
        ax1.tick_params(axis='y', labelcolor=color, labelsize=8)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        
        # 净利润图表 - 使用中文
        ax2 = ax1.twinx()
        color = 'orange'
        
        if profit_data.empty:
            return None
            
        ax2.set_ylabel('净利润', color=color, fontsize=12)
        line2 = ax2.plot(profit_dates_display, profit_data['net_profit_parent_quarterly'],
                        color=color, marker='s', linewidth=2, linestyle='--', 
                        label='净利润', markersize=4)
        ax2.tick_params(axis='y', labelcolor=color, labelsize=8)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        
        # 设置标题和格式 - 使用中文
        plt.title(f'{stock_info.security_name}({stock_info.security_code})市值与净利润趋势分析',
                 fontsize=14, pad=20)
        
        # 图例和网格 - 使用中文
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # 调整布局
        fig.tight_layout()
        
        # 转换为base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        print(f"图表生成错误: {e}")
        import traceback
        traceback.print_exc()
        return None
