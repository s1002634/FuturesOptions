#!/usr/bin/env python
"""驗證 PostgreSQL 資料庫設定"""
import psycopg2

# 資料庫設定
DB_NAME = "futures_db"
DB_USER = "postgres"
DB_PASSWORD = "Vv04560456"
DB_HOST = "localhost"
DB_PORT = "5432"

print("=" * 60)
print("驗證 PostgreSQL 資料庫設定")
print("=" * 60)

try:
    # 連線到資料庫
    print(f"\n[1/3] 連線到資料庫 '{DB_NAME}'...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()
    print("[OK] 成功連線")

    # 查看所有資料表
    print(f"\n[2/3] 查詢資料表...")
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = cursor.fetchall()

    print(f"[OK] 找到 {len(tables)} 個資料表:")
    for table in tables:
        print(f"  - {table[0]}")

    # 檢查關鍵資料表
    print(f"\n[3/3] 檢查關鍵資料表...")
    required_tables = ['contract', 'k_contract']
    existing_table_names = [t[0] for t in tables]

    all_exist = True
    for table_name in required_tables:
        if table_name in existing_table_names:
            # 查詢資料表結構
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print(f"\n  [OK] {table_name} ({len(columns)} 個欄位)")

            # 檢查 is_active 欄位（Contract 資料表）
            if table_name == 'contract':
                column_names = [c[0] for c in columns]
                if 'is_active' in column_names:
                    print(f"    [OK] is_active 欄位存在")
                else:
                    print(f"    [ERROR] is_active 欄位不存在")
                    all_exist = False

            # 顯示前 5 個欄位
            for col in columns[:5]:
                print(f"    - {col[0]}: {col[1]}")
            if len(columns) > 5:
                print(f"    ... 還有 {len(columns) - 5} 個欄位")
        else:
            print(f"  [ERROR] {table_name} 不存在")
            all_exist = False

    # 查詢資料筆數
    print(f"\n資料筆數:")
    cursor.execute("SELECT COUNT(*) FROM contract;")
    contract_count = cursor.fetchone()[0]
    print(f"  - contract: {contract_count} 筆")

    cursor.execute("SELECT COUNT(*) FROM k_contract;")
    k_contract_count = cursor.fetchone()[0]
    print(f"  - k_contract: {k_contract_count} 筆")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    if all_exist:
        print("[OK] PostgreSQL 資料庫設定完成!")
    else:
        print("[WARNING] PostgreSQL 資料庫設定不完整")
    print("=" * 60)
    print(f"資料庫: {DB_NAME}")
    print(f"位址: {DB_HOST}:{DB_PORT}")
    print(f"使用者: {DB_USER}")
    print("=" * 60)

    print("\n下一步:")
    print("1. 啟動 Django API:")
    print("   cd web")
    print("   python manage.py runserver 8111")
    print("\n2. 啟動多連線訂閱系統:")
    print("   cd C:\\Users\\samoi\\Desktop\\FO")
    print("   python config_multi_connection.py")
    print("\n資料庫鎖定問題應該已解決!")

except Exception as e:
    print(f"\n[ERROR] 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
