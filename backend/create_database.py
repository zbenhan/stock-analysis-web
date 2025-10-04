# create_database.py
import sqlite3
import os
from pathlib import Path

def create_sqlite_database(db_name='stock_data1111111.db'):
    """
    创建SQLite数据库和表结构
    """
    # 获取项目根目录
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / db_name
    
    print(f"创建数据库: {db_path}")
    
    try:
        # 连接数据库（如果不存在会自动创建）
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建 security_info 表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_info (
            security_code TEXT PRIMARY KEY,
            security_name TEXT NOT NULL,
            listing_board TEXT,
            industry_name TEXT
        )
        ''')
        
        # 创建 closing_price 表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS closing_price (
            EntryID TEXT PRIMARY KEY,
            security_code TEXT NOT NULL,
            total_share_capital TEXT,
            trade_date TEXT,
            closing_price REAL,
            UNIQUE (security_code, EntryID)
        )
        ''')
        
        # 创建 financial_report 表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_report (
            ReportID TEXT PRIMARY KEY,
            security_code TEXT NOT NULL,
            report_period TEXT NOT NULL,
            parent_equity_attributable REAL,
            net_profit_parent_chareholders REAL,
            UNIQUE (security_code, report_period)
        )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_closing_price_security_code 
        ON closing_price(security_code)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_closing_price_trade_date 
        ON closing_price(trade_date)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_financial_report_security_code 
        ON financial_report(security_code)
        ''')
        
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_financial_report_period 
        ON financial_report(report_period)
        ''')
        
        # 提交更改
        conn.commit()
        print("数据库表创建成功！")
        
        # 显示表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("创建的表:", [table[0] for table in tables])
        
    except sqlite3.Error as e:
        print(f"数据库创建错误: {e}")
    finally:
        if conn:
            conn.close()



if __name__ == "__main__":
    # 创建数据库和表
    create_sqlite_database()




