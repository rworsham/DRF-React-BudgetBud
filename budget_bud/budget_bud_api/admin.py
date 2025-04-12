from django.contrib import admin
from .models import (
    Report,
    ReportDashboard,
    Family,
    Invitation,
    Category,
    Budget,
    BudgetGoal,
    Transaction,
    Account,
    BalanceHistory,
    SavingsGoal
)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')
    list_filter = ('name',)

@admin.register(ReportDashboard)
class ReportDashboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'report', 'x_size', 'y_size')
    list_filter = ('x_size', 'y_size')
    search_fields = ('user__username', 'report__name')

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_members')
    search_fields = ('name',)

    def get_members(self, obj):
        return ", ".join([member.username for member in obj.members.all()])
    get_members.short_description = 'Members'

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'token', 'created_at', 'expires_at')
    search_fields = ('email', 'user__username')
    list_filter = ('created_at', 'expires_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    search_fields = ('name', 'user__username')

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_amount', 'user')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

@admin.register(BudgetGoal)
class BudgetGoalAdmin(admin.ModelAdmin):
    list_display = ('budget', 'target_balance', 'current_balance', 'goal_met', 'start_date', 'end_date')
    search_fields = ('budget__name',)
    list_filter = ('goal_met', 'start_date', 'end_date')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'date', 'category', 'budget', 'account', 'is_recurring')
    search_fields = ('category__name', 'budget__name', 'account__name')
    list_filter = ('transaction_type', 'category', 'budget', 'is_recurring')
    list_editable = ('amount', 'is_recurring')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'balance', 'user')
    search_fields = ('name', 'user__username')
    list_filter = ('user',)

@admin.register(BalanceHistory)
class BalanceHistoryAdmin(admin.ModelAdmin):
    list_display = ('account', 'balance', 'date')
    search_fields = ('account__name',)
    list_filter = ('account', 'date')

@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ('account', 'target_balance', 'current_balance', 'goal_met', 'start_date', 'end_date')
    search_fields = ('account__name',)
    list_filter = ('goal_met', 'start_date', 'end_date')