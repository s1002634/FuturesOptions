from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Contract, KContract
from .serializers import ContractSerializer, KContractSerializer


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
