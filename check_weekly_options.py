import shioaji as sj
import sys

# 設定輸出編碼為 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 登入
print("Logging in...")
api = sj.Shioaji(simulation=True)
accounts = api.login("DjfiMXMcmwgGeG7752TSKxZggAXJWnPpozUTgFgabmAG", "CEyt2NQcotntHiyMc6nAciApu2iTSxhzMN3fJ5T13UAX")

print("\n=== 查詢週選擇權 / 日選擇權 ===\n")

# 獲取所有選擇權類型
options_types = [attr for attr in dir(api.Contracts.Options)
                 if not attr.startswith('_')
                 and attr not in ['append', 'get', 'keys', 'post_init', 'set_status_fetched']]

print(f"Total Options Types: {len(options_types)}\n")

# 查找可能的週選擇權類型
weekly_keywords = ['W', 'WEEK', 'DAILY', 'TXW', 'TEW', 'TFW']
potential_weekly = []

print("=== 所有選擇權類型 ===")
for ot in options_types:
    # 檢查是否包含週選關鍵字
    is_weekly = any(keyword in ot.upper() for keyword in weekly_keywords)

    try:
        options_obj = getattr(api.Contracts.Options, ot)
        if hasattr(options_obj, 'keys'):
            contracts = list(options_obj.keys())
            print(f"{ot}: {len(contracts)} contracts", end="")

            if is_weekly:
                print(" <-- 可能是週選擇權", end="")
                potential_weekly.append(ot)

            # 顯示前3個合約代碼作為範例
            if contracts:
                print(f" (e.g., {contracts[0]})")
            else:
                print()
    except Exception as e:
        print(f"{ot}: Error - {e}")

# 特別查看 TXO 相關的選擇權
print("\n=== TXO 系列選擇權（台指選擇權）===")
txo_related = [ot for ot in options_types if 'TX' in ot]
for ot in txo_related:
    try:
        options_obj = getattr(api.Contracts.Options, ot)
        if hasattr(options_obj, 'keys'):
            contracts = list(options_obj.keys())[:3]
            print(f"{ot}: {contracts}")

            # 檢查合約詳情
            if contracts:
                first_contract = options_obj[contracts[0]]
                print(f"  Example: {first_contract.code} - {getattr(first_contract, 'name', 'N/A')}")
                print(f"  Delivery: {getattr(first_contract, 'delivery_month', 'N/A')}")
    except Exception as e:
        print(f"{ot}: Error - {e}")

# 查看是否有 Weekly Options
print("\n=== 檢查是否有專門的週選擇權屬性 ===")
if hasattr(api.Contracts, 'WeeklyOptions'):
    print("Found WeeklyOptions!")
    weekly_types = dir(api.Contracts.WeeklyOptions)
    print(f"Weekly Option Types: {weekly_types}")
else:
    print("沒有找到 WeeklyOptions 屬性")

# 查看期貨交易所是否有週選擇權說明
print("\n=== 台灣期貨交易所的選擇權類型 ===")
print("""
台灣期貨交易所提供的主要選擇權：

1. 月選擇權 (Monthly Options)
   - TXO: 台指選擇權（每月第三個星期三到期）
   - TEO: 電子選擇權（每月到期）
   - TFO: 金融選擇權（每月到期）

2. 週選擇權 (Weekly Options)
   - TXW: 台指週選擇權（如果有的話）
   - 通常每週到期

3. 一般選擇權命名規則：
   - TX4, TXV, TXX, TXY 可能是不同週期的台指選擇權

讓我們檢查這些代碼的合約...
""")

# 詳細檢查 TX 系列
print("\n=== TX 系列詳細資訊 ===")
for ot in ['TXO', 'TX4', 'TXV', 'TXX', 'TXY']:
    if ot in options_types:
        try:
            options_obj = getattr(api.Contracts.Options, ot)
            if hasattr(options_obj, 'keys'):
                contracts = list(options_obj.keys())
                print(f"\n{ot}:")
                print(f"  Total contracts: {len(contracts)}")

                # 檢查前5個合約
                for contract_code in contracts[:5]:
                    contract = options_obj[contract_code]
                    print(f"  - {contract.code}: {getattr(contract, 'name', 'N/A')}")
                    print(f"    Delivery: {getattr(contract, 'delivery_month', 'N/A')}")
        except Exception as e:
            print(f"{ot}: Error - {e}")

api.logout()
print("\nComplete!")
