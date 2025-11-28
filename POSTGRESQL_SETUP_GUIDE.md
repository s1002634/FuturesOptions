# PostgreSQL 設定指南

## 為什麼需要切換到 PostgreSQL？

SQLite 的限制：
- **單一寫入者**: SQLite 一次只能有一個寫入操作，多個連線同時寫入會造成 `database is locked` 錯誤
- **不適合併發**: 您的系統使用多個 Shioaji 連線（最多 5 個），同時發送報價更新，SQLite 無法處理

PostgreSQL 的優勢：
- **MVCC (多版本併發控制)**: 支援真正的併發寫入，多個連線可同時更新資料
- **更好的效能**: 對於大量並發寫入操作，效能遠優於 SQLite
- **企業級穩定性**: 適合處理高頻交易資料

---

## 安裝 PostgreSQL

### 方法 1: 官方安裝程式（推薦）

1. 前往下載頁面：https://www.postgresql.org/download/windows/

2. 下載 PostgreSQL 安裝程式（建議使用最新穩定版，如 PostgreSQL 16）

3. 執行安裝程式，設定以下選項：
   - **Password**: `Vv04560456`
   - **Port**: `5432`
   - **Locale**: Default locale
   - 確保勾選安裝 **pgAdmin** (圖形化管理工具)

4. 完成安裝後，PostgreSQL 服務會自動啟動

### 方法 2: 使用 Chocolatey（如果已安裝 Chocolatey）

```powershell
choco install postgresql
```

---

## 設定步驟

### 已完成的設定 ✅

1. ✅ 安裝 `psycopg2-binary` (Python PostgreSQL 驅動)
2. ✅ 修改 `web/backend/settings.py`，切換到 PostgreSQL
3. ✅ 創建 `setup_postgresql.py` 自動設定腳本

### 需要您完成的步驟

#### 步驟 1: 安裝 PostgreSQL（如果尚未安裝）
- 使用上方的「安裝 PostgreSQL」指南

#### 步驟 2: 執行自動設定腳本
```bash
cd C:\Users\samoi\Desktop\FO
python setup_postgresql.py
```

這個腳本會：
1. 檢查 PostgreSQL 是否已安裝
2. 創建 `futures_db` 資料庫
3. 執行 Django migrations 建立資料表

#### 步驟 3: 啟動系統
```bash
# 終端機 1: 啟動 Django API
cd C:\Users\samoi\Desktop\FO\web
python manage.py runserver 8111

# 終端機 2: 啟動多連線訂閱系統
cd C:\Users\samoi\Desktop\FO
python config_multi_connection.py
```

---

## 資料庫連線設定

新的 PostgreSQL 設定 (已套用在 `web/backend/settings.py`):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'futures_db',
        'USER': 'postgres',
        'PASSWORD': 'Vv04560456',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 常見問題排解

### Q1: 執行 setup_postgresql.py 時出現連線錯誤
**錯誤**: `could not connect to server`

**解決方法**:
1. 確認 PostgreSQL 服務是否正在運行
   ```powershell
   # 檢查服務狀態
   Get-Service postgresql*

   # 如果未運行，啟動服務
   Start-Service postgresql-x64-16  # 版本號可能不同
   ```

2. 確認防火牆是否允許連線到 Port 5432

### Q2: 密碼驗證失敗
**錯誤**: `password authentication failed for user "postgres"`

**解決方法**:
1. 使用 pgAdmin 重設 postgres 使用者密碼為 `Vv04560456`
2. 或修改 `web/backend/settings.py` 中的密碼設定

### Q3: 想要遷移 SQLite 的現有資料到 PostgreSQL

**解決方法**:
```bash
# 1. 從 SQLite 匯出資料
cd C:\Users\samoi\Desktop\FO\web
python manage.py dumpdata futures > backup.json

# 2. 切換到 PostgreSQL 並執行 setup_postgresql.py

# 3. 匯入資料到 PostgreSQL
python manage.py loaddata backup.json
```

### Q4: 想要切換回 SQLite

在 `web/backend/settings.py` 中：
1. 註解掉 PostgreSQL 設定
2. 取消註解 SQLite 設定
3. 重新啟動 Django

---

## 驗證設定

設定完成後，執行以下指令驗證：

```bash
cd C:\Users\samoi\Desktop\FO\web
python manage.py dbshell
```

如果成功連線到 PostgreSQL，會看到：
```
psql (16.x)
Type "help" for help.

futures_db=#
```

輸入 `\dt` 可以查看所有資料表：
```
futures_db=# \dt
              List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | contract        | table | postgres
 public | k_contract      | table | postgres
 ...
```

輸入 `\q` 離開 psql。

---

## 效能比較

### SQLite (之前)
- ❌ 多連線寫入時出現 `database is locked`
- ❌ 併發寫入效能差
- ⚠️ 需要複雜的 WAL 模式和 timeout 設定

### PostgreSQL (現在)
- ✅ 支援真正的併發寫入
- ✅ 5 個 Shioaji 連線可同時更新資料
- ✅ MVCC 確保資料一致性
- ✅ 更好的查詢效能

---

## 下一步

完成 PostgreSQL 設定後：
1. 多連線系統應該可以穩定運行，不再出現 database locked 錯誤
2. K 線記錄器可以正常每分鐘記錄活躍契約
3. 可以考慮新增資料庫索引優化查詢效能
4. 可以使用 pgAdmin 管理資料庫和查看資料

如有任何問題，請參考 PostgreSQL 官方文件：
https://www.postgresql.org/docs/
