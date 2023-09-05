from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorites, Ingredient, IngredientsForRecipes,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .mixins import CreateDestroyViewSet
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (FavoritesSerializer, IngredientSerializer,
                          RecipeGetSerializer, RecipePostPatchDeleteSerializer,
                          ShopCartSerializer, SubGetSerializer,
                          SubPostSerializer, SubSmallRecipeSerializer,
                          TagSerializer, UserChangePasswordSerializer,
                          UserCreateSerializer, UserGetSerializer)

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов"""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    """Вьюсет для рецептов"""
    queryset = Recipe.objects.all()
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostPatchDeleteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            "user": user.pk,
            "recipe": pk
        }
        serializer = ShopCartSerializer(data=data)
        if (request.method == 'POST'
                and serializer.is_valid(raise_exception=True)):
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        get_object_or_404(ShoppingCart, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        list_of_products = 'Список продуктов:'
        ingredients = IngredientsForRecipes.objects.filter(
            recipe__add_shopcart__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__measurement_unit'
        )
        total_amount = 0
        for ingredient in ingredients:
            total_amount += ingredient['amount']
            list_of_products += (
                f'\n{ingredient["ingredient__name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}'
            )
        file = 'list_of_products.txt'
        response = HttpResponse(list_of_products, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return response


class FavoriteViewSet(CreateDestroyViewSet):
    serializer_class = FavoritesSerializer
    permission_classes = [IsAuthenticated]
    model = Favorites

    def create(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.model.objects.create(user=request.user, recipe=recipe)
        serializer = SubSmallRecipeSerializer(recipe, many=False)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe_id = kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(
            self.model, user=request.user, recipe=recipe
            ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(ModelViewSet):
    """Вьюсет для пользователя"""
    queryset = User.objects.all()

    @property
    def user(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return UserGetSerializer
        return UserCreateSerializer

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            methods=['post'])
    def set_password(self, request):
        serializer = UserChangePasswordSerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            self.user.set_password(serializer.validated_data['new_password'])
            self.user.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            methods=['get'])
    def me(self, request):
        return Response(self.get_serializer(self.user).data,
                        status=status.HTTP_200_OK)

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            methods=['get'])
    def subscriptions(self, request):
        pages = self.paginate_queryset(
            User.objects.filter(subauthor__user=self.user)
            )
        serializer = SubGetSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True,
            permission_classes=[IsAuthenticated],
            methods=['post', 'delete'])
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        data = {
            "user": self.user.pk,
            "author": pk
        }
        serializer = SubPostSerializer(data=data)
        if (request.method == 'POST'
                and serializer.is_valid(raise_exception=True)):
            serializer.save()
            return Response(SubGetSerializer(
                author,
                context={'request': request}
            ).data)

        get_object_or_404(Subscription, user=self.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
