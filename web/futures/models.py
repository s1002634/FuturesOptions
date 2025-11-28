from django.db import models


class Contract(models.Model):
    exchange = models.CharField(max_length=20, help_text="交易所", default="TAIFEX")
    code = models.CharField(max_length=50, help_text="商品代碼", db_index=True)
    datetime = models.DateTimeField(help_text="日期")
    open = models.DecimalField(max_digits=20, decimal_places=4, help_text="開盤價")
    underlying_price = models.DecimalField(max_digits=20, decimal_places=4, help_text="標的物價格")
    bid_side_total_vol = models.IntegerField(help_text="買盤成交總量 (lot)")
    ask_side_total_vol = models.IntegerField(help_text="賣盤成交總量 (lot)")
    avg_price = models.DecimalField(max_digits=20, decimal_places=4, help_text="均價")
    close = models.DecimalField(max_digits=20, decimal_places=4, help_text="成交價")
    high = models.DecimalField(max_digits=20, decimal_places=4, help_text="最高價(自開盤)")
    low = models.DecimalField(max_digits=20, decimal_places=4, help_text="最低價(自開盤)")
    amount = models.DecimalField(max_digits=20, decimal_places=4, help_text="成交額 (NTD)")
    total_amount = models.DecimalField(max_digits=20, decimal_places=4, help_text="總成交額 (NTD)")
    volume = models.IntegerField(help_text="成交量 (lot)")
    total_volume = models.IntegerField(help_text="總成交量 (lot)")
    tick_type = models.IntegerField(help_text="內外盤別 {1: 外盤, 2: 內盤, 0: 無法判定}")
    chg_type = models.IntegerField(help_text="漲跌註記 {1: 漲停, 2: 漲, 3: 平盤, 4: 跌, 5: 跌停}")
    price_chg = models.DecimalField(max_digits=20, decimal_places=4, help_text="漲跌")
    pct_chg = models.DecimalField(max_digits=20, decimal_places=4, help_text="漲跌幅 (%)")
    simtrade = models.IntegerField(help_text="試撮")
    is_active = models.BooleanField(default=True, help_text="是否為活躍契約（正在交易中）", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, help_text="建立時間")
    updated_at = models.DateTimeField(auto_now=True, help_text="更新時間")

    def __str__(self):
        return f"{self.code} - {self.datetime}"

    class Meta:
        db_table = 'contract'
        indexes = [
            models.Index(fields=['code']),  # 按合約代碼查詢
            models.Index(fields=['-updated_at']),  # 按更新時間排序
            models.Index(fields=['code', '-updated_at']),  # 組合索引
        ]


class KContract(models.Model):
    """K線資料 - 每分鐘記錄一次"""
    exchange = models.CharField(max_length=20, help_text="交易所", default="TAIFEX")
    code = models.CharField(max_length=50, help_text="商品代碼")
    datetime = models.DateTimeField(help_text="日期", db_index=True)
    open = models.DecimalField(max_digits=20, decimal_places=4, help_text="開盤價")
    underlying_price = models.DecimalField(max_digits=20, decimal_places=4, help_text="標的物價格")
    bid_side_total_vol = models.IntegerField(help_text="買盤成交總量 (lot)")
    ask_side_total_vol = models.IntegerField(help_text="賣盤成交總量 (lot)")
    avg_price = models.DecimalField(max_digits=20, decimal_places=4, help_text="均價")
    close = models.DecimalField(max_digits=20, decimal_places=4, help_text="成交價")
    high = models.DecimalField(max_digits=20, decimal_places=4, help_text="最高價(自開盤)")
    low = models.DecimalField(max_digits=20, decimal_places=4, help_text="最低價(自開盤)")
    amount = models.DecimalField(max_digits=20, decimal_places=4, help_text="成交額 (NTD)")
    total_amount = models.DecimalField(max_digits=20, decimal_places=4, help_text="總成交額 (NTD)")
    volume = models.IntegerField(help_text="成交量 (lot)")
    total_volume = models.IntegerField(help_text="總成交量 (lot)")
    tick_type = models.IntegerField(help_text="內外盤別 {1: 外盤, 2: 內盤, 0: 無法判定}")
    chg_type = models.IntegerField(help_text="漲跌註記 {1: 漲停, 2: 漲, 3: 平盤, 4: 跌, 5: 跌停}")
    price_chg = models.DecimalField(max_digits=20, decimal_places=4, help_text="漲跌")
    pct_chg = models.DecimalField(max_digits=20, decimal_places=4, help_text="漲跌幅 (%)")
    simtrade = models.IntegerField(help_text="試撮")
    created_at = models.DateTimeField(auto_now_add=True, help_text="建立時間")

    def __str__(self):
        return f"{self.code} - {self.datetime}"

    class Meta:
        db_table = 'k_contract'
        unique_together = [['code', 'datetime']]  # 同一合約同一時間只有一筆記錄
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['code', '-datetime']),  # 按合約和時間查詢（最重要）
            models.Index(fields=['-datetime']),  # 按時間排序
            models.Index(fields=['code']),  # 按合約查詢
        ]
