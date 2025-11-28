from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import Contract, KContract
from .serializers import ContractSerializer, KContractSerializer, KContractLightSerializer
from datetime import datetime, timedelta


class StandardResultsSetPagination(PageNumberPagination):
    """標準分頁設定"""
    page_size = 100  # 每頁100筆
    page_size_query_param = 'page_size'
    max_page_size = 1000  # 最多1000筆


def dashboard(request):
    """即時期貨報價看板"""
    return render(request, 'futures/dashboard.html')


def kline_chart(request):
    """K線圖表頁面"""
    return render(request, 'futures/kline_chart.html')


class ContractViewSet(viewsets.ModelViewSet):
    """期貨合約 ViewSet - 優化查詢效能"""
    queryset = Contract.objects.all().order_by('-updated_at')
    serializer_class = ContractSerializer
    permission_classes = [AllowAny]
    lookup_field = 'code'  # 使用 code 而不是 id 作為查找欄位

    def get_queryset(self):
        """
        支援查詢參數:
        - code: 合約代碼
        - limit: 限制筆數 (預設20, 最多200)
        - codes: 多個合約代碼 (逗號分隔)
        """
        queryset = Contract.objects.all().order_by('-updated_at')

        # 按 code 過濾
        code = self.request.query_params.get('code', None)
        if code:
            queryset = queryset.filter(code=code)

        # 按多個 codes 過濾
        codes = self.request.query_params.get('codes', None)
        if codes:
            code_list = [c.strip() for c in codes.split(',')]
            queryset = queryset.filter(code__in=code_list)

        # 限制筆數
        limit = self.request.query_params.get('limit', None)
        if limit:
            try:
                limit_num = min(int(limit), 200)  # 最多200筆
                queryset = queryset[:limit_num]
            except (ValueError, TypeError):
                queryset = queryset[:20]  # 預設20筆
        else:
            queryset = queryset[:20]  # 預設20筆

        # 優化查詢 - 只載入必要欄位
        queryset = queryset.only(
            'id', 'code', 'exchange', 'datetime', 'open', 'high', 'low', 'close',
            'volume', 'total_volume', 'price_chg', 'pct_chg', 'chg_type',
            'underlying_price', 'bid_side_total_vol', 'ask_side_total_vol',
            'avg_price', 'amount', 'total_amount', 'tick_type', 'simtrade',
            'updated_at'
        )

        return queryset

    def update(self, request, *args, **kwargs):
        """
        支援 update_or_create 邏輯（線程安全）
        如果 code 存在則更新，不存在則建立
        使用 update_or_create 避免競爭條件
        """
        code = kwargs.get('code')

        # 驗證資料
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # 使用 update_or_create 原子操作（線程安全）
        instance, created = Contract.objects.update_or_create(
            code=code,
            defaults=validated_data
        )

        # 返回結果
        output_serializer = self.get_serializer(instance)
        if created:
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(output_serializer.data, status=status.HTTP_200_OK)


