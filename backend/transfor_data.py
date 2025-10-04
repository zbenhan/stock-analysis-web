import sqlite3
from pathlib import Path

def transfer_data(db1_path, db2_path):
    """
    将数据从第一个数据库转换并导入到第二个数据库
    """
    # 确保数据库文件存在
    if not Path(db1_path).exists():
        print(f"错误: 第一个数据库文件不存在: {db1_path}")
        return False
    
    if not Path(db2_path).exists():
        print(f"错误: 第二个数据库文件不存在: {db2_path}")
        return False
    
    try:
        # 连接两个数据库
        conn1 = sqlite3.connect(db1_path)
        conn2 = sqlite3.connect(db2_path)
        cursor1 = conn1.cursor()
        cursor2 = conn2.cursor()
        
        print("开始数据转移...")
        
        # 1. 转移 security_info 表数据
        print("转移 security_info 表数据...")
        cursor1.execute("SELECT security_code, security_name, listing_board, industry_name FROM security_info")
        securities = cursor1.fetchall()
        
        for security in securities:
            try:
                cursor2.execute(
                    "INSERT OR IGNORE INTO security_info (security_code, security_name, listing_board, industry_name) VALUES (?, ?, ?, ?)",
                    security
                )
            except sqlite3.IntegrityError:
                # 如果记录已存在，忽略错误
                pass
        
        print(f"成功转移 {len(securities)} 条证券信息记录")
        
        # 2. 转移 closing_price 表数据
        print("转移 closing_price 表数据...")
        cursor1.execute("SELECT EntryID, security_code, total_share_capital, trade_date, closing_price FROM closing_price")
        closing_prices = cursor1.fetchall()
        
        transferred_count = 0
        for price in closing_prices:
            original_entry_id, security_code, total_share_capital, trade_date, closing_price = price
            
            # 生成新的EntryID: 取security_code前6位 + 原始EntryID
            # 如果security_code长度不足6位，用0填充
            security_code_prefix = security_code[:6].ljust(6, '0') if len(security_code) >= 6 else security_code.ljust(6, '0')
            new_entry_id = security_code_prefix + str(original_entry_id)
            
            try:
                cursor2.execute(
                    "INSERT OR IGNORE INTO closing_price (EntryID, security_code, total_share_capital, trade_date, closing_price) VALUES (?, ?, ?, ?, ?)",
                    (new_entry_id, security_code, total_share_capital, trade_date, closing_price)
                )
                transferred_count += 1
            except sqlite3.IntegrityError:
                # 如果记录已存在，忽略错误
                pass
        
        print(f"成功转移 {transferred_count} 条收盘价记录")
        
        # 3. 转移 financial_report 表数据
        print("转移 financial_report 表数据...")
        cursor1.execute("SELECT security_code, report_period, parent_equity_attributable, net_profit_parent_chareholders FROM financial_report")
        financial_reports = cursor1.fetchall()
        
        transferred_report_count = 0
        for report in financial_reports:
            security_code, report_period, parent_equity_attributable, net_profit_parent_chareholders = report
            
            # 生成ReportID: 取security_code前6位 + report_period去掉"-"字符
            # 如果security_code长度不足6位，用0填充
            security_code_prefix = security_code[:6].ljust(6, '0') if len(security_code) >= 6 else security_code.ljust(6, '0')
            report_period_clean = report_period.replace("-", "")
            report_id = security_code_prefix + report_period_clean
            
            try:
                cursor2.execute(
                    "INSERT OR IGNORE INTO financial_report (ReportID, security_code, report_period, parent_equity_attributable, net_profit_parent_chareholders) VALUES (?, ?, ?, ?, ?)",
                    (report_id, security_code, report_period, parent_equity_attributable, net_profit_parent_chareholders)
                )
                transferred_report_count += 1
            except sqlite3.IntegrityError:
                # 如果记录已存在，忽略错误
                pass
        
        print(f"成功转移 {transferred_report_count} 条财务报告记录")
        
        # 提交事务
        conn2.commit()
        print("数据转移完成！")
        
        # 显示转移后的数据统计
        print("\n转移后第二个数据库的数据统计:")
        cursor2.execute("SELECT COUNT(*) FROM security_info")
        sec_count = cursor2.fetchone()[0]
        print(f"security_info 表记录数: {sec_count}")
        
        cursor2.execute("SELECT COUNT(*) FROM closing_price")
        price_count = cursor2.fetchone()[0]
        print(f"closing_price 表记录数: {price_count}")
        
        cursor2.execute("SELECT COUNT(*) FROM financial_report")
        report_count = cursor2.fetchone()[0]
        print(f"financial_report 表记录数: {report_count}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        if 'conn2' in locals():
            conn2.rollback()
        return False
    except Exception as e:
        print(f"发生未知错误: {e}")
        if 'conn2' in locals():
            conn2.rollback()
        return False
    finally:
        # 关闭数据库连接
        if 'conn1' in locals():
            conn1.close()
        if 'conn2' in locals():
            conn2.close()

def verify_table_structure(db_path):
    """
    验证第二个数据库的表结构是否正确
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = ['security_info', 'closing_price', 'financial_report']
        for table in required_tables:
            if table not in tables:
                print(f"错误: 第二个数据库缺少表 {table}")
                return False
        
        # 检查closing_price表是否有EntryID字段
        cursor.execute("PRAGMA table_info(closing_price)")
        closing_price_columns = [column[1] for column in cursor.fetchall()]
        if 'EntryID' not in closing_price_columns:
            print("错误: closing_price表缺少EntryID字段")
            return False
        
        # 检查financial_report表是否有ReportID字段
        cursor.execute("PRAGMA table_info(financial_report)")
        financial_report_columns = [column[1] for column in cursor.fetchall()]
        if 'ReportID' not in financial_report_columns:
            print("错误: financial_report表缺少ReportID字段")
            return False
        
        print("数据库表结构验证通过")
        return True
        
    except sqlite3.Error as e:
        print(f"验证表结构时发生错误: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    # 数据库路径
    db1_path = r"C:\Users\ben\source\repos\stock_analysis_web\data\stock_data1.db"
    db2_path = r"C:\Users\ben\source\repos\stock_analysis_web\data\stock_data2.db"
    
    print("开始数据转移程序")
    print(f"源数据库: {db1_path}")
    print(f"目标数据库: {db2_path}")
    print("-" * 50)
    
    # 验证第二个数据库的表结构
    if not verify_table_structure(db2_path):
        print("表结构验证失败，程序终止")
        return
    
    # 执行数据转移
    success = transfer_data(db1_path, db2_path)
    
    if success:
        print("\n数据转移成功完成！")
    else:
        print("\n数据转移失败！")

if __name__ == "__main__":
    main()