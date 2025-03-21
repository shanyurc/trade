import sqlite3

def update_database():
    """更新数据库结构，添加price_precision字段"""
    conn = sqlite3.connect('trades.db')
    cursor = conn.cursor()
    
    # 检查price_precision字段是否存在
    cursor.execute("PRAGMA table_info(trades)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    if 'price_precision' not in column_names:
        print("添加price_precision字段...")
        cursor.execute("ALTER TABLE trades ADD COLUMN price_precision INTEGER DEFAULT 2")
        conn.commit()
        print("数据库更新成功!")
    else:
        print("price_precision字段已存在，无需更新。")
    
    conn.close()

if __name__ == "__main__":
    update_database() 