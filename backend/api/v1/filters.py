from django.contrib.auth import get_user_model
from django_filters import (CharFilter, FilterSet, ModelChoiceFilter,
                            ModelMultipleChoiceFilter, NumberFilter)

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""
    is_favorited = NumberFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = NumberFilter(
        method='filter_is_in_shopping_cart'
    )
    author = ModelChoiceFilter(
        field_name='author', queryset=User.objects.all()
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug', queryset=Tag.objects.all(),
        to_field_name='slug'
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'author', 'tags',)

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(
                add_favorites__user_id=self.request.user.pk
            )
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(
                add_shoppingcart__user_id=self.request.user.pk
            )
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='startswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
