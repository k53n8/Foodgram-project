from django_filters import (BooleanFilter, FilterSet, ModelChoiceFilter,
                            ModelMultipleChoiceFilter)

from recipes.models import Recipe, Tag, User


class RecipeFilter(FilterSet):
    """Фильтр для рецептов"""
    is_favorited = BooleanFilter(
        field_name='in_favorites__user', method='filter_is_favorited'
        )
    is_in_shopping_cart = BooleanFilter(
        field_name='in_carts__user', method='filter_is_in_shopping_cart'
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
            return queryset.filter(in_favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopcart__user=self.request.user)
        return queryset
