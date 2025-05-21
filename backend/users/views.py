from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from api.permissions import IsAuthorOrReadOnly
from .models import User, Subscription
from .serializers import (
    UserSerializer,
    ChangePasswordSerializer,
    AvatarSerializer,
    AuthTokenSerializer,
    UserRegistrationSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authtoken.models import Token


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        print(f"Action: {self.action}")  # Отладочный вывод
        print(f"Request method: {self.request.method}")  # Отладочный вывод
        if self.action == 'list':
            return UserSerializer
        elif self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Настраиваем разрешения для конкретных действий.
        """
        if self.action in ['create']:
            permission_classes = []
        elif self.action in ['partial_update', 'update', 'list', 'retrieve']:
            permission_classes = [IsAuthorOrReadOnly]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class AuthTokenView(APIView):
    def post(self, request):
        serializer = AuthTokenSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.create(serializer.validated_data), status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(status=204)
        except (AttributeError, Token.DoesNotExist):
            return Response({'error': 'Invalid token'}, status=400)


class UserAvatarUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, partial=True)
        if serializer.is_valid():
            request.user.avatar.delete(save=True)
            serializer.save()
            avatar_url = serializer.instance.avatar.url
            full_avatar_url = request.build_absolute_uri(avatar_url)
            return Response({'avatar': full_avatar_url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
