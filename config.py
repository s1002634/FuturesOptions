import shioaji as sj
from shioaji import TickSTKv1, TickFOPv1, Exchange
import time
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import threading

# 全域變數
last_k_record_minute = None
subscribed_codes = set()  # 記錄訂閱的合約代碼

api = sj.Shioaji(simulation=True)   # simulation=True 即表示使用模擬環境
accounts =  api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")
api.activate_ca(
    ca_path="./Sinopac.pfx",
    ca_passwd="L124793253",
    person_id="L124793253",
)


print("Login and activate CA success")


def record_k_line_bulk_snapshot(minute_time):
    """
    批次記錄 K 線快照 - 一次 API 呼叫處理所有合約
    從資料庫的所有 Contract 取得最新資料並批次建立 KContract
    """
    try:
        # 記錄開始時間
        start_time = time.time()

        # 呼叫批次快照 API
        response = requests.post(
            "http://127.0.0.1:8111/api/k-contracts/bulk-snapshot/",
            json={"datetime": minute_time + ":00"},
            timeout=10  # 批次操作可能需要較長時間
        )

        # 計算耗時
        elapsed_time = (time.time() - start_time) * 1000  # 轉換為毫秒

        if response.status_code in [200, 201]:
            result = response.json()
            print(f"[K線批次] 記錄成功 | 時間: {minute_time}")
            print(f"  ✓ 建立筆數: {result.get('created_count')}/{result.get('total_contracts')}")
            print(f"  ✓ API 耗時: {result.get('elapsed_ms', 0):.2f}ms")
            print(f"  ✓ 總耗時: {elapsed_time:.2f}ms")
        else:
            print(f"[K線批次] 記錄失敗 | 錯誤: {response.text}")
            print(f"  ✗ HTTP 狀態碼: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"[K線批次] 記錄失敗 | 例外: {e}")


def k_line_scheduler():
    """每分鐘的排程器 - 獨立執行緒 (使用批次快照)"""
    global last_k_record_minute

    while True:
        try:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d %H:%M")

            # 每分鐘的第1秒執行記錄
            if now.second == 1 and current_minute != last_k_record_minute:
                last_k_record_minute = current_minute
                print(f"\n{'='*60}")
                print(f"[K線排程] 開始記錄 {current_minute} (批次模式)")
                print(f"{'='*60}")
                record_k_line_bulk_snapshot(current_minute)
                print(f"{'='*60}\n")

            time.sleep(0.5)  # 每 0.5 秒檢查一次
        except Exception as e:
            print(f"[K線排程] 錯誤: {e}")
            time.sleep(1)

# Define callback function for futures real-time quotes
@api.on_tick_fop_v1()
def quote_callback(exchange: Exchange, tick: TickFOPv1):
    global subscribed_codes

    # 記錄訂閱的合約代碼
    subscribed_codes.add(tick.code)

    # 準備要發送的資料 - 包含所有必需欄位
    data = {
        "exchange": str(exchange),
        "code": tick.code,
        "datetime": str(tick.datetime),
        "open": round(float(tick.open), 4),
        "underlying_price": round(float(tick.underlying_price), 4),
        "bid_side_total_vol": tick.bid_side_total_vol,
        "ask_side_total_vol": tick.ask_side_total_vol,
        "avg_price": round(float(tick.avg_price), 4) if tick.avg_price else 0.0,
        "close": round(float(tick.close), 4),
        "high": round(float(tick.high), 4),
        "low": round(float(tick.low), 4),
        "amount": round(float(tick.amount), 4),
        "total_amount": round(float(tick.total_amount), 4),
        "volume": tick.volume,
        "total_volume": tick.total_volume,
        "tick_type": tick.tick_type,
        "chg_type": tick.chg_type,
        "price_chg": round(float(tick.price_chg), 4),
        "pct_chg": round(float(tick.pct_chg), 4),
        "simtrade": tick.simtrade
    }

    # 顯示資料
    print(f"Exchange: {exchange} | Code: {tick.code} | Price: {tick.close} | Volume: {tick.volume} | Total_Volume: {tick.total_volume} | Time: {tick.datetime}")

    # 發送到 API - 使用 PUT 更新方式
    try:
        # 記錄開始時間
        start_time = time.time()

        # 使用 code 作為識別碼來更新資料
        response = requests.put(
            f"http://127.0.0.1:8111/api/contracts/{tick.code}/",
            json=data,
            timeout=5
        )

        # 計算耗時
        elapsed_time = (time.time() - start_time) * 1000  # 轉換為毫秒

        print(f"API Response: {response.status_code} | 耗時: {elapsed_time:.2f}ms")
        if response.status_code in [200, 201]:
            print("✓ Data updated successfully")
        else:
            print(f"API Error: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data to API: {e}")

    print("-" * 50)


# Subscribe to different futures contracts
# TXF = 台指期貨 (Taiwan Stock Index Futures)
api.quote.subscribe(
    api.Contracts.Futures.TXF['TXFR1'],  # TXFR1 = nearest month contract
    quote_type = sj.constant.QuoteType.Tick,
    version = sj.constant.QuoteVersion.v1,
)
api.quote.subscribe(
    api.Contracts.Futures.TXF['TXFR2'],  # TXFR1 = nearest month contract
    quote_type = sj.constant.QuoteType.Tick,
    version = sj.constant.QuoteVersion.v1,
)

print("Starting to receive real-time quotes...")
print("Press Ctrl+C to stop")

# 啟動 K 線排程器 (獨立執行緒)
scheduler_thread = threading.Thread(target=k_line_scheduler, daemon=True)
scheduler_thread.start()
print("K 線排程器已啟動 (每分鐘記錄一次)")

# Keep the program running to receive real-time data
try:
    while True:
        time.sleep(.2)  # Sleep in short intervals to allow Ctrl+C to work
except KeyboardInterrupt:
    print("\nStopping quote reception")
    api.logout()
    print("Logged out successfully")