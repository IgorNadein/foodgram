
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Subscription
from food.serializers import Base64ImageField

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        # read_only_fields = ('username', 'email')

    # def get_subscriptions_count(self, obj):
    #     return obj.subscriptions.count()

    # def get_subscribers_count(self, obj):
    #     return obj.subscribers.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user,
            author=obj
        ).exists()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный старый пароль")
        return value

    def validate(self, attrs):
        try:
            validate_password(attrs['new_password'])
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        return attrs

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get(
                'request'), email=email, password=password)

            if not user:
                # Проверка существования пользователя
                user = User.objects.filter(email=email).first()
                if not user:
                    raise serializers.ValidationError(
                        {'detail': 'Пользователь с таким email не найден'},
                        code='authorization'
                    )

                raise serializers.ValidationError(
                    {'detail': 'Неверный пароль'},
                    code='authorization'
                )
        else:
            raise serializers.ValidationError(
                {'detail': 'Пожалуйста, предоставьте email и пароль'},
                code='authorization'
            )

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return {'auth_token': token.key}
