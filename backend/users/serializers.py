
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core import validators

from .models import User, Subscription
from food.serializers import Base64ImageField, RecipeShortSerializer

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

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            subscriber=request.user,
            author=obj
        ).exists()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация."""
    email = serializers.EmailField(
        required=True,
        max_length=254,
    )
    username = serializers.CharField(
        required=True,
        max_length=150,
        validators=[
            validators.RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Enter a valid username. This value may contain only letters, numbers, @/./+/-/_ characters.',
            ),
        ],
    )
    first_name = serializers.CharField(
        required=True,
        max_length=150,
    )
    last_name = serializers.CharField(
        required=True,
        max_length=150,
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
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
        extra_kwargs = {'password': {'write_only': True}}

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

    def validate_username(self, value):
        """Check username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with that username already exists.')
        return value

    def validate_email(self, value):
        """Check email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with that email already exists.')
        return value


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


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


class SubscribedUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(subscriber=request.user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
        recipes = obj.recipes.all()[:recipes_limit]
        return RecipeShortSerializer(recipes, many=True, context={'request': request}).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True, write_only=True, label="Current password")
    new_password = serializers.CharField(
        required=True, write_only=True, label="New password")

    def validate_new_password(self, value):
        validate_password(value)  # Django's password validation
        return value

    def validate(self, data):
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        user = self.context['request'].user

        if user.is_superuser:
            # Superusers authenticate with username
            if not authenticate(username=user.username, password=current_password):
                raise serializers.ValidationError(
                    {'current_password': 'Incorrect password.'})
        else:
            # Regular users authenticate with email
            if not authenticate(username=user.email, password=current_password):
                raise serializers.ValidationError(
                    {'current_password': 'Incorrect password.'})  # or user.username

        if current_password == new_password:
            raise serializers.ValidationError(
                {'new_password': 'The new password cannot be the same as the old password.'}
            )

        # Return the validated data with original field names
        return {'old_password': current_password, 'new_password': new_password}

    def save(self):
        user = self.context['request'].user
        password = self.validated_data['new_password']
        user.set_password(password)
        user.save()
        update_session_auth_hash(self.context['request'], user)
