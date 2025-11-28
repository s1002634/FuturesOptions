#!/usr/bin/env python
"""標記已結算的契約資料為不活躍"""
import os
import sys
import django
from datetime import datetime

# Add web directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from futures.models import Contract
from get_active_contracts import get_active_contracts

def mark_expired_contracts():
    """標記已結算（不活躍）的契約資料為 is_active=False"""

    print("=" * 60)
    print("標記已結算契約資料")
    print("=" * 60)

    # 獲取活躍契約
    active_contracts = get_active_contracts()

    if not active_contracts:
        print("[WARNING] 無法找到活躍契約")
        return

    # 取得活躍契約類型
    active_types = set([c['type'] for c in active_contracts])
    print(f"\n活躍契約類型: {', '.join(active_types)}")

    # 查找資料庫中的所有契約
    all_contracts = Contract.objects.all()
    total_count = all_contracts.count()

    print(f"資料庫中總契約數: {total_count}")

    if total_count == 0:
        print("\n[INFO] 資料庫中沒有契約資料，無需標記")
        return

    # 找出需要標記為不活躍的契約（不屬於活躍類型）
    expired_contracts = []
    for contract in all_contracts:
        # 從契約代碼中提取類型 (例如: TX127150L5 -> TX1)
        code = contract.code
        contract_type = None

        # 檢查各種契約類型
        for active_type in ['TXO', 'TX1', 'TX2', 'TX4', 'TX5', 'TXU', 'TXV', 'TXX', 'TXY', 'TXZ']:
            if code.startswith(active_type):
                contract_type = active_type
                break

        # 如果契約類型不在活躍列表中，標記為不活躍
        if contract_type and contract_type not in active_types:
            if contract.is_active:  # 只記錄當前為活躍狀態的
                expired_contracts.append({
                    'code': code,
                    'type': contract_type,
                    'updated_at': contract.updated_at
                })

    if not expired_contracts:
        print("\n[INFO] 沒有需要標記的已結算契約")
        return

    # 顯示將要標記的契約
    print(f"\n找到 {len(expired_contracts)} 個已結算契約:")
    print("-" * 60)

    # 按類型分組統計
    from collections import Counter
    type_counts = Counter([c['type'] for c in expired_contracts])
    for contract_type, count in sorted(type_counts.items()):
        print(f"  {contract_type}: {count} 個")

    # 詢問是否標記
    print("-" * 60)
    response = input(f"\n是否標記這 {len(expired_contracts)} 個已結算契約為不活躍? (y/n): ")

    if response.lower() != 'y':
        print("\n[CANCELLED] 取消標記作業")
        return

    # 執行標記
    print("\n開始標記...")
    marked_count = 0

    for expired in expired_contracts:
        try:
            Contract.objects.filter(code=expired['code']).update(is_active=False)
            marked_count += 1
            if marked_count % 50 == 0:
                print(f"  已標記 {marked_count}/{len(expired_contracts)} 個...")
        except Exception as e:
            print(f"  [ERROR] 標記 {expired['code']} 失敗: {e}")

    print(f"\n{'='*60}")
    print(f"標記完成!")
    print(f"{'='*60}")
    print(f"[OK] 標記為不活躍: {marked_count} 個契約")
    print(f"[OK] 保留為活躍: {total_count - marked_count} 個契約")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    mark_expired_contracts()
