from django.contrib.auth import get_user_model
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorites, Ingredient, IngredientsForRecipes,
                            Recipe, ShoppingCart, Tag)
from users.models import Subscription

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageNumberPaginationWithLimit
from .permissions import IsAdminAuthorOrReadOnly
from .serializers import (FavoritesSerializer, IngredientSerializer,
                          RecipeGetSerializer, RecipePostPatchDeleteSerializer,
                          ShopCartSerializer, SubGetSerializer,
                          SubPostSerializer, TagSerializer,
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
    pagination_class = PageNumberPaginationWithLimit

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipePostPatchDeleteSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        FavoritesSerializer.create_entry(FavoritesSerializer, pk, request)
        return Response(status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = Favorites.objects.filter(
            recipe=recipe, user=request.user
            ).delete()
        if deleted == 0:
            return Response(
                {'error': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        ShopCartSerializer.create_entry(ShopCartSerializer, pk, request)
        return Response(status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        deleted, _ = Favorites.objects.filter(
            recipe=recipe, user=request.user
            ).delete()
        if deleted == 0:
            return Response(
                {'error': 'Рецепт не найден в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.filter(recipe=recipe, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_product_list(self, ingredients):
        list_of_products = [
            f'{ingredient["ingredient__name"]} - '
            f'{ingredient["amount"]} '
            f'{ingredient["ingredient__measurement_unit"]}'
            for ingredient in ingredients
        ]
        list_of_products.insert(0, 'Список продуктов:')
        return list_of_products

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = IngredientsForRecipes.objects.filter(
            recipe__add_shopcart__user=request.user
        ).order_by('ingredient__name').values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=F('amount'))

        list_of_products = self.get_product_list(ingredients)
        file = 'list_of_products.txt'
        response = HttpResponse(
            '\n'.join(list_of_products), content_type='text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename="{file}.txt"'
        return response


class UserViewSet(UserViewSet):
    """Вьюсет для пользователя"""
    queryset = User.objects.all()
    pagination_class = PageNumberPaginationWithLimit

    @property
    def user(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return UserGetSerializer
        return UserCreateSerializer

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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        data = {
            "user": self.user.pk,
            "author": pk
        }
        serializer = SubPostSerializer(data=data)
        serializer.save()
        return Response(SubGetSerializer(
            author,
            context={'request': request}
        ).data)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        deleted, _ = Subscription.objects.filter(
            user=self.user, author=author
        ).delete()
        if deleted == 0:
            return Response(
                {'error': 'Вы не подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
