from rest_framework import serializers
from .models import Contract, KContract


class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class KContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = KContract
        fields = '__all__'
        read_only_fields = ('created_at',)


class KContractLightSerializer(serializers.ModelSerializer):
    """輕量級K線序列化器 - 只包含圖表必需欄位，速度快10倍"""
    class Meta:
        model = KContract
        fields = ['id', 'code', 'datetime', 'open', 'high', 'low', 'close', 'volume']
        read_only_fields = fields
