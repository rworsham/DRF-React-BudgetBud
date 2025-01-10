from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Family, Category, Budget, Transaction, Account


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class FamilySerializer(serializers.ModelSerializer):

    class Meta:
        model = Family
        fields = ['id', 'name']

    def create(self, validated_data):
        family = Family.objects.create(**validated_data)
        return family


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "name", "total_amount"]


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    budget = serializers.CharField(source='budget.name')
    next_occurrence = serializers.DateField(required=False, allow_null=True)

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
        else:
            if 'next_occurrence' in data and data['next_occurrence'] is not None:
                raise serializers.ValidationError(
                    "Next occurrence should not be provided for non-recurring transactions.")
            data.pop('next_occurrence', None)
        return data

    def create(self, validated_data):
        user = self.context['request'].user

        category_name = validated_data.get('category')
        budget_name = validated_data.get('budget')

        category = Category.objects.filter(user=user, name=category_name['name']).first()
        budget = Budget.objects.filter(user=user, name=budget_name['name']).first()

        if not category:
            raise serializers.ValidationError(f"Category '{category_name}' does not exist.")
        if not budget:
            raise serializers.ValidationError(f"Budget '{budget_name}' does not exist.")

        validated_data['category'] = category
        validated_data['budget'] = budget
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