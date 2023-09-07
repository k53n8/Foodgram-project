import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (Favorites, Ingredient, IngredientsForRecipes,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания пользователя"""
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы,'
                'цифры и символ подчеркивания!'
            )
        return value

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
        return bool(
           request and
           request.user.is_authenticated and
           obj.subauthor.filter(user=request.user).exists()
        )


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


class SubGetSerializer(UserGetSerializer):
    """Сериализатор отображения подписок пользователя"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = UserGetSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipes = obj.recipes.all()
        rec_limit = request.query_params.get('recipes_limit')
        if rec_limit:
            recipes = recipes[:int(rec_limit)]
        return SubSmallRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubSmallRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор уменьшенного рецепта для отображения в подписках"""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubPostSerializer(serializers.ModelSerializer):
    """Сериализатор действия подписки"""
    class Meta:
        model = Subscription
        fields = ('user', 'author')

    def create(self, validated_data):
        return Subscription.objects.create(**validated_data)

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя!'
            )
        if Subscription.objects.filter(
                user=data['user'], author=data['author']
                ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя!'
            )
        return data


class IngredientsForRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор кол-ва ингредиентов в рецепте"""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsForRecipes
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image',
                  'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            obj.add_favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request and
            request.user.is_authenticated and
            obj.add_shoppingcart.filter(user=request.user).exists()
        )


class AmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор кол-ва ингредиентов в рецепте
    при изменении или создании рецепта
    """
    id = serializers.IntegerField()

    class Meta:
        model = IngredientsForRecipes
        fields = ('id', 'amount')


class RecipePostPatchDeleteSerializer(serializers.ModelSerializer):
    """Сериализатор создания/изменения/удаления рецепта"""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserGetSerializer(read_only=True)
    ingredients = AmountSerializer(
        source='ingredient_for_recipe',
        many=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Пожалуйста добавьте теги к рецепту!'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Вы уже добавили этот тег!'
            )
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Пожалуйста добавьте ингредиенты!'
            )
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Вы уже добавили этот ингредиент!'
            )
        return ingredients

    def create_bulk_ingredients(self, recipe, ingredients):
        IngredientsForRecipes.objects.bulk_create(
            [IngredientsForRecipes(
                ingredient_id=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_bulk_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_bulk_ingredients(recipe=instance, ingredients=ingredients)
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance,
                                   context=context).data


class FavAndShopTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'user', 'recipe')

    def validate(self, data):
        recipe = data.get('recipe')
        user = data.get('user')
        if self.Meta.model.objects.filter(recipe=recipe, user=user).exists():
            raise serializers.ValidationError(
                'Вы уже добавили этот рецепт!'
            )
        return data

    @staticmethod
    def create_entry(serializer_class, pk, request):
        data = {'user': request.user.pk, 'recipe': pk}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return SubSmallRecipeSerializer(
            instance,
            context=context
        ).data


class FavoritesSerializer(FavAndShopTemplateSerializer):
    """Сериализатор избранного"""
    class Meta(FavAndShopTemplateSerializer.Meta):
        model = Favorites


class ShopCartSerializer(FavAndShopTemplateSerializer):
    """Сериализатор списка покупок"""
    class Meta(FavAndShopTemplateSerializer.Meta):
        model = ShoppingCart
