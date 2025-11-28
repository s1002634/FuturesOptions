#!/usr/bin/env python
"""
自動獲取當天活躍的臺指選擇權契約代碼
根據當前日期計算哪些契約是活躍的
"""
import shioaji as sj
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

def get_nth_weekday(year, month, weekday, n):
    """
    獲取某月第N個特定星期幾的日期
    weekday: 0=週一, 1=週二, 2=週三, 3=週四, 4=週五, 5=週六, 6=週日
    n: 1=第一週, 2=第二週, 3=第三週, 4=第四週, 5=第五週
    """
    from calendar import monthcalendar
    cal = monthcalendar(year, month)

    # 找到第n個該星期幾
    count = 0
    for week in cal:
        if week[weekday] != 0:
            count += 1
            if count == n:
                return datetime(year, month, week[weekday])
    return None

def get_active_contracts(today=None):
    """
    根據今天的日期，返回活躍的契約類型和到期日

    返回格式:
    [
        {'type': 'TXY', 'expiry': datetime(2025, 11, 28), 'days_left': 2},
        {'type': 'TX1', 'expiry': datetime(2025, 12, 3), 'days_left': 7},
        ...
    ]
    """
    if today is None:
        today = datetime.now()

    active_contracts = []

    # 計算本月和下個月
    current_month = today.month
    current_year = today.year

    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1

    # 定義契約類型和對應的到期規則
    # 週三到期契約
    wednesday_contracts = [
        ('TX1', 1),  # 第1週週三
        ('TX2', 2),  # 第2週週三
        ('TXO', 3),  # 第3週週三 (月到期)
        ('TX4', 4),  # 第4週週三
        ('TX5', 5),  # 第5週週三
    ]

    # 週五到期契約
    friday_contracts = [
        ('TXU', 1),  # 第1週週五
        ('TXV', 2),  # 第2週週五
        ('TXX', 3),  # 第3週週五
        ('TXY', 4),  # 第4週週五
        ('TXZ', 5),  # 第5週週五
    ]

    # 檢查本月的契約
    for contract_type, week_num in wednesday_contracts:
        expiry = get_nth_weekday(current_year, current_month, 2, week_num)  # 2 = 週三
        if expiry and expiry >= today:
            days_left = (expiry - today).days
            active_contracts.append({
                'type': contract_type,
                'expiry': expiry,
                'days_left': days_left,
                'month': f'{current_year}-{current_month:02d}'
            })

    for contract_type, week_num in friday_contracts:
        expiry = get_nth_weekday(current_year, current_month, 4, week_num)  # 4 = 週五
        if expiry and expiry >= today:
            days_left = (expiry - today).days
            active_contracts.append({
                'type': contract_type,
                'expiry': expiry,
                'days_left': days_left,
                'month': f'{current_year}-{current_month:02d}'
            })

    # 檢查下個月的契約（期交所會提前加掛次2週的契約）
    for contract_type, week_num in wednesday_contracts[:2]:  # TX1, TX2
        expiry = get_nth_weekday(next_year, next_month, 2, week_num)
        if expiry:
            days_left = (expiry - today).days
            if days_left <= 14:  # 只加掛2週內的契約
                active_contracts.append({
                    'type': contract_type,
                    'expiry': expiry,
                    'days_left': days_left,
                    'month': f'{next_year}-{next_month:02d}'
                })

    for contract_type, week_num in friday_contracts[:2]:  # TXU, TXV
        expiry = get_nth_weekday(next_year, next_month, 4, week_num)
        if expiry:
            days_left = (expiry - today).days
            if days_left <= 14:  # 只加掛2週內的契約
                active_contracts.append({
                    'type': contract_type,
                    'expiry': expiry,
                    'days_left': days_left,
                    'month': f'{next_year}-{next_month:02d}'
                })

    # 按到期日排序
    active_contracts.sort(key=lambda x: x['expiry'])

    return active_contracts

def get_most_active_contract(today=None):
    """
    獲取最活躍的契約類型（最接近到期的）
    """
    active = get_active_contracts(today)
    if not active:
        return None

    # 返回最接近到期但還有至少1天的契約
    for contract in active:
        if contract['days_left'] >= 1:
            return contract

    # 如果都要到期了，返回第一個
    return active[0] if active else None

def fetch_contract_codes(api, contract_type):
    """
    從 Shioaji API 獲取指定類型的所有契約代碼
    """
    try:
        # 根據契約類型獲取
        if contract_type == 'TXO':
            contracts = api.Contracts.Options.TXO
        elif contract_type == 'TX1':
            contracts = api.Contracts.Options.TX1
        elif contract_type == 'TX2':
            contracts = api.Contracts.Options.TX2
        elif contract_type == 'TX4':
            contracts = api.Contracts.Options.TX4
        elif contract_type == 'TX5':
            contracts = api.Contracts.Options.TX5
        elif contract_type == 'TXU':
            contracts = api.Contracts.Options.TXU
        elif contract_type == 'TXV':
            contracts = api.Contracts.Options.TXV
        elif contract_type == 'TXX':
            contracts = api.Contracts.Options.TXX
        elif contract_type == 'TXY':
            contracts = api.Contracts.Options.TXY
        elif contract_type == 'TXZ':
            contracts = api.Contracts.Options.TXZ
        else:
            print(f"Unknown contract type: {contract_type}")
            return []

        # 獲取所有契約代碼
        codes = [contract.code for contract in contracts]
        return codes
    except Exception as e:
        print(f"Error fetching {contract_type} contracts: {e}")
        return []

if __name__ == "__main__":
    print("=" * 60)
    print("臺指選擇權活躍契約分析")
    print("=" * 60)

    today = datetime.now()
    print(f"\n今天日期: {today.strftime('%Y-%m-%d (%A)')}")

    # 獲取活躍契約
    active = get_active_contracts(today)

    print(f"\n目前活躍的契約 ({len(active)} 個):")
    print("-" * 60)
    for i, contract in enumerate(active, 1):
        print(f"{i}. {contract['type']:4} | "
              f"到期: {contract['expiry'].strftime('%Y-%m-%d (%a)')} | "
              f"剩餘: {contract['days_left']:2} 天 | "
              f"月份: {contract['month']}")

    # 獲取最活躍的契約
    most_active = get_most_active_contract(today)

    if most_active:
        print("\n" + "=" * 60)
        print("推薦訂閱的契約（最活躍）")
        print("=" * 60)
        print(f"契約類型: {most_active['type']}")
        print(f"到期日期: {most_active['expiry'].strftime('%Y-%m-%d (%A)')}")
        print(f"剩餘天數: {most_active['days_left']} 天")

        # 嘗試連接 Shioaji 並獲取契約代碼
        try:
            load_dotenv()
            api = sj.Shioaji(simulation=False)
            api.login(
                os.getenv('SHIOAJI_API_KEY', 'FFN9N94adMtjyGBSJ9NzTwKokSbTAw4oZ5kDFEkPdB4T'),
                os.getenv('SHIOAJI_SECRET_KEY', 'EAdpeiNPqEPMH4QdJdQ9PvhbKTcW8TJyvHgeaTrKAgon')
            )

            print(f"\n正在獲取 {most_active['type']} 的契約代碼...")
            codes = fetch_contract_codes(api, most_active['type'])

            if codes:
                print(f"找到 {len(codes)} 個契約")

                # 儲存到 JSON 檔案
                filename = f"{most_active['type'].lower()}_contracts_list.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(codes, f, ensure_ascii=False, indent=2)

                print(f"✓ 已儲存至: {filename}")
                print(f"\n前 10 個契約代碼:")
                for code in codes[:10]:
                    print(f"  - {code}")
            else:
                print("⚠️  未找到契約代碼")

            api.logout()

        except Exception as e:
            print(f"\n⚠️  無法連接 Shioaji: {e}")
            print("請確認 API 金鑰和憑證設定正確")

    print("\n" + "=" * 60)
