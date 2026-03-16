from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate

from apps.users.serializers.auth_serializers import (
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
)

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny] 
    
    def post(self, request) :
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Register successful", "email": user.email},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user is None:
                return Response(
                    {"error": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChangePasswordView(APIView) :
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serialized = ChangePasswordSerializer(data=request.data)
        if serialized.is_valid():
            user = request.user
            old_password = serialized.validated_data['old_password']
            new_password = serialized.validated_data['new_password']
            
            if not user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user.set_password(new_password)
            user.save()
            return Response({"message": "Password changed successfully"})
        return Response(serialized.errors, status=status.HTTP_400_BADREQUEST)
    
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
