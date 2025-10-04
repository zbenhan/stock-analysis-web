# -*- coding: utf-8 -*-
import sqlite3, shutil, datetime, time, os, sys

# 1. 先用副本，避免任何锁
db_path = r'D:\db_tmp\stock_data.db'      # 临时副本路径
src_path = r'C:\Users\ben\source\repos\stock_analysis_web\data\stock_data.db'

# ---------- 1. 复制 ----------
os.makedirs(r'D:\db_tmp', exist_ok=True)
shutil.copy2(src_path, db_path)
print("已复制到 D:\\db_tmp，开始离线处理...")

# ---------- 2. 业务同前 ----------
def get_conn(timeout=30):
    return sqlite3.connect(db_path, timeout=timeout)

def update_closing_price():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT EntryID, security_code FROM closing_price")
        for eid, code in cur.fetchall():
            if code and len(str(code)) >= 6:
                new_id = str(code)[:6] + str(eid)
                cur.execute("UPDATE closing_price SET EntryID=? WHERE EntryID=?", (new_id, eid))
        conn.commit()
    print("closing_price 更新完成")

def add_report_id():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(financial_report)")
        if 'ReportID' not in [c[1] for c in cur.fetchall()]:
            cur.execute("ALTER TABLE financial_report ADD COLUMN ReportID TEXT")
        cur.execute("SELECT security_code, report_period FROM financial_report")
        for code, per in cur.fetchall():
            if code and len(str(code)) >= 6 and per:
                rid = str(code)[:6] + str(per)
                cur.execute("UPDATE financial_report SET ReportID=? WHERE security_code=? AND report_period=?", (rid, code, per))
        conn.commit()
    print("financial_report 更新完成")

# ---------- 3. 运行 ----------
update_closing_price()
add_report_id()

# ---------- 4. 复制回去 ----------
shutil.copy2(db_path, src_path)
print("处理完毕，已覆盖回原文件！")
