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
