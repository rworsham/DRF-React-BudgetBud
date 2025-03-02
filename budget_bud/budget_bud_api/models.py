from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid
from budget_bud.budget_bud_api.utils import SendEmail


class Family(models.Model):
    name = models.CharField(max_length=30)
    members = models.ManyToManyField(User, related_name='families')

    def __str__(self):
        return self.name


class Invitation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()


class Category(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name


class Budget(models.Model):
    name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')

    def __str__(self):
        return self.name


class BudgetGoal(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='budget_goals')
    target_balance = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    goal_met = models.BooleanField(default=False)
    date_set = models.DateField(default=timezone.now)
    alert_sent = models.BooleanField(default=False)

    def update_goal_progress(self, amount):
        self.current_balance += amount
        self.save()

    def check_goal_met(self):
        if self.budget.balance >= self.target_balance and not self.goal_met:
            self.goal_met = True
            self.save()
            self.send_alert()
        else:
            self.send_alert()

    def send_alert(self):
        if not self.alert_sent:
            if self.current_balance < self.target_balance:
                over_amount = self.target_balance - self.current_balance
                data = {
                    "username": self.budget.user.username,
                    "budget": self.budget.name,
                    "over_amount": over_amount
                }
                email_service = SendEmail()
                try:
                    email_service.send_mail(recipient=self.budget.user.email, message_type="BudgetGoalFailed", data=data)
                    self.alert_sent = True
                    self.save()
                except Exception as e:
                    print(f"Error sending alert: {e}")
            else:
                amount_saved = self.current_balance - self.target_balance
                data = {
                    "username": self.budget.user.username,
                    "budget": self.budget.name,
                    "amount_saved": amount_saved
                }
                email_service = SendEmail()
                try:
                    email_service.send_mail(recipient=self.budget.user.email, message_type="BudgetGoal", data=data)
                    self.alert_sent = True
                    self.save()
                except Exception as e:
                    print(f"Error sending alert: {e}")



class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    RECURRING_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('one-time', 'One-time'),
    ]

    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='transactions')
    budget = models.ForeignKey('Budget', on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='transactions')
    is_recurring = models.BooleanField(default=False)
    recurring_type = models.CharField(max_length=10, choices=RECURRING_TYPES, blank=True, null=True)
    next_occurrence = models.DateField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)

    def __str__(self):
        return f"{self.transaction_type.title()} - {self.amount}"

    def save(self, *args, **kwargs):
        if self.is_recurring and self.next_occurrence is None:
            if self.recurring_type == 'daily':
                self.next_occurrence = self.date + timezone.timedelta(days=1)
            elif self.recurring_type == 'weekly':
                self.next_occurrence = self.date + timezone.timedelta(weeks=1)
            elif self.recurring_type == 'monthly':
                self.next_occurrence = self.date + timezone.relativedelta.relativedelta(months=1)
            elif self.recurring_type == 'yearly':
                self.next_occurrence = self.date + timezone.relativedelta.relativedelta(years=1)
            else:
                self.next_occurrence = None
        super().save(*args, **kwargs)

        account = self.account
        if self.transaction_type == 'income':
            new_balance = account.balance + self.amount
        elif self.transaction_type == 'expense':
            new_balance = account.balance - self.amount
        else:
            raise ValueError("Invalid transaction type.")

        BalanceHistory.objects.create(account=account, balance=new_balance, date=self.date)

        account.balance = new_balance
        account.save()

        savings_goals = account.savings_goals.all()
        if savings_goals.exists():
            for goal in savings_goals:
                goal.current_balance = account.balance
                goal.save()

        budget = self.budget
        budget_goals = budget.budget_goals.all()
        if budget_goals.exists():
            for goal in budget_goals:
                if goal.budget == budget:
                    if self.transaction_type == 'income':
                        goal.update_goal_progress(Decimal(self.amount))
                        goal.save()
                    elif self.transaction_type == 'expense':
                        goal.update_goal_progress(-Decimal(self.amount))
                        goal.save()


class Account(models.Model):
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_balance_at_date(self, date):
        try:
            balance_history = self.balancehistory_set.filter(date__lte=date).latest('date')
            return balance_history.balance
        except BalanceHistory.DoesNotExist:
            return self.balance


class BalanceHistory(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balance_history')
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f'{self.account.name} - {self.balance} on {self.date}'

    class Meta:
        ordering = ['date']


class SavingsGoal(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='savings_goals')
    target_balance = models.DecimalField(max_digits=10, decimal_places=2)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    goal_met = models.BooleanField(default=False)
    date_set = models.DateField(default=timezone.now)
    alert_sent = models.BooleanField(default=False)

    def check_goal_met(self):
        if self.account.balance >= self.target_balance and not self.goal_met:
            self.goal_met = True
            self.save()
            self.send_alert()
        else:
            self.send_alert()

    def send_alert(self):
        if not self.alert_sent:
            if self.current_balance < self.target_balance:
                over_amount = self.target_balance - self.current_balance
                data = {
                    "username": self.account.user.username,
                    "account": self.account.name,
                    "over_amount": over_amount
                }
                email_service = SendEmail()
                try:
                    email_service.send_mail(recipient=self.account.user.email, message_type="SavingsGoalFailed", data=data)
                    self.alert_sent = True
                    self.save()
                except Exception as e:
                    print(f"Error sending alert: {e}")
            else:
                amount_saved = self.current_balance - self.target_balance
                data = {
                    "username": self.account.user.username,
                    "account": self.account.name,
                    "amount_saved": amount_saved
                }
                email_service = SendEmail()
                try:
                    email_service.send_mail(recipient=self.account.user.email, message_type="SavingsGoal", data=data)
                    self.alert_sent = True
                    self.save()
                except Exception as e:
                    print(f"Error sending alert: {e}")

class Report(models.Model):
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ReportDashboard(models.Model):
    X_SIZES = [
        ('33', 'small'),
        ('66', 'medium'),
        ('100', 'large'),
    ]

    Y_SIZES = [
        ('33', 'small'),
        ('66', 'medium'),
        ('100', 'large'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='report_dashboards')
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='dashboards')
    x_size = models.CharField(max_length=6, choices=X_SIZES)
    y_size = models.CharField(max_length=6, choices=Y_SIZES)