import base64

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorites, Ingredient, IngredientsForRecipes,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class Base64Serializer(serializers.ImageField):
    """Cериализатор обработки base64"""
    def to_internal_value(self, data):
        try:
            if isinstance(data, str) and data.startswith('data:image'):
                format, imgstr = data.split(';base64,')
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name='temp.' + format.split('/')[-1]
                )
        except Exception as e:
            raise ValidationError(f'Ошибка при обработке изображения: {e}')
        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя"""
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, instance):
        user_serializer = UserGetSerializer(instance, context=self.context)
        return user_serializer.data


class UserGetSerializer(serializers.ModelSerializer):
    """Сериализатор информации о пользователе"""
    is_subscribed = serializers.BooleanField(
        read_only=True,
        source='is_subscribed_by_current_user'
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed_by_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class UserChangePasswordSerializer(serializers.Serializer):
    """Сериализатор смены пароля"""
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('new_password', 'current_password',)

    def update(self, instance, validated_data):
        current_password = validated_data.get('current_password')
        new_password = validated_data.get('new_password')

        if not instance.check_password(current_password):
            raise ValidationError('Неправильный пароль!')
        validate_password(new_password)
        instance.set_password(new_password)
        instance.save()
        return instance


class SubGetSerializer(serializers.ModelSerializer):
    """Сериализатор отображения подписок пользователя"""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=author
            ).exists()
        return False

    def get_recipes(self, author):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = Recipe.objects.filter(author=author)
        rec_limit = request.query_params.get('recipes_limit')
        if rec_limit:
            recipes = recipes[:int(rec_limit)]
        return SubSmallRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()


class SubSmallRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор уменьшенного рецепта для отображения в подписках"""
    image = Base64Serializer()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubPostSerializer(serializers.ModelSerializer):
    """Сериализатор действия подписки"""
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def create(self, validated_data):
        if Subscription.objects.filter(
                user=validated_data['user'],
                author=validated_data['author']).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя!'
            )
        return Subscription.objects.create(**validated_data)

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя!'
            )
        return data


class IngredientsForRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор кол-ва ингредиентов в рецепте"""
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsForRecipes
        fields = ('id', 'name', 'measurement_unit', 'measure')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега"""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор получения рецепта"""
    tags = TagSerializer(many=True)
    author = UserGetSerializer()
    ingredients = IngredientsForRecipesSerializer(
        source='ingredient_for_recipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64Serializer()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time')
        read_only_fields = ('is_favorited', 'is_in_shopping_cart')

    @property
    def user(self):
        return self.context.get('request').user

    def get_is_favorited(self, recipe):
        return self.user.is_authenticated and Favorites.objects.filter(
            user=self.user, recipe=recipe.id
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        return self.user.is_authenticated and ShoppingCart.objects.filter(
            user=self.user, recipe=recipe.id
        ).exists()


class MeasureSerializer(serializers.ModelSerializer):
    """
    Сериализатор кол-ва ингредиентов в рецепте, при
    изменении или создании рецепта
    """
    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientsForRecipes
        fields = ('id', 'measure')


class RecipePostPatchDeleteSerializer(serializers.ModelSerializer):
    """Сериализатор создания/изменения/удаления рецепта"""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserGetSerializer(read_only=True)
    ingredients = MeasureSerializer(many=True)
    image = Base64Serializer()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate(self, data):
        tags_len = len(data['tags'])
        if tags_len == 0:
            raise serializers.ValidationError(
                'Пожалуйста добавьте теги к рецепту!'
            )
        ingredients_id = []
        for ingredient in data['ingredients']:
            if ingredient['measure'] < 1:
                raise serializers.ValidationError(
                    'Колличество ингридиента не может быть меньше одного'
                )
            ingredients_id.append(ingredient['id'])
        if data['cooking_time'] == 0:
            raise serializers.ValidationError(
                'Время приготовления блюда не может быть равно нулю!'
            )
        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            recipe.ingredient_for_recipe.create(
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                measure=ingredient['measure']
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.set([
            IngredientsForRecipes(
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                recipe=instance,
                measure=ingredient['measure']
            ) for ingredient in ingredients
        ])
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance,
                                   context=context).data


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ['id', 'user', 'recipe']
        model = Favorites


class ShopCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок"""

    class Meta:
        model = ShoppingCart
        fields = '__all__'
