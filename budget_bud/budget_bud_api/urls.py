from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserListCreateView, UserRetrieveUpdateDestroyView, FamilyView, CategoryViewSet, BudgetViewSet, \
    TransactionViewSet, AccountViewSet, AllTransactionViewSet, TransactionBarChartViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename="category")
router.register(r'budget', BudgetViewSet, basename="budget")
router.register(r'transaction', TransactionViewSet, basename='transaction')
router.register(r'transactions', AllTransactionViewSet, basename='all_transactions')
router.register(r'account', AccountViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/users/', UserListCreateView.as_view(), name='user-list-create'),
    path('api/user/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('api/family', FamilyView.as_view()),
    path('api/transaction-bar-chart/', TransactionBarChartViewSet.as_view(), name='transaction-bar-chart'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
