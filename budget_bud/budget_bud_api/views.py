from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .models import User, Family, Category, Budget, Transaction, Account
from .serializers import UserSerializer, FamilySerializer, CategorySerializer, BudgetSerializer, TransactionSerializer, \
    AccountSerializer


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        return self.request.user


class FamilyView(generics.ListAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        user = self.request.user
        return Budget.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class AllTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        total_income = queryset.filter(transaction_type='income').aggregate(total_income=Sum('amount'))[
                           'total_income'] or 0

        total_expenses = queryset.filter(transaction_type='expense').aggregate(total_expenses=Sum('amount'))[
                             'total_expenses'] or 0

        net_income = total_income - total_expenses

        transactions = TransactionSerializer(queryset, many=True).data

        response_data = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'transactions': transactions
        }

        return Response(response_data)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer