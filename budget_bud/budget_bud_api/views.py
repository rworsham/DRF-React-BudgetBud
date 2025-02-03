from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from .models import User, Family, Category, Budget, Transaction, Account, BalanceHistory, ReportDashboard, Report, \
    SavingsGoal
from .serializers import UserSerializer, UserCreateSerializer, FamilySerializer, CategorySerializer, BudgetSerializer, \
    TransactionSerializer, \
    AccountSerializer, ReportDashboardSerializer, SavingsGoalSerializer


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


class UserReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user

        try:
            dashboards = ReportDashboard.objects.filter(user=user).select_related('report')
            if not dashboards.exists():
                return Response(
                    {"detail": "No reports found for this user."},
                    status=200
                )

            reports = []
            for dashboard in dashboards:
                reports.append({
                    'id': dashboard.id,
                    'display_name': dashboard.report.display_name,
                    'x_size': dashboard.x_size,
                    'y_size': dashboard.y_size,
                })

            return Response(reports, status=200)

        except Exception as e:
            return Response(status=400)

    def post(self, request, *args, **kwargs):
        user = self.request.user
        serializer = ReportDashboardSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(
                user=user)

            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    def patch(self, request, *args, **kwargs):
        user = self.request.user
        report_id = request.data.get("report_id")

        try:
            print(report_id)
            print(user)
            dashboard = ReportDashboard.objects.get(id=report_id, user=user)
            print(dashboard)
        except ReportDashboard.DoesNotExist:
            raise NotFound({"detail": "Report dashboard not found or not owned by the user."})

        serializer = ReportDashboardSerializer(dashboard, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)



class ReportChoices(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = Report.objects.all().values('id', 'display_name')
        return Response(reports)


class FamilyView(generics.ListAPIView):
    serializer_class = FamilySerializer

    def get_queryset(self):
        user = self.request.user
        return Family.objects.filter(members=user)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user

        transaction_count = Transaction.objects.filter(user=user).count()
        net_balance = Transaction.objects.filter(user=user).aggregate(Sum('amount'))['amount__sum']
        goal_met_count = SavingsGoal.objects.filter(account__user=user, goal_met=True).count()

        response_data = {
            'total_transactions': transaction_count,
            'savings_goals_met': goal_met_count,
            'net_balance': net_balance,
        }

        return Response(response_data)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
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

    def create(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        account_id = data.get('account')
        if not account_id:
            return Response({"error": "Account is required."}, status=400)

        account = Account.objects.filter(id=account_id, user=user).first()
        if not account:
            return Response({"error": "Account does not exist or does not belong to the user."},
                            status=400)

        category_id = data.get('category')
        budget_id = data.get('budget')

        category = Category.objects.filter(user=user, id=category_id).first()
        budget = Budget.objects.filter(user=user, id=budget_id).first()

        if not category:
            return Response({"error": f"Category '{category_id}' does not exist."},
                            status=400)
        if not budget:
            return Response({"error": f"Budget '{budget_id}' does not exist."}, status=400)

        data['category'] = category.id
        data['budget'] = budget.id
        data['user'] = user

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=200)

        return Response(serializer.errors, status=400)

    def destroy(self, request, *args, **kwargs):
        user = self.request.user
        transaction_id = kwargs.get('pk')

        try:
            transaction = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found."}, status=404)

        if transaction.user != user:
            return Response({"error": "You do not have permission to delete this transaction."}, status=403)

        transaction.delete()
        return Response(status=204)


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
            .values('id', 'amount', 'budget__name', 'category__name', 'account__name', 'date', 'transaction_type', 'is_recurring',
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
                "account": entry['account__name'],
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
        serializer = AccountSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'name': user.name},
            status=200
            )
        return Response(serializer.errors, status=400)


class AccountsOverviewReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        today = datetime.today().date()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        accounts = Account.objects.filter(user=request.user)

        date_balances = defaultdict(lambda: {account.name: None for account in accounts})

        balance_histories = BalanceHistory.objects.filter(
            account__in=accounts,
            date__gte=first_day_of_month,
            date__lte=last_day_of_month
        )

        for history in balance_histories:
            date_balances[history.date][history.account.name] = history.balance

        previous_balances = {account.name: None for account in accounts}

        data = []
        for single_date in self._get_dates_in_month(first_day_of_month, last_day_of_month):
            formatted_entry = {
                'name': single_date.strftime('%Y-%m-%d'),
            }

            for account in accounts:
                balance = date_balances[single_date].get(account.name, None)

                if balance is None and previous_balances.get(account.name) is not None:
                    balance = previous_balances[account.name]

                formatted_entry[account.name] = balance

                if balance is not None:
                    previous_balances[account.name] = balance

            data.append(formatted_entry)

        return Response(data)

    def _get_dates_in_month(self, start_date, end_date):
        current_date = start_date
        while current_date <= end_date:
            yield current_date
            current_date += timedelta(days=1)


class AccountHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, start_date=None, end_date=None, account_id=None):
        user = self.request.user
        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        if not account_id:
            raise ValueError("Account ID is required.")

        queryset = Transaction.objects.filter(
            user=user,
            account_id=account_id,
            date__gte=start_date,
            date__lte=end_date
        )
        return queryset

    def post(self, request, *args, **kwargs):
        print(request.data)
        account_id = request.data.get('account_id')
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)

        if not account_id:
            return Response(
                {"detail": "Account ID required"},
                status=400
            )

        if not start_date or not end_date:
            current_date = datetime.today()
            start_date = current_date.replace(day=1).date()
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = (next_month - timedelta(days=1)).date()

        queryset = self.get_queryset(start_date=start_date, end_date=end_date, account_id=account_id)

        aggregated_data = (
            queryset
            .values('id', 'amount', 'budget__name', 'category__name', 'date', 'transaction_type', 'description')
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
        headers = ["ID", "Amount", "Description", "Budget", "Category", "Date", "Type"]

        p.setFont("Helvetica", 16)
        p.drawString(margin_left + 100, margin_top, f"Account History Report: {start_date} to {end_date}")

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
        response['Content-Disposition'] = 'attachment; filename="account_history_report.pdf"'
        return response


class SavingsGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = self.request.user

        serializer = SavingsGoalSerializer(data=request.data)

        if serializer.is_valid():
            account = Account.objects.filter(id=request.data['account'], user=user).first()
            if not account:
                return Response({"detail": "Account not found or you do not have permission to access this account."},
                                status=400)

            savings_goal = serializer.save(account=account)
            return Response(SavingsGoalSerializer(savings_goal).data, status=200)

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

