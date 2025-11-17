from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Contract, KContract
from .serializers import ContractSerializer, KContractSerializer
from datetime import datetime


def dashboard(request):
    """即時期貨報價看板"""
    return render(request, 'futures/dashboard.html')


def kline_chart(request):
    """K線圖表頁面"""
    return render(request, 'futures/kline_chart.html')


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all().order_by('-updated_at')
    serializer_class = ContractSerializer
    permission_classes = [AllowAny]
    lookup_field = 'code'  # 使用 code 而不是 id 作為查找欄位

    def update(self, request, *args, **kwargs):
        """
        支援 update_or_create 邏輯
        如果 code 存在則更新，不存在則建立
        """
        code = kwargs.get('code')

        # 嘗試取得現有資料
        try:
            instance = Contract.objects.get(code=code)
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Contract.DoesNotExist:
            # 不存在則建立新的
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class KContractViewSet(viewsets.ModelViewSet):
    """K線資料 ViewSet"""
    queryset = KContract.objects.all()
    serializer_class = KContractSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """支援按 code 過濾"""
        queryset = KContract.objects.all().order_by('-datetime')
        code = self.request.query_params.get('code', None)
        if code:
            queryset = queryset.filter(code=code)
        return queryset

    @action(detail=False, methods=['post'], url_path='bulk-snapshot')
    def bulk_snapshot(self, request):
        """
        批次建立 K 線快照 - 從所有 Contract 取得最新資料並批次建立 KContract

        請求格式:
        POST /api/k-contracts/bulk-snapshot/
        {
            "datetime": "2025-11-17 16:45:00"  # 可選,不提供則使用當前時間
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

        # 取得所有 Contract 的最新資料
        contracts = Contract.objects.all()

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
