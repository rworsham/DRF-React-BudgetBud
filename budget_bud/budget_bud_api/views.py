from datetime import timedelta
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import User, Family, Category, Budget, Transaction, Account
from .serializers import UserSerializer, FamilySerializer, CategorySerializer, BudgetSerializer, TransactionSerializer, \
    AccountSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.http import JsonResponse

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = JsonResponse({"message": "Login successful"})
            response.set_cookie(
                'access_token', access_token,
                httponly=True,
                secure=True,
                samesite='None',
                max_age=timedelta(minutes=30),
                path='/'
            )

            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=True,
                secure=True,
                samesite='None',
                max_age=timedelta(days=7),
                path='/'
            )

            return response
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=401)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class FamilyView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Family.objects.all()
    serializer_class = FamilySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Category.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Budget.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer