from django.shortcuts import render
from rest_framework import generics, viewsets
from .models import User, Family, Category, Budget, Transaction, Account
from .serializers import UserSerializer, FamilySerializer, CategorySerializer, BudgetSerializer


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class FamilyView(generics.ListAPIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer