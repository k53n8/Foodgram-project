from colorfield.fields import ColorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram.constants import (COLOR_FIELD_SYMBOL_LIMIT, DEFAULT_COLOR,
                                GENERAL_FIELDS_SYMBOL_LIMIT,
                                RECIPE_NAME_FIELD_SYMBOL_LIMIT)
from users.models import User


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Название тега',
        unique=True,
    )
    color = ColorField(
        max_length=COLOR_FIELD_SYMBOL_LIMIT,
        verbose_name='Цвет тега',
        default=DEFAULT_COLOR,
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        unique=True,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Название ингредиента',
    )
    measurement_unit = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique ingredient')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    name = models.CharField(
        max_length=RECIPE_NAME_FIELD_SYMBOL_LIMIT,
        verbose_name='Название рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        through='IngredientsForRecipes',
        verbose_name='Ингредиенты для рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тег',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (мин.)',
        validators=[
            MinValueValidator(
                1, message='Время приготовления должно быть больше 0!'
                ),
            MaxValueValidator(
                32000, message='Время приготовления не должно превышать 32000!'
                ),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    image = models.ImageField(
        blank=True,
        default=None,
        upload_to='recipes/images/',
        verbose_name='Изображение',
    )

    class Meta:
        ordering = ['pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class FavAndCartTemplate(models.Model):
    """Базовая модель для избранного и списка покупок"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='add_%(class)s'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='add_%(class)s'
    )

    class Meta:
        abstract = True
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'], name='unique_relation_%(class)s'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил(а) {self.recipe}'


class ShoppingCart(FavAndCartTemplate):
    """Модель добавления рецепта в список покупок"""
    class Meta(FavAndCartTemplate.Meta):
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списках покупок'


class Favorites(FavAndCartTemplate):
    """Модель избранного для рецептов"""
    class Meta(FavAndCartTemplate.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class IngredientsForRecipes(models.Model):
    """Модель связи рецептов с ингредиентами"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_for_recipe',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_for_recipe',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(
                1, message='Кол-во ингредиента должно быть больше 0!'
                ),
            MaxValueValidator(
                32000, message='Кол-во ингредиента не должно превышать 32000!'
                ),
        ],
    )

    class Meta:
        verbose_name = 'Количество ингредиента в рецепте',
        verbose_name_plural = 'Количество ингредиентов в рецепте'

    def __str__(self):
        return (f'В {self.recipe} используется {self.ingredient}'
                f' в кол-ве {self.amount}')
