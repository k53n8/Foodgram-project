from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField(
        max_length=settings.OTHER_SYM_LIMIT,
        verbose_name='Название тега',
        unique=True,
    )
    color = models.CharField(
        max_length=settings.OTHER_SYM_LIMIT,
        verbose_name='Цвет тега',
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        unique=True,
        validators=[
            RegexValidator(regex=r'^[-a-zA-Z0-9_]+$')],

    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег',
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(
        max_length=settings.OTHER_SYM_LIMIT,
        verbose_name='Название ингридиента',
    )
    measurement_unit = models.CharField(
        max_length=settings.OTHER_SYM_LIMIT,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_ingredient')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов"""
    name = models.CharField(
        max_length=settings.RECIPE_SYM_LIMIT,
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
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (мин.)',
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
        null=True,
        default=None,
        upload_to='recipes/images/',
        verbose_name='Изображение',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    """Модель добавления рецепта в список покупок"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopcart',
        verbose_name='Рецепты для покупок',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopcart',
        verbose_name='Владелец списка покупок',
    )

    class Meta:
        verbose_name = 'Рецепт в списке покупок'
        verbose_name_plural = 'Рецепты в списках покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='Рецепт уже добавлен в список покупок!'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил(а) в список покупок {self.recipe}'


class Favorites(models.Model):
    """Модель избранного для рецептов"""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Избранные рецепты',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'user'],
                                    name='Рецепт уже добавлен в избранное!')
        ]

    def __str__(self) -> str:
        return f'{self.user} добавил(а) в избранное {self.recipe}'


class IngredientsForRecipes(models.Model):
    """Модель связи рецептов с ингредиентами"""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_measure',
        verbose_name='Ингридиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_measure',
        verbose_name='Рецепт',
    )
    measure = models.PositiveSmallIntegerField(
        verbose_name='Количество ингридиента'
    )

    class Meta:
        verbose_name = 'Количество ингридиента в рецепте',
        verbose_name_plural = 'Количество ингридиентов в рецепте'

    def __str__(self):
        return (f'В {self.recipe} используется {self.ingredient}'
                f' в кол-ве {self.measure}')
