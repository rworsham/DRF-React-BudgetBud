from django.urls import path
from .views import UserListCreateView, UserRetrieveUpdateDestroyView, FamilyView

urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('family', FamilyView.as_view()),
]