class KContractViewSet(viewsets.ModelViewSet):
    """K線資料 ViewSet - 優化大量資料查詢"""
    queryset = KContract.objects.all()
    serializer_class = KContractSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        支援多種查詢參數:
        - code: 合約代碼
        - limit: 限制筆數 (預設100, 最多1000)
        - hours: 最近N小時的資料
        - start_date: 開始時間 (YYYY-MM-DD HH:MM:SS)
        - end_date: 結束時間 (YYYY-MM-DD HH:MM:SS)
        - codes_only: 只取得合約代碼列表 (值為true時，不返回完整資料)
        """
        code = self.request.query_params.get('code', None)
        hours = self.request.query_params.get('hours', None)

        # 優化策略：沒有指定code且要查詢時間範圍時，直接限制筆數避免全表掃描
        if not code and hours:
            # 先限制筆數再過濾，避免掃描全表
            limit = self.request.query_params.get('limit', None)
            try:
                # 放寬限制：最多50000筆（支援查詢1個月資料）
                limit_num = min(int(limit), 50000) if limit else 1000
            except (ValueError, TypeError):
                limit_num = 1000

            # 計算時間範圍
            try:
                hours_ago = timezone.now() - timedelta(hours=int(hours))
                # 使用索引優化的查詢：先按時間過濾，再限制筆數
                queryset = KContract.objects.filter(
                    datetime__gte=hours_ago
                ).order_by('-datetime')[:limit_num]
            except (ValueError, TypeError):
                queryset = KContract.objects.all().order_by('-datetime')[:limit_num]

            # 只返回必要欄位
            return queryset.only('id', 'code', 'datetime', 'close')

        # 一般查詢流程
        queryset = KContract.objects.all().order_by('-datetime')

        # 按 code 過濾（最重要的過濾條件，應該優先）
        if code:
            queryset = queryset.filter(code=code)

        # 時間範圍過濾 - 最近N小時
        if hours:
            try:
                hours_ago = timezone.now() - timedelta(hours=int(hours))
                queryset = queryset.filter(datetime__gte=hours_ago)
            except (ValueError, TypeError):
                pass

        # 自訂時間範圍
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date:
            try:
                start_dt = timezone.make_aware(datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S"))
                queryset = queryset.filter(datetime__gte=start_dt)
            except (ValueError, TypeError):
                pass

        if end_date:
            try:
                end_dt = timezone.make_aware(datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"))
                queryset = queryset.filter(datetime__lte=end_dt)
            except (ValueError, TypeError):
                pass

        # 限制筆數 (不使用分頁時)
        limit = self.request.query_params.get('limit', None)
        if limit and not self.request.query_params.get('page'):
            try:
                # 放寬限制：最多50000筆（約1個月的分鐘資料）
                limit_num = min(int(limit), 50000)
                queryset = queryset[:limit_num]
            except (ValueError, TypeError):
                queryset = queryset[:100]  # 預設100筆

        # 使用 only 優化查詢 - 根據是否有code決定返回欄位
        if code:
            # 有指定code時返回完整資料
            queryset = queryset.only(
                'id', 'code', 'datetime', 'open', 'high', 'low', 'close',
                'volume', 'total_volume', 'underlying_price'
            )
        else:
            # 沒指定code時只返回基本欄位
            queryset = queryset.only('id', 'code', 'datetime', 'close')

        return queryset

    def get_serializer_class(self):
        """根據查詢參數選擇序列化器"""
        # 如果有指定code且要查詢圖表資料，使用輕量級序列化器
        if self.request.query_params.get('code') and self.request.query_params.get('no_page') == 'true':
            return KContractLightSerializer
        return KContractSerializer

    def list(self, request, *args, **kwargs):
        """重載 list 方法，支援無分頁模式 + 超高速模式"""
        # 如果有 no_page 參數，則不分頁
        if request.query_params.get('no_page') == 'true':
            code = request.query_params.get('code')

            # 超高速模式：有指定code時，直接用values()返回字典，跳過序列化器
            if code and request.query_params.get('fast') == 'true':
                queryset = self.filter_queryset(self.get_queryset())
                # 直接返回字典列表，不經過序列化器（快5-10倍）
                data = list(queryset.values('id', 'code', 'datetime', 'open', 'high', 'low', 'close', 'volume'))
                return Response(data)

            # 一般模式：使用序列化器
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='contract-codes')
    def contract_codes(self, request):
        """
        快速獲取所有活躍的合約代碼
        用於下拉選單等場景，不需要完整資料

        查詢參數:
        - hours: 最近N小時有資料的合約 (預設1小時)
        - limit: 最多返回多少個合約代碼 (預設200)

        返回格式: ["TX427150K5", "TX428600W5", ...]
        """
        hours = request.query_params.get('hours', '1')
        limit = request.query_params.get('limit', '200')

        try:
            hours_ago = timezone.now() - timedelta(hours=int(hours))
            limit_num = min(int(limit), 500)  # 最多500個

            # 優化策略：使用原生SQL或ORM的高效查詢
            # 方法1：先取最新的N筆記錄，再去重（更快）
            recent_records = KContract.objects.filter(
                datetime__gte=hours_ago
            ).order_by('-datetime').values('code')[:limit_num * 5]  # 取5倍數量確保有足夠的不同code

            # Python端去重（比資料庫distinct快）
            seen = set()
            codes = []
            for record in recent_records:
                code = record['code']
                if code not in seen:
                    seen.add(code)
                    codes.append(code)
                    if len(codes) >= limit_num:
                        break

            return Response(sorted(codes))
        except (ValueError, TypeError) as e:
            return Response([], status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-snapshot')
    def bulk_snapshot(self, request):
        """
        批次建立 K 線快照 - 從所有 Contract 取得最新資料並批次建立 KContract

        請求格式:
        POST /api/k-contracts/bulk-snapshot/
        {
            "datetime": "2025-11-17 16:45:00",  # 可選,不提供則使用當前時間
            "contract_codes": ["TX127150K5", "TX127200K5", ...]  # 可選,只記錄指定的契約代碼
        }

        回應:
        {
            "success": true,
            "created_count": 100,
            "datetime": "2025-11-17 16:45:00",
            "elapsed_ms": 45.23
        }
        """
        import time
        start_time = time.time()

        # 取得時間參數 (如果沒提供則使用當前時間)
        snapshot_datetime_str = request.data.get('datetime')
        if not snapshot_datetime_str:
            # 當前時間取整到分鐘
            now = timezone.now()
            snapshot_datetime_str = now.strftime("%Y-%m-%d %H:%M:00")

        # 將字串轉換為時區感知的 datetime 物件
        snapshot_datetime = timezone.make_aware(
            datetime.strptime(snapshot_datetime_str, "%Y-%m-%d %H:%M:%S")
        )

        # 取得契約代碼過濾列表 (可選)
        contract_codes = request.data.get('contract_codes')

        # 取得 Contract 的最新資料 (只取活躍契約)
        if contract_codes:
            # 只取得指定的活躍契約
            contracts = Contract.objects.filter(code__in=contract_codes, is_active=True)
        else:
            # 只取得所有活躍契約 (預設行為)
            contracts = Contract.objects.filter(is_active=True)

        if not contracts.exists():
            return Response({
                'success': False,
                'error': '沒有找到任何 Contract 資料',
                'created_count': 0
            }, status=status.HTTP_400_BAD_REQUEST)

        # 準備批次建立的 KContract 物件列表
        k_contracts = []
        for contract in contracts:
            k_contracts.append(KContract(
                exchange=contract.exchange,
                code=contract.code,
                datetime=snapshot_datetime,
                open=contract.open,
                underlying_price=contract.underlying_price,
                bid_side_total_vol=contract.bid_side_total_vol,
                ask_side_total_vol=contract.ask_side_total_vol,
                avg_price=contract.avg_price,
                close=contract.close,
                high=contract.high,
                low=contract.low,
                amount=contract.amount,
                total_amount=contract.total_amount,
                volume=contract.volume,
                total_volume=contract.total_volume,
                tick_type=contract.tick_type,
                chg_type=contract.chg_type,
                price_chg=contract.price_chg,
                pct_chg=contract.pct_chg,
                simtrade=contract.simtrade,
            ))

        # 批次建立 (ignore_conflicts=True 避免重複建立)
        created_objects = KContract.objects.bulk_create(
            k_contracts,
            ignore_conflicts=True  # 如果 (code, datetime) 已存在則跳過
        )

        elapsed_time = (time.time() - start_time) * 1000  # 轉換為毫秒

        return Response({
            'success': True,
            'created_count': len(created_objects),
            'total_contracts': contracts.count(),
            'datetime': snapshot_datetime_str,
            'elapsed_ms': round(elapsed_time, 2)
        }, status=status.HTTP_201_CREATED)
