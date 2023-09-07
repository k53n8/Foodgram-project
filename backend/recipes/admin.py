from django.contrib import admin

from .models import (Favorites, Ingredient, IngredientsForRecipes, Recipe,
                     ShoppingCart, Tag)


class IngredientsForRecipesInline(admin.StackedInline):
    model = IngredientsForRecipes
    min_num = 1
    extra = 1


class FavoritesInline(admin.StackedInline):
    model = Favorites


class ShoppingCartInline(admin.StackedInline):
    model = ShoppingCart


class RecipeAdmin(admin.ModelAdmin):
    inlines = [
        IngredientsForRecipesInline, FavoritesInline, ShoppingCartInline
        ]
    list_display = ('pk', 'author', 'name', 'text', 'cooking_time',
                    'pub_date')
    search_fields = ('author', 'name', 'tags')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = 'N/A'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    empty_value_display = 'N/A'


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name',)
    empty_value_display = 'N/A'


admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
