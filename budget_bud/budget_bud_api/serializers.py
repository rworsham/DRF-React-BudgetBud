from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Family, Category, Budget, Transaction, Account

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FamilySerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True)

    class Meta:
        model = Family
        fields = ['id', 'name', 'members']

    def create(self, validated_data):
        members_data = validated_data.pop('members')
        family = Family.objects.create(**validated_data)
        family.members.set(members_data)
        return family

    def update(self, instance, validated_data):
        members_data = validated_data.pop('members', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        if members_data is not None:
            instance.members.set(members_data)

        return instance

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "name", "total_amount"]


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    budget = serializers.PrimaryKeyRelatedField(queryset=Budget.objects.all())

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'amount', 'transaction_type', 'description',
            'category', 'budget', 'is_recurring', 'recurring_type', 'next_occurrence'
        ]

    def validate(self, data):
        if data.get('is_recurring'):
            if not data.get('recurring_type'):
                raise serializers.ValidationError("Recurring type is required for recurring transactions.")
            if not data.get('next_occurrence'):
                raise serializers.ValidationError("Next occurrence must be set for recurring transactions.")
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        transaction = Transaction.objects.create(**validated_data)
        return transaction

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "balance", "user"]