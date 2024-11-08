from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserListCreateView, UserRetrieveUpdateDestroyView, FamilyView, CategoryViewSet, BudgetViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'budget', BudgetViewSet)

urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('family', FamilyView.as_view()),
    path('api/', include(router.urls)),
]
