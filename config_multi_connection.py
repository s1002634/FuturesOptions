import shioaji as sj
from shioaji import TickSTKv1, TickFOPv1, Exchange
import time
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
import threading
from get_active_contracts import get_active_contracts, fetch_contract_codes

# 全域變數
last_k_record_minute = None
subscribed_codes = set()  # 記錄訂閱的合約代碼
api_connections = []  # 儲存所有 API 連線

# API 憑證
API_KEY = "FFN9N94adMtjyGBSJ9NzTwKokSbTAw4oZ5kDFEkPdB4T"
SECRET_KEY = "EAdpeiNPqEPMH4QdJdQ9PvhbKTcW8TJyvHgeaTrKAgon"
CA_PATH = "./Sinopac.pfx"
CA_PASSWD = "L124793253"
PERSON_ID = "L124793253"

# 每個連線的訂閱上限
SUBSCRIPTION_LIMIT_PER_CONNECTION = 200
# 最大連線數
MAX_CONNECTIONS = 5

def create_api_connection(connection_id):
    """創建一個新的 API 連線"""
    try:
        print(f"\n[連線 {connection_id}] 正在建立連線...")
        api = sj.Shioaji(simulation=False)

        # 登入
        accounts = api.login(API_KEY, SECRET_KEY)
        print(f"[連線 {connection_id}] 登入成功")

        # 啟用憑證
        api.activate_ca(
            ca_path=CA_PATH,
            ca_passwd=CA_PASSWD,
            person_id=PERSON_ID,
        )
        print(f"[連線 {connection_id}] 憑證啟用成功")

        return api
    except Exception as e:
        print(f"[連線 {connection_id}] 建立失敗: {e}")
        return None

def create_quote_callback(api_instance):
    """為每個 API 實例創建專屬的 callback"""
    @api_instance.on_tick_fop_v1()
    def quote_callback(exchange: Exchange, tick: TickFOPv1):
        global subscribed_codes

        # 記錄訂閱的合約代碼
        subscribed_codes.add(tick.code)

        # 準備要發送的資料
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

        # 發送到 API
        try:
            start_time = time.time()
            response = requests.put(
                f"http://127.0.0.1:8111/api/contracts/{tick.code}/",
                json=data,
                timeout=5
            )
            elapsed_time = (time.time() - start_time) * 1000

            print(f"API Response: {response.status_code} | 耗時: {elapsed_time:.2f}ms")
            if response.status_code in [200, 201]:
                print("[OK] Data updated successfully")
            else:
                print(f"API Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send data to API: {e}")

        print("-" * 50)

    return quote_callback

def k_line_scheduler():
    """每分鐘的排程器 - 獨立執行緒 (只記錄活躍契約)"""
    global last_k_record_minute, subscribed_codes

    while True:
        try:
            now = datetime.now()
            current_minute = now.strftime("%Y-%m-%d %H:%M")

            # 每分鐘的第1秒執行記錄
            if now.second == 1 and current_minute != last_k_record_minute:
                last_k_record_minute = current_minute

                # 檢查是否有訂閱的契約
                if not subscribed_codes:
                    print(f"\n[K線排程] {current_minute} - 尚無訂閱契約，跳過記錄")
                    time.sleep(0.5)
                    continue

                print(f"\n{'='*60}")
                print(f"[K線排程] 開始記錄 {current_minute} (活躍契約: {len(subscribed_codes)} 個)")
                print(f"{'='*60}")

                try:
                    start_time = time.time()

                    # 只記錄已訂閱（活躍）的契約
                    # 傳遞訂閱的契約代碼列表給 API，只記錄這些活躍契約
                    response = requests.post(
                        "http://127.0.0.1:8111/api/k-contracts/bulk-snapshot/",
                        json={
                            "datetime": current_minute + ":00",
                            "contract_codes": list(subscribed_codes)  # 只記錄活躍契約
                        },
                        timeout=10
                    )
                    elapsed_time = (time.time() - start_time) * 1000

                    if response.status_code in [200, 201]:
                        result = response.json()
                        created_count = result.get('created_count', 0)
                        print(f"[K線批次] 記錄成功 | 時間: {current_minute}")
                        print(f"  [OK] 建立筆數: {created_count}/{len(subscribed_codes)} 個 K 線記錄")
                        print(f"  [OK] 活躍契約: {len(subscribed_codes)} 個 (只記錄已訂閱)")
                        print(f"  [OK] API 耗時: {result.get('elapsed_ms', 0):.2f}ms")
                        print(f"  [OK] 總耗時: {elapsed_time:.2f}ms")
                    else:
                        print(f"[K線批次] 記錄失敗 | 錯誤: {response.text}")
                        print(f"  [ERROR] HTTP 狀態碼: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"[K線批次] 記錄失敗 | 例外: {e}")

                print(f"{'='*60}\n")

            time.sleep(0.5)
        except Exception as e:
            print(f"[K線排程] 錯誤: {e}")
            time.sleep(1)

def subscribe_with_multiple_connections(contract_batches):
    """使用多個連線訂閱契約（優化版：填滿每個連線）"""

    print(f"\n{'='*60}")
    print(f"多連線訂閱系統（優化配額分配）")
    print(f"{'='*60}")
    print(f"總契約數: {sum(batch['total_count'] for batch in contract_batches)}")
    print(f"需要連線數: {len(contract_batches)}")
    print(f"{'='*60}\n")

    total_subscribed = 0
    total_failed = 0

    for i, batch in enumerate(contract_batches, 1):
        type_groups = batch['type_groups']
        total_count = batch['total_count']

        print(f"\n{'='*60}")
        print(f"[連線 {i}] 訂閱混合契約 ({total_count} 個)")
        print(f"{'='*60}")

        # 顯示此批次包含的契約類型和數量
        for contract_type, codes in type_groups.items():
            print(f"  - {contract_type}: {len(codes)} 個")
        print(f"{'='*60}")

        # 創建新連線
        api = create_api_connection(i)
        if not api:
            print(f"[連線 {i}] 跳過此批次")
            continue

        # 註冊 callback (所有連線都需要註冊以接收報價)
        create_quote_callback(api)

        api_connections.append(api)

        # 訂閱此批次中的所有契約（按類型分組訂閱）
        batch_subscribed = 0
        batch_failed = 0

        for contract_type, contract_codes in type_groups.items():
            # 獲取契約物件
            try:
                contract_obj = getattr(api.Contracts.Options, contract_type, None)
            except AttributeError:
                contract_obj = None

            if not contract_obj:
                print(f"  [連線 {i}] 契約類型 {contract_type} 不存在，跳過 {len(contract_codes)} 個")
                batch_failed += len(contract_codes)
                continue

            # 訂閱此類型的所有契約
            type_subscribed = 0
            type_failed = 0

            for code in contract_codes:
                try:
                    api.quote.subscribe(
                        contract_obj[code],
                        quote_type=sj.constant.QuoteType.Tick,
                        version=sj.constant.QuoteVersion.v1,
                    )
                    type_subscribed += 1
                    batch_subscribed += 1

                    # 每 50 個顯示進度
                    if batch_subscribed % 50 == 0:
                        print(f"  [連線 {i}] 已訂閱 {batch_subscribed}/{total_count} 個...")
                except Exception as e:
                    print(f"  [連線 {i}] 訂閱 {code} 失敗: {e}")
                    type_failed += 1
                    batch_failed += 1

            print(f"  [連線 {i}] {contract_type} 訂閱: {type_subscribed}/{len(contract_codes)} 個")
            if type_failed > 0:
                print(f"  [連線 {i}] {contract_type} 失敗: {type_failed} 個")

        print(f"\n[連線 {i}] 批次訂閱完成: {batch_subscribed}/{total_count} 個")
        if batch_failed > 0:
            print(f"[連線 {i}] 批次失敗: {batch_failed} 個")

        total_subscribed += batch_subscribed
        total_failed += batch_failed

        # 稍微延遲，避免太快建立連線
        if i < len(contract_batches):
            time.sleep(2)

    return total_subscribed, total_failed

# 主程式
if __name__ == "__main__":
    print("="*60)
    print("多連線自動契約訂閱系統")
    print("="*60)

    # 獲取所有活躍的契約
    active_contracts = get_active_contracts()
    tradeable_contracts = [c for c in active_contracts if c['days_left'] >= 0]

    if not tradeable_contracts:
        print("[WARNING] 無法找到活躍契約，請檢查日期設定")
        exit(1)

    print(f"\n找到 {len(tradeable_contracts)} 個可交易的契約:")
    print("-" * 60)
    for contract in tradeable_contracts:
        expiry_date = contract['expiry'].strftime('%Y-%m-%d (%a)')
        print(f"  {contract['type']:4} | 到期: {expiry_date} | 剩餘: {contract['days_left']:2} 天")
    print("-" * 60)

    # 創建第一個連線來獲取契約代碼
    print("\n[主連線] 建立連線以獲取契約代碼...")
    main_api = create_api_connection(0)
    if not main_api:
        print("[ERROR] 無法建立主連線")
        exit(1)

    # 獲取所有契約代碼並分批
    all_contract_codes = []

    for contract_info in tradeable_contracts:
        contract_type = contract_info['type']
        print(f"\n正在獲取 {contract_type} 的契約代碼...")

        codes = fetch_contract_codes(main_api, contract_type)
        if codes:
            print(f"[OK] {contract_type}: {len(codes)} 個契約")

            # 儲存到 JSON
            json_filename = f"{contract_type.lower()}_contracts_list.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(codes, f, ensure_ascii=False, indent=2)

            all_contract_codes.append({
                'type': contract_type,
                'codes': codes
            })
        else:
            print(f"[WARNING] 未找到 {contract_type} 契約代碼")

    # 登出主連線
    main_api.logout()
    print("\n[主連線] 已登出")

    # 優化批次分配：盡量填滿每個連線的 200 個配額
    contract_batches = []
    current_batch = []  # 當前批次的契約列表

    # 將所有契約代碼展開成單一列表，並記錄每個契約的類型
    all_contracts_flat = []
    for contract_group in all_contract_codes:
        contract_type = contract_group['type']
        codes = contract_group['codes']
        for code in codes:
            all_contracts_flat.append({
                'type': contract_type,
                'code': code
            })

    # 按照契約類型分組，盡量填滿每個批次
    for contract_info in all_contracts_flat:
        current_batch.append(contract_info)

        # 當批次達到 200 個時，創建新批次
        if len(current_batch) >= SUBSCRIPTION_LIMIT_PER_CONNECTION:
            contract_batches.append(current_batch[:SUBSCRIPTION_LIMIT_PER_CONNECTION])
            current_batch = current_batch[SUBSCRIPTION_LIMIT_PER_CONNECTION:]

    # 處理剩餘的契約
    if current_batch:
        contract_batches.append(current_batch)

    # 重新組織批次格式：將同一批次中的契約按類型分組
    formatted_batches = []
    for batch in contract_batches:
        # 按契約類型分組
        type_groups = {}
        for contract_info in batch:
            contract_type = contract_info['type']
            if contract_type not in type_groups:
                type_groups[contract_type] = []
            type_groups[contract_type].append(contract_info['code'])

        formatted_batches.append({
            'contracts': batch,
            'type_groups': type_groups,
            'total_count': len(batch)
        })

    contract_batches = formatted_batches

    # 檢查是否超過連線限制
    if len(contract_batches) > MAX_CONNECTIONS:
        print(f"\n[WARNING] 需要 {len(contract_batches)} 個連線，但上限為 {MAX_CONNECTIONS}")
        print(f"[WARNING] 只會訂閱前 {MAX_CONNECTIONS * SUBSCRIPTION_LIMIT_PER_CONNECTION} 個契約")
        contract_batches = contract_batches[:MAX_CONNECTIONS]

    # 使用多連線訂閱
    total_subscribed, total_failed = subscribe_with_multiple_connections(contract_batches)

    # 總結
    print(f"\n{'='*60}")
    print(f"所有契約訂閱完成!")
    print(f"{'='*60}")
    print(f"[OK] 使用連線數: {len(api_connections)}")
    print(f"[OK] 總成功: {total_subscribed} 個合約")
    if total_failed > 0:
        print(f"[ERROR] 總失敗: {total_failed} 個合約")

    # 收集所有訂閱的契約類型
    all_types = set()
    for batch in contract_batches:
        all_types.update(batch['type_groups'].keys())
    print(f"[OK] 訂閱類型: {', '.join(sorted(all_types))}")

    # 顯示每個連線的使用率
    print(f"\n連線使用率:")
    for idx, batch in enumerate(contract_batches, 1):
        usage_pct = (batch['total_count'] / SUBSCRIPTION_LIMIT_PER_CONNECTION) * 100
        print(f"  連線 {idx}: {batch['total_count']}/200 ({usage_pct:.1f}%)")

    print(f"{'='*60}\n")

    # 顯示用量
    if api_connections:
        print(api_connections[0].usage())

    print("\nStarting to receive real-time quotes...")
    print("Press Ctrl+C to stop")

    # 啟動 K 線排程器
    scheduler_thread = threading.Thread(target=k_line_scheduler, daemon=True)
    scheduler_thread.start()
    print("K 線排程器已啟動 (每分鐘記錄一次)")

    # 保持程式運行
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n\nStopping quote reception")
        for i, api in enumerate(api_connections, 1):
            try:
                api.logout()
                print(f"[連線 {i}] 已登出")
            except:
                pass
        print("All connections logged out successfully")
