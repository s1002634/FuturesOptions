import shioaji as sj
import json
import sys

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 登入
print("Logging in...")
api = sj.Shioaji(simulation=True)
accounts = api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")

print("\n=== 獲取所有選擇權合約 ===\n")

# 獲取所有選擇權類型
options_types = [attr for attr in dir(api.Contracts.Options)
                 if not attr.startswith('_')
                 and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]

print(f"Total Options Types: {len(options_types)}\n")

all_options_data = {}
all_options_detail = {}

# 獲取每種選擇權的詳細資訊
for i, ot in enumerate(options_types, 1):
    try:
        options_obj = getattr(api.Contracts.Options, ot)
        if hasattr(options_obj, 'keys'):
            contracts_list = list(options_obj.keys())
            all_options_data[ot] = contracts_list

            print(f"{i}. {ot}: {len(contracts_list)} contracts")

            # 獲取第一個合約的詳細資訊作為範例
            if contracts_list:
                first_contract = options_obj[contracts_list[0]]
                detail_info = {
                    "total_contracts": len(contracts_list),
                    "example_contract": contracts_list[0],
                    "sample_contracts": contracts_list[:5]  # 前5個合約作為範例
                }

                # 嘗試獲取合約詳細資訊
                try:
                    detail_info["contract_info"] = {
                        "code": first_contract.code,
                        "name": getattr(first_contract, 'name', 'N/A'),
                        "category": getattr(first_contract, 'category', 'N/A'),
                        "delivery_month": getattr(first_contract, 'delivery_month', 'N/A'),
                    }
                    print(f"   Example: {first_contract.code} - {getattr(first_contract, 'name', 'N/A')}")
                except Exception as e:
                    print(f"   Could not get detailed info: {e}")

                all_options_detail[ot] = detail_info

    except Exception as e:
        print(f"Error getting {ot}: {e}")

# 儲存完整的選擇權列表
print("\n=== 儲存選擇權資訊到檔案 ===")

with open('all_options_contracts.json', 'w', encoding='utf-8') as f:
    json.dump(all_options_data, f, indent=2, ensure_ascii=False)

print(f"Done! Saved {len(all_options_data)} options types to all_options_contracts.json")

# 儲存詳細資訊
with open('all_options_detail.json', 'w', encoding='utf-8') as f:
    json.dump(all_options_detail, f, indent=2, ensure_ascii=False)

print(f"Done! Saved detailed info to all_options_detail.json")

# 統計資訊
print("\n=== 統計資訊 ===")
total_contracts = sum(len(contracts) for contracts in all_options_data.values())
print(f"Total option types: {len(all_options_data)}")
print(f"Total option contracts: {total_contracts}")

# 顯示一些主要的選擇權類型
print("\n=== 主要選擇權類型 ===")
main_options = {
    'TXO': '台指選擇權',
    'TEO': '電子選擇權',
    'TFO': '金融選擇權',
}

for code, name in main_options.items():
    if code in all_options_data:
        print(f"{code} ({name}): {len(all_options_data[code])} contracts")
    else:
        print(f"{code} ({name}): Not found")

# 登出
api.logout()
print("\nComplete!")
