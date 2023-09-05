from django.contrib.auth import get_user_model
from django_filters import (CharFilter, FilterSet, ModelChoiceFilter,
                            ModelMultipleChoiceFilter, NumberFilter)

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""
    is_favorited = NumberFilter(
        field_name='add_favorites__user', method='filter_is_favorited'
    )
    is_in_shopping_cart = NumberFilter(
        field_name='add_shopcart__user', method='filter_is_in_shopping_cart'
    )
    author = ModelChoiceFilter(
        field_name='author', queryset=User.objects.all()
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug', to_field_name='slug',
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'author', 'tags',)

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(add_favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(add_shopcart__user=self.request.user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='startswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
