from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models import CheckConstraint, F, Q

from foodgram.constants import GENERAL_FIELDS_SYMBOL_LIMIT


class User(AbstractUser):
    """Модель пользователя"""
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта',
    )
    username = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        unique=True,
        verbose_name='Псевдоним пользователя',
        validators=[UnicodeUsernameValidator()],
    )
    first_name = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Фамилия пользователя',
    )
    password = models.CharField(
        max_length=GENERAL_FIELDS_SYMBOL_LIMIT,
        verbose_name='Пароль',
    )

    class Meta:
        ordering = ['username']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscription(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subauthor',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            CheckConstraint(
                check=~Q(user=F('author')),
                name='self_subscription_check'
            )
        ]
