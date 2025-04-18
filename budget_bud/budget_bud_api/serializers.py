from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from .models import Family, Category, Budget, Transaction, Account, ReportDashboard, Report, SavingsGoal, BudgetGoal, \
    Invitation


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


class ContactSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    inquiryType = serializers.CharField(max_length=300)
    message = serializers.CharField()

    def validate(self, data):
        request = self.context.get('request')
        user = request.user if request else None

        if not user or not user.is_authenticated:
            if not data.get('email'):
                raise serializers.ValidationError("Email is required for unauthenticated users.")
        return data


class InvitedUserSignInSerializer(serializers.ModelSerializer):
    token = serializers.UUIDField(write_only=True)

    class Meta:
        model = Invitation
        fields = ['token']

    def validate_token(self, value):
        if not isinstance(value, uuid.UUID):
            raise serializers.ValidationError("Invalid token.")

        invitation = Invitation.objects.filter(token=value).first()
        if invitation:
            if self.initial_data.get('username') == User.objects.get(email=invitation.email).username:
                if invitation.expires_at < timezone.now():
                    raise serializers.ValidationError("The invitation link is expired.")
            else:
                raise serializers.ValidationError("The user does not match the invited user on the invitation.")
        else:
            raise serializers.ValidationError("The invitation token is invalid or does not exist.")
        return value

    def create(self, validated_data):
        user = User.objects.get(username=self.initial_data.get('username'))
        token = validated_data.get('token')
        invitation = Invitation.objects.get(token=token)

        family = invitation.user.families.first()
        family.members.add(user)

        invitation.delete()
        return user

class InvitedUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    token = serializers.UUIDField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'token']

    def validate_token(self, value):
        if not isinstance(value, uuid.UUID):
            raise serializers.ValidationError("Invalid token.")

        invitation = Invitation.objects.filter(token=value).first()
        if invitation:
            if self.initial_data.get('email') == invitation.email:
                if invitation.expires_at < timezone.now():
                    raise serializers.ValidationError("The invitation link is expired.")
            else:
                raise serializers.ValidationError("The provided email does not match the email on the invitation.")
        else:
            raise serializers.ValidationError("The invitation token is invalid or does not exist.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                password=validated_data['password']
            )

            token = validated_data.get('token')
            invitation = Invitation.objects.get(token=token)

            family = invitation.user.families.first()
            family.members.add(user)

            invitation.delete()
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
        fields = ["id", "name"]


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = ["id", "name", "total_amount"]


class BudgetGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetGoal
        fields = ['budget', 'target_balance', 'start_date', 'end_date']


class TransactionSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    budget = serializers.PrimaryKeyRelatedField(queryset=Budget.objects.all())
    account = serializers.PrimaryKeyRelatedField(queryset=Account.objects.all())
    next_occurrence = serializers.DateField(required=False, allow_null=True)
    family = serializers.PrimaryKeyRelatedField(queryset=Family.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'amount', 'transaction_type', 'description',
            'category', 'budget', 'account', 'is_recurring', 'recurring_type', 'next_occurrence', 'family',
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
        category = validated_data.get('category')
        budget = validated_data.get('budget')
        account = validated_data.get('account')
        family = validated_data.get('family')

        if not category:
            raise serializers.ValidationError(f"Category does not exist.")
        if not budget:
            raise serializers.ValidationError(f"Budget does not exist.")
        if not account:
            raise serializers.ValidationError(f"Account does not exist.")
        if not family:
            raise serializers.ValidationError(f"Family does not exist.")

        validated_data['family'] = family
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
        fields = ["id", "name", "balance"]

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class SavingsGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsGoal
        fields = ['account', 'target_balance', 'start_date', 'end_date']


class ReportDashboardSerializer(serializers.ModelSerializer):
    report = serializers.PrimaryKeyRelatedField(queryset=Report.objects.all())

    class Meta:
        model = ReportDashboard
        fields = ['report', 'x_size', 'y_size']

    def validate(self, data):
        if data['x_size'] not in dict(ReportDashboard.X_SIZES):
            raise serializers.ValidationError("Invalid x_size value.")
        if data['y_size'] not in dict(ReportDashboard.Y_SIZES):
            raise serializers.ValidationError("Invalid y_size value.")
        return data