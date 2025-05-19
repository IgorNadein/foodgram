from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Subscription
from .serializers import UserSerializer, ChangePasswordSerializer, AvatarSerializer, SubscriptionSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(methods=['post'], detail=False)
    def register(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(methods=['get'], detail=True)
    def profile(self, request, pk=None):
        user = self.get_object()
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def current(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(methods=['put'], detail=True)
    def add_avatar(self, request, pk=None):
        user = self.get_object()
        serializer = AvatarSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    @action(methods=['delete'], detail=True)
    def delete_avatar(self, request, pk=None):
        user = self.get_object()
        user.avatar.delete()
        return Response(status=204)

    @action(methods=['post'], detail=True)
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Пароль успешно изменен'}, status=200)
        return Response(serializer.errors, status=400)

    @action(methods=['post'], detail=True)
    def follow(self, request, pk=None):
        author = self.get_object()
        subscriber = request.user
        subscription, created = Subscription.objects.get_or_create(
            author=author, subscriber=subscriber)
        if created:
            return Response({'detail': 'Подписка успешно создана'}, status=201)
        return Response({'detail': 'Вы уже подписаны на этого пользователя'}, status=400)

    @action(methods=['delete'], detail=True)
    def unfollow(self, request, pk=None):
        author = self.get_object()
        subscriber = request.user
        try:
            subscription = Subscription.objects.get(
                author=author, subscriber=subscriber)
            subscription.delete()
            return Response({'detail': 'Подписка удалена'}, status=204)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Вы не подписаны на этого пользователя'}, status=404)
