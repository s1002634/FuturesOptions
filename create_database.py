#!/usr/bin/env python
"""使用 psycopg2 創建 PostgreSQL 資料庫"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 資料庫設定
DB_NAME = "futures_db"
DB_USER = "postgres"
DB_PASSWORD = "Vv04560456"
DB_HOST = "localhost"
DB_PORT = "5432"

print("=" * 60)
print("創建 PostgreSQL 資料庫")
print("=" * 60)

try:
    # 連線到預設的 postgres 資料庫
    print(f"\n[1/3] 連線到 PostgreSQL 伺服器 ({DB_HOST}:{DB_PORT})...")
    conn = psycopg2.connect(
        dbname='postgres',  # 連線到預設資料庫
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    # 設定自動提交模式（創建資料庫需要）
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print(f"[OK] 成功連線到 PostgreSQL 伺服器")

    # 檢查資料庫是否已存在
    print(f"\n[2/3] 檢查資料庫 '{DB_NAME}' 是否存在...")
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    exists = cursor.fetchone()

    if exists:
        print(f"[INFO] 資料庫 '{DB_NAME}' 已存在")
        response = input(f"\n是否刪除並重建資料庫 '{DB_NAME}'? (y/n): ")

        if response.lower() == 'y':
            print(f"\n[3/3] 刪除並重建資料庫 '{DB_NAME}'...")

            # 中斷所有連線
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{DB_NAME}'
                AND pid <> pg_backend_pid();
            """)

            # 刪除資料庫
            cursor.execute(f"DROP DATABASE {DB_NAME};")
            print(f"[OK] 已刪除資料庫 '{DB_NAME}'")

            # 創建新資料庫
            cursor.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"[OK] 已創建資料庫 '{DB_NAME}'")
        else:
            print("[INFO] 保留現有資料庫")
    else:
        print(f"\n[3/3] 創建資料庫 '{DB_NAME}'...")
        cursor.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"[OK] 已創建資料庫 '{DB_NAME}'")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("資料庫創建完成!")
    print("=" * 60)
    print(f"[OK] 資料庫名稱: {DB_NAME}")
    print(f"[OK] 連線位址: {DB_HOST}:{DB_PORT}")
    print(f"[OK] 使用者: {DB_USER}")
    print("=" * 60)

    print("\n下一步: 執行 Django migrations")
    print("  cd web")
    print("  python manage.py migrate")

except psycopg2.OperationalError as e:
    print(f"\n[ERROR] 無法連線到 PostgreSQL 伺服器")
    print(f"錯誤訊息: {e}")
    print("\n請確認:")
    print(f"1. PostgreSQL 服務是否正在運行")
    print(f"2. 使用者名稱和密碼是否正確 (使用者: {DB_USER}, 密碼: {DB_PASSWORD})")
    print(f"3. PostgreSQL 是否監聽在 {DB_HOST}:{DB_PORT}")
    print("\n檢查 PostgreSQL 服務:")
    print("  powershell -Command \"Get-Service postgresql*\"")
    exit(1)

except Exception as e:
    print(f"\n[ERROR] 發生錯誤: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
