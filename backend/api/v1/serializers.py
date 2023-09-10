from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorites, Ingredient, IngredientsForRecipes,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class UserCreateSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'password'
        )


class UserGetSerializer(UserSerializer):
    """Сериализатор информации о пользователе"""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.subauthor.filter(user=request.user).exists()
        )


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


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор получения рецепта"""
    tags = TagSerializer(many=True)
    author = UserGetSerializer(read_only=True)
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
            request
            and request.user.is_authenticated
            and obj.add_favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.add_shoppingcart.filter(user=request.user).exists()
        )


class AmountSerializer(serializers.ModelSerializer):
    """
    Сериализатор кол-ва ингредиентов в рецепте, при
    изменении или создании рецепта
    """
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

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
    ingredients = AmountSerializer(many=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    # def validate(self, data):
    #     tags = data.get('tags')
    #     ingredients = data.get('ingredients')
    #     if not tags:
    #         raise serializers.ValidationError(
    #             {'tags': 'Пожалуйста добавьте теги к рецепту!'}
    #         )
    #     if len(tags) != len(set(tags)):
    #         raise serializers.ValidationError(
    #             {'tags': 'Теги не должны повторяться!'}
    #         )
    #     if not ingredients:
    #         raise serializers.ValidationError(
    #             {'ingredients': 'Пожалуйста добавьте ингредиенты!'}
    #         )
    #     ingredient_ids = [ingredient['id'] for ingredient in ingredients]
    #     if len(ingredient_ids) != len(set(ingredient_ids)):
    #         raise serializers.ValidationError(
    #             {'ingredients': 'Ингредиенты не должны повторяться!'}
    #         )
    #     return data

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
        if instance is None:
            raise serializers.ValidationError(
                {'recipe': 'Рецепт не найден!'}
            )
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_bulk_ingredients(recipe=instance, ingredients=ingredients)
        return super().update(instance, validated_data)

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
                {'recipe': 'Вы уже добавили этот рецепт!'}
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
