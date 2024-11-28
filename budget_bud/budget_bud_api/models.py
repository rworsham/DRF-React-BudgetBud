from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Family(models.Model):
    name = models.CharField(max_length=30, default="")
    members = models.ManyToManyField(User, related_name='families')

    def __str__(self):
        return self.name


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
    is_recurring = models.BooleanField(default=False)
    recurring_type = models.CharField(max_length=10, choices=RECURRING_TYPES, blank=True, null=True)
    next_occurrence = models.DateField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')

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


class Account(models.Model):
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')

    def __str__(self):
        return self.name