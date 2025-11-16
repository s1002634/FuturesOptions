import shioaji as sj
import json
import sys

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 登入
print("Logging in...")
api = sj.Shioaji(simulation=True)
accounts = api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")

all_contracts = {
    "futures": {},
    "options": {},
    "stocks": {}
}

# 1. 獲取所有期貨合約
print("\n=== 獲取期貨合約 ===")
futures_types = [attr for attr in dir(api.Contracts.Futures)
                 if not attr.startswith('_')
                 and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]

print(f"Total Futures Types: {len(futures_types)}")

for ft in futures_types:
    try:
        futures_obj = getattr(api.Contracts.Futures, ft)
        if hasattr(futures_obj, 'keys'):
            contracts_list = list(futures_obj.keys())
            all_contracts["futures"][ft] = contracts_list
            # 獲取第一個合約的詳細資訊作為範例
            if contracts_list:
                first_contract = futures_obj[contracts_list[0]]
                print(f"  {ft}: {len(contracts_list)} contracts, e.g. {contracts_list[0]}")
    except Exception as e:
        print(f"  Error getting {ft}: {e}")

# 2. 獲取選擇權合約
print("\n=== 獲取選擇權合約 ===")
try:
    options_types = [attr for attr in dir(api.Contracts.Options)
                     if not attr.startswith('_')
                     and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]

    print(f"Total Options Types: {len(options_types)}")

    for ot in options_types[:20]:  # 只處理前20種以節省時間
        try:
            options_obj = getattr(api.Contracts.Options, ot)
            if hasattr(options_obj, 'keys'):
                contracts_list = list(options_obj.keys())
                all_contracts["options"][ot] = contracts_list
                print(f"  {ot}: {len(contracts_list)} contracts")
        except Exception as e:
            print(f"  Error getting {ot}: {e}")
except Exception as e:
    print(f"Error accessing Options: {e}")

# 3. 獲取股票合約（只列出主要股票）
print("\n=== 獲取股票合約 ===")
try:
    # 獲取所有股票代碼
    all_stocks = list(api.Contracts.Stocks.keys())
    print(f"Total Stocks: {len(all_stocks)}")

    # 只儲存前100檔股票作為範例
    all_contracts["stocks"]["all_codes"] = all_stocks[:100]

    # 列出一些熱門股票
    popular_stocks = ['2330', '2317', '2454', '2308', '2303', '3008', '2412', '2881']
    print("Popular Stocks:")
    for code in popular_stocks:
        if code in api.Contracts.Stocks:
            contract = api.Contracts.Stocks[code]
            print(f"  {code}: {contract.name}")
            all_contracts["stocks"][code] = {
                "name": contract.name,
                "code": contract.code,
                "exchange": str(contract.exchange)
            }
except Exception as e:
    print(f"Error getting stocks: {e}")

# 儲存所有合約資訊到 JSON 檔案
print("\n=== 儲存合約資訊到檔案 ===")

with open('all_contracts_complete.json', 'w', encoding='utf-8') as f:
    json.dump(all_contracts, f, indent=2, ensure_ascii=False)

print(f"Done! Saved to all_contracts_complete.json")
print(f"  - Futures: {len(all_contracts['futures'])} types")
print(f"  - Options: {len(all_contracts['options'])} types")
print(f"  - Stocks: {len(all_contracts['stocks'])} items")

# 創建一個簡化版本，只包含期貨的 R1, R2 合約（最近月和次近月）
print("\n=== 創建簡化版期貨列表 ===")
simple_futures = {}
for ft, contracts in all_contracts["futures"].items():
    # 只保留 R1, R2 合約
    r_contracts = [c for c in contracts if 'R1' in c or 'R2' in c]
    if r_contracts:
        simple_futures[ft] = r_contracts

with open('futures_r_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(simple_futures, f, indent=2, ensure_ascii=False)

print(f"Done! Saved {len(simple_futures)} futures types with R1/R2 contracts to futures_r_contracts.json")

# 登出
api.logout()
print("\nComplete!")
