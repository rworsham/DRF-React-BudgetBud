from unicodedata import category

from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta
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
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)


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


class TransactionBarChartViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, start_date=None, end_date=None):
        user = self.request.user
        print(f"Filtering transactions for user: {user}")
        print(f"Start date: {start_date}, End date: {end_date}")

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        print(f"Querying transactions with dates: {start_date} to {end_date}")

        queryset = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        print(f"Queryset after filtering: {queryset}")
        return queryset

    def post(self, request, *args, **kwargs):
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use 'YYYY-MM-DD'."},
                status=400
            )

        print(f"Converted Start Date: {start_date}, End Date: {end_date}")

        queryset = self.get_queryset(start_date=start_date, end_date=end_date)

        aggregated_data = (
            queryset
            .values('category__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('category__name')
        )

        print(f"Agg Data: {aggregated_data}")

        response_data = [
            {
                "category": entry['category__name'],
                "total_amount": str(entry['total_amount'])
            }
            for entry in aggregated_data
        ]

        print(f"Response Data: {response_data}")

        return Response(response_data)


class TransactionTableViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, start_date=None, end_date=None):
        user = self.request.user
        print(f"Filtering transactions for user: {user}")
        print(f"Start date: {start_date}, End date: {end_date}")

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        print(f"Querying transactions with dates: {start_date} to {end_date}")

        queryset = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        print(f"Queryset after filtering: {queryset}")
        return queryset

    def post(self, request, *args, **kwargs):
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use 'YYYY-MM_DD'."},
                status=400
            )

        print(f"Converted Start Date; {start_date}, End date: {end_date}")

        queryset = self.get_queryset(start_date=start_date, end_date=end_date)

        aggregated_data = (
            queryset
            .values('id','amount', 'budget__name', 'category__name', 'date', 'transaction_type', 'is_recurring',
                    'next_occurrence', 'description')
            .order_by('date')
        )

        print(f"Aggregated Data: {aggregated_data}")

        response_data = [
            {
                "id": entry['id'],
                "amount": entry['amount'],
                "description": entry['description'],
                "budget": entry['budget__name'],
                "category": entry['category__name'],
                "date": entry['date'],
                "transaction_type": entry['transaction_type'],
                "is_recurring": entry['is_recurring'],
                "next_occurrence": entry['next_occurrence']
            }
            for entry in aggregated_data
        ]

        print(f"Response data: {response_data}")

        return Response(response_data)


class TransactionPieChartViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, start_date=None, end_date=None):
        user = self.request.user
        print(f"Filtering transactions for user: {user}")
        print(f"Start date: {start_date}, End date: {end_date}")

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        print(f"Querying transactions with dates: {start_date} to {end_date}")

        queryset = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        print(f"Queryset after filtering: {queryset}")
        return queryset

    def post(self, request, *args, **kwargs):
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        try:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use 'YYYY-MM_DD'."},
                status=400
            )

        print(f"Converted Start Date; {start_date}, End date: {end_date}")

        queryset = self.get_queryset(start_date=start_date, end_date=end_date)

        aggregated_data = (
            queryset
            .values('category__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('category__name')
        )

        print(f"Agg Data: {aggregated_data}")

        response_data = [
            {
                "name": entry['category__name'],
                "value": entry['total_amount']
            }
            for entry in aggregated_data
        ]

        print(f"Response Data: {response_data}")

        return Response(response_data)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer