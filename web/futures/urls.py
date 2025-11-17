from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractViewSet, KContractViewSet, dashboard, kline_chart

router = DefaultRouter()
router.register(r'contracts', ContractViewSet)
router.register(r'k-contracts', KContractViewSet)

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('kline-chart/', kline_chart, name='kline_chart'),
    path('', include(router.urls)),
]
