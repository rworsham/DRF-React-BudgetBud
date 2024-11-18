from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserListCreateView, UserRetrieveUpdateDestroyView, FamilyView, CategoryViewSet, BudgetViewSet, \
    TransactionViewSet, AccountViewSet, LoginView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename="category")
router.register(r'budget', BudgetViewSet)
router.register(r'transaction', TransactionViewSet)
router.register(r'account', AccountViewSet)

urlpatterns = [
    path('api/users/', UserListCreateView.as_view(), name='user-list-create'),
    path('api/users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('api/family', FamilyView.as_view()),
    path('api/', include(router.urls)),
    path('api/token/', LoginView.as_view(), name='login-view'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
