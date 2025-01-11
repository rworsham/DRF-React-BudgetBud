from unicodedata import category

from django.core.serializers import serialize
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from .models import User, Family, Category, Budget, Transaction, Account
from .serializers import UserSerializer, UserCreateSerializer, FamilySerializer, CategorySerializer, BudgetSerializer, TransactionSerializer, \
    AccountSerializer

class UserCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'username': user.username,
                'email': user.email
            })

        return Response(serializer.errors)


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
    serializer_class = FamilySerializer

    def get_queryset(self):
        user = self.request.user
        return Family.objects.filter(members=user)


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

class BudgetTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = self.request.user
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

        transaction_queryset = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )

        budget_queryset = Budget.objects.filter(user=user)
        budgets_remaining = []

        for budget in budget_queryset:
            budget_transactions = Transaction.objects.filter(budget=budget, date__range=[start_date,
                                                                                         end_date])

            total_income = budget_transactions.filter(transaction_type='income').aggregate(Sum('amount'))[
                               'amount__sum'] or 0

            total_expense = budget_transactions.filter(transaction_type='expense').aggregate(Sum('amount'))[
                                'amount__sum'] or 0

            total_remaining = budget.total_amount - total_expense

            budgets_remaining.append({
                'budget_name': budget.name,
                'starting_budget': budget.total_amount,
                'remaining_budget': total_remaining,
                'total_income': total_income,
                'total_expense': total_expense,
            })

        transaction_serializer = TransactionSerializer(transaction_queryset, many=True)

        return Response({
            'transactions': transaction_serializer.data,
            'budgets_remaining': budgets_remaining
        })


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
        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        queryset = Transaction.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        )
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

        queryset = self.get_queryset(start_date=start_date, end_date=end_date)

        aggregated_data = (
            queryset
            .values('id', 'amount', 'budget__name', 'category__name', 'date', 'transaction_type', 'is_recurring',
                    'next_occurrence', 'description')
            .order_by('date')
        )

        if request.data.get('format') == 'pdf':
            return self.create_pdf(aggregated_data, start_date, end_date)

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

        return Response(response_data)

    def create_pdf(self, aggregated_data, start_date, end_date):
        buffer = BytesIO()

        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        margin_left = 30
        margin_top = 550
        column_width = 70
        headers = ["ID", "Amount", "Description", "Budget", "Category", "Date", "Type", "Recurring?",
                   "Next Occurrence"]

        p.setFont("Helvetica", 16)
        p.drawString(margin_left + 100, margin_top, f"Transaction Report: {start_date} to {end_date}")

        p.setFont("Helvetica", 12)
        y_position = margin_top - 30

        for index, header in enumerate(headers):
            p.drawString(margin_left + (index * column_width), y_position, header)

        y_position -= 20

        for entry in aggregated_data:
            p.drawString(margin_left, y_position, str(entry['id']))
            p.drawString(margin_left + column_width, y_position, str(entry['amount']))
            p.drawString(margin_left + 2 * column_width, y_position, entry['description'][:30])
            p.drawString(margin_left + 3 * column_width, y_position, entry['budget__name'])
            p.drawString(margin_left + 4 * column_width, y_position, entry['category__name'])
            p.drawString(margin_left + 5 * column_width, y_position, str(entry['date']))
            p.drawString(margin_left + 6 * column_width, y_position, entry['transaction_type'])
            p.drawString(margin_left + 7 * column_width, y_position, str(entry['is_recurring']))
            p.drawString(margin_left + 8 * column_width, y_position,
                         str(entry['next_occurrence']) if entry['next_occurrence'] else "N/A")

            y_position -= 20

            if y_position < 100:
                p.showPage()
                y_position = margin_top
                for index, header in enumerate(headers):
                    p.drawString(margin_left + (index * column_width), y_position, header)
                y_position -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transaction_report.pdf"'
        return response


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


class AccountViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        user = self.request.user
        return Account.objects.filter(user=user)

    def get(self, request, *args, **kwargs):
        accounts = self.get_queryset(request)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = AccountSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'name': user.name},
            status=200
            )
        return Response(serializer.errors, status=400)


class FamilyCreateViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = self.request.user

        if user.families.exists():
            return Response(
                {'detail': 'You are already a member of a family and cannot create a new one.'},
                status=400
            )

        name = request.data.get('name')
        if not name:
            return Response(
                {'detail': 'Family name is required.'},
                status=400
            )

        serializer = FamilySerializer(data=request.data)

        if serializer.is_valid():
            family = serializer.save()
            family.members.add(user)
            return Response({
                'family_name': family.name
            }, status=200)

        return Response(serializer.errors, status=400)


def generate_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.drawString(100, 750, "Hello, World! This is a dynamically generated PDF.")
    p.showPage()
    p.save()

    buffer.seek(0)

    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="generated_file.pdf"'
    return response
