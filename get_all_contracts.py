import shioaji as sj
import json

# 登入
api = sj.Shioaji(simulation=True)
accounts = api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")

print("=== 獲取所有商品檔 ===\n")

# 1. 期貨 (Futures)
print("=" * 80)
print("期貨合約 (Futures)")
print("=" * 80)
futures_types = [attr for attr in dir(api.Contracts.Futures)
                 if not attr.startswith('_')
                 and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]

print(f"總共 {len(futures_types)} 種期貨類型\n")

# 顯示前30種期貨及其合約
for i, ft in enumerate(futures_types[:30], 1):
    try:
        futures_obj = getattr(api.Contracts.Futures, ft)
        if hasattr(futures_obj, 'keys'):
            contracts = list(futures_obj.keys())[:5]
            if contracts:
                print(f"{i}. {ft}: {contracts}")
    except:
        pass

print("\n" + "=" * 80)
print("股票 (Stocks)")
print("=" * 80)

# 2. 股票 (Stocks) - 顯示一些範例
try:
    stock_codes = ['2330', '2317', '2454', '2308', '2303']  # 台積電、鴻海、聯發科、台達電、聯電
    print("熱門股票範例:")
    for code in stock_codes:
        if code in api.Contracts.Stocks:
            contract = api.Contracts.Stocks[code]
            print(f"  {code}: {contract.name} ({contract.exchange})")
except Exception as e:
    print(f"獲取股票資訊錯誤: {e}")

print("\n" + "=" * 80)
print("選擇權 (Options)")
print("=" * 80)

# 3. 選擇權 (Options)
try:
    options_types = [attr for attr in dir(api.Contracts.Options)
                     if not attr.startswith('_')
                     and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]
    print(f"總共 {len(options_types)} 種選擇權類型")
    print("前10種選擇權類型:", options_types[:10])
except Exception as e:
    print(f"獲取選擇權資訊錯誤: {e}")

print("\n" + "=" * 80)
print("將所有期貨類型輸出到檔案")
print("=" * 80)

# 將所有期貨類型和合約輸出到 JSON 檔案
all_futures_data = {}
for ft in futures_types:
    try:
        futures_obj = getattr(api.Contracts.Futures, ft)
        if hasattr(futures_obj, 'keys'):
            all_futures_data[ft] = list(futures_obj.keys())
    except:
        pass

with open('all_futures_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(all_futures_data, f, indent=2, ensure_ascii=False)

print(f"Done! Saved {len(all_futures_data)} futures types to all_futures_contracts.json")

# 登出
api.logout()
print("\n完成!")
