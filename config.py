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


def get_contract_data(code):
    """從 API 取得 Contract 的最新資料"""
    try:
        response = requests.get(
            f"http://127.0.0.1:8111/api/contracts/{code}/",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"[K線] 取得 {code} 資料失敗: {e}")
        return None


def record_k_line_for_all_contracts(minute_time):
    """記錄所有訂閱合約的 K 線資料"""
    for code in subscribed_codes:
        # 從 Contract API 取得最新資料
        contract_data = get_contract_data(code)

        if contract_data:
            # 準備 K 線資料
            k_data = {
                "exchange": contract_data.get("exchange"),
                "code": contract_data.get("code"),
                "datetime": minute_time + ":00",
                "open": contract_data.get("open"),
                "underlying_price": contract_data.get("underlying_price"),
                "bid_side_total_vol": contract_data.get("bid_side_total_vol"),
                "ask_side_total_vol": contract_data.get("ask_side_total_vol"),
                "avg_price": contract_data.get("avg_price"),
                "close": contract_data.get("close"),
                "high": contract_data.get("high"),
                "low": contract_data.get("low"),
                "amount": contract_data.get("amount"),
                "total_amount": contract_data.get("total_amount"),
                "volume": contract_data.get("volume"),
                "total_volume": contract_data.get("total_volume"),
                "tick_type": contract_data.get("tick_type"),
                "chg_type": contract_data.get("chg_type"),
                "price_chg": contract_data.get("price_chg"),
                "pct_chg": contract_data.get("pct_chg"),
                "simtrade": contract_data.get("simtrade"),
            }

            try:
                response = requests.post(
                    "http://127.0.0.1:8111/api/k-contracts/",
                    json=k_data,
                    timeout=5
                )

                if response.status_code in [200, 201]:
                    print(f"[K線] {code} 記錄成功 | 時間: {minute_time}")
                else:
                    print(f"[K線] {code} 記錄失敗 | 錯誤: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"[K線] {code} 記錄失敗 | 例外: {e}")


def k_line_scheduler():
    """每分鐘的排程器 - 獨立執行緒"""
    global last_k_record_minute

    while True:
        try:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d %H:%M")

            # 每分鐘的第1秒執行記錄
            if now.second == 1 and current_minute != last_k_record_minute:
                last_k_record_minute = current_minute
                print(f"\n{'='*60}")
                print(f"[K線排程] 開始記錄 {current_minute}")
                print(f"{'='*60}")
                record_k_line_for_all_contracts(current_minute)
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
    print(f"Exchange: {exchange} | Code: {tick.code} | Price: {tick.close} | Volume: {tick.volume} | Time: {tick.datetime}")

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
        time.sleep(.5)  # Sleep in short intervals to allow Ctrl+C to work
except KeyboardInterrupt:
    print("\nStopping quote reception")
    api.logout()
    print("Logged out successfully")