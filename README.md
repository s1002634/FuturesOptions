# 台指選擇權期貨訂閱系統

使用 Shioaji API 自動訂閱台指選擇權的即時報價，並將資料儲存到 PostgreSQL 資料庫。

## 系統架構

```
FO/
├── web/                          # Django 後端
│   ├── backend/                  # Django 專案設定
│   ├── futures/                  # 期貨應用程式
│   │   ├── models.py            # 資料模型 (Contract, KContract)
│   │   ├── views.py             # API endpoints
│   │   └── migrations/          # 資料庫遷移檔案
│   └── manage.py                # Django 管理指令
│
├── config_multi_connection.py   # 主要訂閱程式（多連線版本）
├── get_active_contracts.py      # 獲取活躍契約工具
│
├── create_database.py           # 創建 PostgreSQL 資料庫
├── verify_postgresql.py         # 驗證資料庫設定
├── mark_expired_contracts.py    # 標記過期契約
├── cleanup_duplicate_contracts.py        # 手動清理重複契約
├── cleanup_duplicate_contracts_auto.py   # 自動清理重複契約
│
├── tx1_contracts_list.json      # TX1 契約列表（自動生成）
├── tx2_contracts_list.json      # TX2 契約列表（自動生成）
├── txu_contracts_list.json      # TXU 契約列表（自動生成）
├── txy_contracts_list.json      # TXY 契約列表（自動生成）
├── tx4_contracts_list.json      # TX4 契約列表（自動生成）
│
├── Sinopac.pfx                  # 憑證檔案
├── requirements.txt             # Python 套件依賴
└── .gitignore                   # Git 忽略檔案設定
```

## 文件

- [POSTGRESQL_SETUP_GUIDE.md](POSTGRESQL_SETUP_GUIDE.md) - PostgreSQL 設定完整指南
- [AUTO_CONTRACT_SELECTION_GUIDE.md](AUTO_CONTRACT_SELECTION_GUIDE.md) - 自動契約選擇系統說明
- [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md) - API 快速參考

## 快速開始

### 1. 啟動 Django API

```bash
cd web
python manage.py runserver 8111
```

### 2. 啟動多連線訂閱系統

```bash
python config_multi_connection.py
```

系統會自動：
- 獲取所有活躍的台指選擇權契約（剩餘天數 ≥ 1 天）
- 使用多個連線訂閱所有契約（每連線最多 200 個）
- 接收即時報價並更新到 PostgreSQL
- 每分鐘記錄 K 線資料

## 資料庫

### PostgreSQL 設定

```
資料庫名稱: futures_db
使用者: postgres
位址: localhost:5432
```

### 資料表

- **contract** - 即時報價資料（每筆 tick 更新）
- **k_contract** - K 線資料（每分鐘記錄一次）

## 主要功能

### 多連線訂閱

- 支援最多 5 個同時連線
- 每個連線可訂閱 200 個契約
- 自動分配契約到不同連線
- 所有連線共用 callback 更新資料庫

### 自動契約選擇

- 自動識別活躍契約（TX1, TX2, TXU, TXV, TXX, TXY, TXZ 等）
- 自動過濾即將到期的契約（剩餘天數 < 1）
- 自動獲取契約代碼並儲存為 JSON

### K 線記錄

- 每分鐘自動記錄一次
- 只記錄已訂閱的活躍契約
- 使用批次 API 提升效能

### 契約生命週期管理

- `is_active` 欄位標記契約狀態
- 使用 `mark_expired_contracts.py` 標記過期契約
- 保留歷史資料供分析使用

## 資料庫管理

### 創建資料庫

```bash
python create_database.py
```

### 驗證設定

```bash
python verify_postgresql.py
```

### 執行 migrations

```bash
cd web
python manage.py migrate
```

### 標記過期契約

```bash
python mark_expired_contracts.py
```

### 清理重複資料

```bash
# 自動清理（推薦）
python cleanup_duplicate_contracts_auto.py

# 手動確認後清理
python cleanup_duplicate_contracts.py
```

## API Endpoints

### Contract API

- `GET /api/contracts/` - 列出所有契約
- `GET /api/contracts/{code}/` - 取得特定契約
- `PUT /api/contracts/{code}/` - 更新契約（使用 update_or_create）
- `DELETE /api/contracts/{code}/` - 刪除契約

### K-Contract API

- `GET /api/k-contracts/` - 列出 K 線資料
- `POST /api/k-contracts/bulk-snapshot/` - 批次記錄 K 線

## 系統需求

- Python 3.8+
- PostgreSQL 14+
- Shioaji API 憑證

## Python 套件

```
Django==5.2.5
djangorestframework
psycopg2-binary
shioaji
python-dotenv
requests
```

## 技術特點

### PostgreSQL vs SQLite

使用 PostgreSQL 的優勢：
- ✅ 真正的併發寫入支援（MVCC）
- ✅ 不會出現 database locked 錯誤
- ✅ 適合多連線高頻寫入
- ✅ 更好的查詢效能

### 原子操作

使用 Django ORM 的 `update_or_create()` 確保執行緒安全：
```python
instance, created = Contract.objects.update_or_create(
    code=code,
    defaults=validated_data
)
```

### 批次處理

K 線記錄使用批次 API，一次處理所有活躍契約：
```python
POST /api/k-contracts/bulk-snapshot/
{
    "datetime": "2025-11-27 09:00:00",
    "contract_codes": ["TX127400X5", "TX127450X5", ...]
}
```

## 常見問題

### Q: 如何切換回 SQLite？

編輯 `web/backend/settings.py`，註解 PostgreSQL 設定，取消註解 SQLite 設定。

### Q: 資料庫連線錯誤？

確認 PostgreSQL 服務正在運行：
```powershell
Get-Service postgresql*
```

### Q: 如何查看目前訂閱的契約？

執行多連線程式時會顯示訂閱摘要，或查看自動生成的 JSON 檔案。

## 授權

本專案僅供學習研究使用。

---

**最後更新**: 2025-11-27
**版本**: v3.0 - PostgreSQL 多連線版本