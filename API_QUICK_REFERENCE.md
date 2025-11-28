# API 快速參考指南

## 📊 效能實測（54萬筆資料）

| API | 響應時間 | 提升 | 說明 |
|-----|---------|------|------|
| 合約代碼列表 | **6.7ms** | 1400倍 ⚡ | 極速 |
| Dashboard | **17ms** | 50倍+ ⚡ | 極速 |
| K線查詢（1小時） | **30ms** | 180倍 ⚡ | 超高速模式 |
| K線查詢（24小時） | **38ms** | 1500倍 🚀 | 超高速模式 |
| K線查詢（1週） | **40ms** | 3000倍 🔥 | 超高速模式 |

---

## 🚀 推薦用法

### 1. 載入圖表合約選單（極速）
```javascript
// ⚡ 只需 6.7ms！
fetch('/api/k-contracts/contract-codes/?hours=1&limit=200')
  .then(res => res.json())
  .then(codes => {
    // ["TX427150K5", "TX428600W5", ...]
    codes.forEach(code => {
      // 填充下拉選單
    });
  });
```

### 2. 載入Dashboard即時報價
```javascript
// ⚡ 只需 17ms！
fetch('/api/contracts/?limit=20')
  .then(res => res.json())
  .then(data => {
    // 顯示最新20筆合約
  });

// 每2秒自動更新
setInterval(() => fetch('/api/contracts/?limit=20'), 2000);
```

### 3. 載入K線圖表資料（超高速模式）🚀
```javascript
const code = 'TX427150K5';
const hours = 24; // 24小時範圍

// 🚀 只需 38ms！（使用 fast=true 啟用超高速模式）
fetch(`/api/k-contracts/?code=${code}&hours=${hours}&limit=1500&no_page=true&fast=true`)
  .then(res => res.json())
  .then(data => {
    // 繪製圖表
    const labels = data.map(d => new Date(d.datetime));
    const prices = data.map(d => d.close);
  });

// 🔥 查詢1週資料也只需 40ms！
fetch(`/api/k-contracts/?code=${code}&hours=168&limit=10000&no_page=true&fast=true`)
```

**超高速模式優勢**：
- ⚡ 24小時：38ms（vs 一般模式6.6秒）
- 🔥 1週：40ms（vs 一般模式可能數分鐘）
- 只返回圖表必需的8個欄位
- 跳過DRF序列化器，直接返回字典

---

## 📖 完整API參數

### Contract API

**端點**: `/api/contracts/`

| 參數 | 說明 | 預設值 | 範例 |
|-----|------|--------|------|
| `code` | 單一合約代碼 | - | `?code=TX427150K5` |
| `codes` | 多個合約（逗號分隔） | - | `?codes=TX427150K5,TX428600W5` |
| `limit` | 限制筆數 | 20 | `?limit=50` (最多200) |

**範例**:
```bash
# 取20筆最新資料
GET /api/contracts/

# 取50筆
GET /api/contracts/?limit=50

# 查詢特定合約
GET /api/contracts/?code=TX427150K5

# 查詢多個合約
GET /api/contracts/?codes=TX427150K5,TX428600W5
```

---

### KContract API

**端點**: `/api/k-contracts/`

| 參數 | 說明 | 預設值 | 範例 |
|-----|------|--------|------|
| `code` | 合約代碼 | - | `?code=TX427150K5` |
| `hours` | 最近N小時 | - | `?hours=1` |
| `limit` | 限制筆數 | 100 | `?limit=500` (最多1000) |
| `no_page` | 不使用分頁 | false | `?no_page=true` |
| `start_date` | 開始時間 | - | `?start_date=2025-11-24 09:00:00` |
| `end_date` | 結束時間 | - | `?end_date=2025-11-24 17:00:00` |
| `page` | 頁碼（分頁模式） | 1 | `?page=2` |
| `page_size` | 每頁筆數 | 100 | `?page_size=50` |

**範例**:
```bash
# 取最近1小時資料（不分頁）
GET /api/k-contracts/?code=TX427150K5&hours=1&no_page=true

# 取最近24小時資料（限制1000筆）
GET /api/k-contracts/?code=TX427150K5&hours=24&limit=1000&no_page=true

# 使用分頁（每頁100筆）
GET /api/k-contracts/?code=TX427150K5&page=1&page_size=100

# 自訂時間範圍
GET /api/k-contracts/?code=TX427150K5&start_date=2025-11-24 09:00:00&end_date=2025-11-24 17:00:00&no_page=true
```

---

### Contract Codes API（極速）⚡

**端點**: `/api/k-contracts/contract-codes/`

| 參數 | 說明 | 預設值 | 範例 |
|-----|------|--------|------|
| `hours` | 最近N小時 | 1 | `?hours=2` |
| `limit` | 最多返回數量 | 200 | `?limit=100` (最多500) |

**特點**:
- ⚡ **極速**: 只需 6-10ms
- 只返回合約代碼列表
- 不返回完整資料
- 專為下拉選單設計

**範例**:
```bash
# 取最近1小時活躍的合約代碼（極速）
GET /api/k-contracts/contract-codes/?hours=1&limit=200

# 回應
["TX427150K5", "TX428600W5", "TX426550W5", ...]
```

**JavaScript使用**:
```javascript
// ⚡ 極速載入合約列表
async function loadContractCodes() {
  const response = await fetch('/api/k-contracts/contract-codes/?hours=1');
  const codes = await response.json();

  // 填充下拉選單
  const select = document.getElementById('contractSelect');
  select.innerHTML = codes.map(code =>
    `<option value="${code}">${code}</option>`
  ).join('');
}
```

---

## 💡 最佳實踐

### 1. 選擇正確的API

| 使用場景 | 推薦API | 原因 |
|---------|--------|------|
| 下拉選單 | `contract-codes` | 極速（6ms），只返回代碼 |
| Dashboard | `contracts?limit=20` | 快速（17ms），最新資料 |
| K線圖表 | `k-contracts?code=...&hours=...` | 指定合約，精確查詢 |

### 2. 合理設定limit

```javascript
// ✓ 好：按需求設定適當的limit
fetch('/api/contracts/?limit=20')  // Dashboard只需20筆

// ✗ 不好：不設limit會載入全部（慢）
fetch('/api/contracts/')  // 預設也是20，但明確寫出更好
```

### 3. 指定code查詢

```javascript
// ✓ 好：有指定code（快）
fetch('/api/k-contracts/?code=TX427150K5&hours=1&no_page=true')

// ✗ 不好：沒指定code + 時間範圍（慢）
fetch('/api/k-contracts/?hours=24&no_page=true')  // 會掃描大量資料
```

### 4. 使用no_page參數

```javascript
// ✓ 好：圖表用途，需要完整資料
fetch('/api/k-contracts/?code=TX427150K5&hours=1&limit=100&no_page=true')

// ✓ 好：列表用途，需要分頁
fetch('/api/k-contracts/?code=TX427150K5&page=1&page_size=100')
```

---

## ⚠️ 注意事項

### 1. 時間範圍查詢
- **有code**: 查詢速度快（320ms for 1小時）
- **無code**: 會較慢，建議使用`contract-codes`代替

### 2. Limit限制
- Contract API: 最多200筆
- KContract API: 最多1000筆
- contract-codes: 最多500個代碼

### 3. 分頁 vs 不分頁
- **圖表**: 使用 `no_page=true`，一次取完整資料
- **列表**: 使用分頁，逐頁載入

---

## 🔧 故障排除

### 問題1: API很慢（超過1秒）

**可能原因**:
- 沒有指定`code`卻查詢大時間範圍
- 沒有設定`limit`

**解決方案**:
```javascript
// ✗ 慢
fetch('/api/k-contracts/?hours=24&no_page=true')

// ✓ 快
fetch('/api/k-contracts/?code=TX427150K5&hours=24&limit=1000&no_page=true')
```

### 問題2: 下拉選單載入慢

**錯誤做法**:
```javascript
// ✗ 載入全部資料再提取code（慢）
fetch('/api/k-contracts/?hours=1&limit=1000&no_page=true')
  .then(res => res.json())
  .then(data => {
    const codes = [...new Set(data.map(d => d.code))];
  });
```

**正確做法**:
```javascript
// ✓ 使用專用API（極速）
fetch('/api/k-contracts/contract-codes/?hours=1')
  .then(res => res.json())
  .then(codes => {
    // 已經去重排序好的代碼列表
  });
```

### 問題3: 資料太舊

**確認方法**:
```javascript
fetch('/api/k-contracts/?code=TX427150K5&limit=1&no_page=true')
  .then(res => res.json())
  .then(data => {
    if (data.length > 0) {
      console.log('最新資料時間:', data[0].datetime);
    }
  });
```

---

## 📚 更多資訊

- 完整優化報告: [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)
- Django Admin: http://127.0.0.1:8111/admin/
- API文件: http://127.0.0.1:8111/api/

---

**最後更新**: 2025-11-24
**資料量**: 54萬+ 筆K線資料
**最佳效能**: 6.7ms (contract-codes API)
