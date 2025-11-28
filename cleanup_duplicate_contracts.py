#!/usr/bin/env python
"""清理資料庫中重複的 Contract 記錄"""
import os
import sys
import django
from collections import defaultdict

# Add web directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from futures.models import Contract

def cleanup_duplicate_contracts():
    """清理重複的契約記錄，保留最新的一筆"""

    print("=" * 60)
    print("清理重複的 Contract 記錄")
    print("=" * 60)

    # 找出所有的契約代碼
    all_contracts = Contract.objects.all().order_by('code', '-updated_at')

    # 按 code 分組
    code_groups = defaultdict(list)
    for contract in all_contracts:
        code_groups[contract.code].append(contract)

    # 找出有重複的 code
    duplicates = {code: contracts for code, contracts in code_groups.items() if len(contracts) > 1}

    if not duplicates:
        print("\n[OK] 沒有發現重複的契約記錄")
        return

    total_duplicates = sum(len(contracts) - 1 for contracts in duplicates.values())
    print(f"\n發現 {len(duplicates)} 個重複的契約代碼")
    print(f"將刪除 {total_duplicates} 筆重複記錄 (保留最新的)")
    print("-" * 60)

    # 顯示前 10 個重複的契約
    print("\n前 10 個重複的契約:")
    for i, (code, contracts) in enumerate(list(duplicates.items())[:10], 1):
        print(f"{i}. {code}: {len(contracts)} 筆記錄")
        for contract in contracts[:3]:  # 顯示前 3 筆
            print(f"   - ID: {contract.id}, 更新時間: {contract.updated_at}")

    if len(duplicates) > 10:
        print(f"... 還有 {len(duplicates) - 10} 個重複的契約代碼")

    # 詢問是否刪除
    print("-" * 60)
    response = input(f"\n是否刪除這 {total_duplicates} 筆重複記錄? (y/n): ")

    if response.lower() != 'y':
        print("\n[CANCELLED] 取消清理作業")
        return

    # 執行清理
    print("\n開始清理...")
    deleted_count = 0

    for code, contracts in duplicates.items():
        # 保留最新的記錄（第一筆），刪除其他的
        latest = contracts[0]
        for contract in contracts[1:]:
            try:
                contract.delete()
                deleted_count += 1
                if deleted_count % 50 == 0:
                    print(f"  已刪除 {deleted_count}/{total_duplicates} 筆...")
            except Exception as e:
                print(f"  [ERROR] 刪除 {code} (ID: {contract.id}) 失敗: {e}")

    print(f"\n{'='*60}")
    print(f"清理完成!")
    print(f"{'='*60}")
    print(f"[OK] 刪除: {deleted_count} 筆重複記錄")
    print(f"[OK] 保留: {len(duplicates)} 個唯一契約 (每個保留最新的)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    cleanup_duplicate_contracts()
