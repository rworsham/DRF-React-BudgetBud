from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserListCreateView, UserCreateView, UserRetrieveUpdateDestroyView, FamilyView, CategoryViewSet, \
    BudgetViewSet, \
    TransactionViewSet, AccountViewSet, AllTransactionViewSet, TransactionBarChartViewSet, TransactionTableViewSet, \
    TransactionPieChartViewSet, BudgetTransactionView, FamilyCreateViewSet, AccountsOverviewReportView, UserReportsView, \
    ReportChoices, AccountHistory, SavingsGoalView, ProfileView, BudgetGoalView, BudgetHistoryView, \
    FamilyAddMemberViewSet, LoginView, FamilyOverviewView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename="category")
router.register(r'budget', BudgetViewSet, basename="budget")
router.register(r'transaction', TransactionViewSet, basename='transaction')
router.register(r'transactions', AllTransactionViewSet, basename='all_transactions')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/users/', UserListCreateView.as_view(), name='user-list-create'),
    path('api/user/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('api/user/reports/', UserReportsView.as_view(), name='user-reports'),
    path('api/user/dashboard-report-options/', ReportChoices.as_view(), name='dashboard-report-options'),
    path('api/accounts/', AccountViewSet.as_view(), name='accounts'),
    path('api/accounts/overview-report/', AccountsOverviewReportView.as_view(), name='accounts-overview-report'),
    path('api/profile/stats/', ProfileView.as_view(), name='profile-stats'),
    path('api/account/history/', AccountHistory.as_view(), name='account-history'),
    path('api/account/savings-goal/', SavingsGoalView.as_view(), name='savings-goal'),
    path('api/family/', FamilyView.as_view()),
    path('api/family/create/', FamilyCreateViewSet.as_view(), name='family-create'),
    path('api/family/invite/', FamilyAddMemberViewSet.as_view(), name='family-invite'),
    path('api/family/overview/', FamilyOverviewView.as_view(), name='family-overview'),
    path('api/budget-goal/', BudgetGoalView.as_view(), name='budget-goal'),
    path('api/budget-history/', BudgetHistoryView.as_view(), name='budget-history'),
    path('api/budget-transaction-overview/', BudgetTransactionView.as_view(), name='budget-transaction-overview'),
    path('api/transaction-bar-chart/', TransactionBarChartViewSet.as_view(), name='transaction-bar-chart'),
    path('api/transaction-table-view/', TransactionTableViewSet.as_view(), name='transaction-table-view'),
    path('api/transaction-pie-chart/', TransactionPieChartViewSet.as_view(), name='transaction-pie-chart'),
    path('api/user/create/', UserCreateView.as_view(), name='user-create'),
    path('api/token/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
