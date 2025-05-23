from django.shortcuts import get_object_or_404
from food.serializers import RecipeShortSerializer
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAuthorOrReadOnly
from .models import Subscription, User
from .serializers import (AuthTokenSerializer, AvatarSerializer,
                          PasswordChangeSerializer, SubscribedUserSerializer,
                          UserRegistrationSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        print(f"Action: {self.action}")
        print(f"Request method: {self.request.method}")
        if self.action == 'list':
            return UserSerializer
        elif self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['partial_update', 'update', 'list', 'retrieve']:
            permission_classes = [IsAuthorOrReadOnly]
        elif self.action in ['destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'],
            url_path='me', permission_classes=[IsAuthorOrReadOnly])
    def me(self, request):
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Требуется аутентификация.'},
                            status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписка/отписка от пользователя."""
        user_to_subscribe = get_object_or_404(User, pk=pk)
        current_user = request.user
        if not current_user.is_authenticated:
            return Response(
                {'detail': 'Требуется аутентификация.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == 'POST':
            if current_user == user_to_subscribe:
                return Response(
                    {'error': 'Вы не можете подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                subscriber=current_user,
                author=user_to_subscribe
            ).exists():
                return Response(
                    {'error': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(
                subscriber=current_user, author=user_to_subscribe)
            recipes_limit = request.query_params.get('recipes_limit')
            if recipes_limit:
                try:
                    recipes_limit = int(recipes_limit)
                except ValueError:
                    recipes_limit = None
            subscribed_user_data = {
                'email': user_to_subscribe.email,
                'id': user_to_subscribe.id,
                'username': user_to_subscribe.username,
                'first_name': user_to_subscribe.first_name,
                'last_name': user_to_subscribe.last_name,
                'is_subscribed': True,
                'recipes': RecipeShortSerializer(
                    user_to_subscribe.recipes.all()[:recipes_limit],
                    many=True,
                    context={'request': request}
                ).data,
                'recipes_count': user_to_subscribe.recipes.count(),
                'avatar': (
                    user_to_subscribe.avatar.url
                    if user_to_subscribe.avatar
                    else None
                )
            }
            return Response(
                subscribed_user_data,
                status=status.HTTP_201_CREATED
            )

        elif request.method == 'DELETE':
            try:
                subscription = Subscription.objects.get(
                    subscriber=current_user, author=user_to_subscribe)
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Subscription.DoesNotExist:
                return Response(
                    {'error': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        """
        Позволяет аутентифицированому пользователю изменить свой пароль.
        """
        serializer = PasswordChangeSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


class AuthTokenView(APIView):
    def post(self, request):
        serializer = AuthTokenSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(
                serializer.create(serializer.validated_data),
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response(status=204)
        except (AttributeError, Token.DoesNotExist):
            return Response({'error': 'Invalid token'}, status=400)


class UserAvatarUpdateOrDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(
            request.user, data=request.data, partial=False)
        if serializer.is_valid():
            if request.user.avatar:
                request.user.avatar.delete(save=True)
            serializer.save()
            if serializer.instance.avatar:
                avatar_url = serializer.instance.avatar.url
                full_avatar_url = request.build_absolute_uri(avatar_url)
                return Response(
                    {'avatar': full_avatar_url},
                    status=status.HTTP_200_OK
                )
            else:
                return Response({'avatar': None}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.user.avatar:
            request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    serializer_class = SubscribedUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        subscribed_users = User.objects.filter(followers__subscriber=user)
        return subscribed_users

    def get_serializer_context(self):
        return {'request': self.request}
