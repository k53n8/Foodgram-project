from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя"""
    ADMIN = 'admin'
    USER = 'user'
    ROLES = [
        (ADMIN, 'administrator'),
        (USER, 'user'),
    ]

    email = models.EmailField(
        max_length=settings.USER_EMAIL_SYM_LIMIT,
        unique=True,
        verbose_name='Электронная почта',
    )
    username = models.CharField(
        max_length=settings.USER_SYM_LIMIT,
        unique=True,
        verbose_name='Псевдоним пользователя',
    )
    first_name = models.CharField(
        max_length=settings.USER_SYM_LIMIT,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=settings.USER_SYM_LIMIT,
        verbose_name='Фамилия пользователя',
    )
    password = models.CharField(
        max_length=settings.USER_SYM_LIMIT,
        verbose_name='Пароль',
    )
    role = models.SlugField(
        choices=ROLES,
        default=USER,
        verbose_name='Роль'
    )
    REQUIRED_FIELDS = ['email']

    @property
    def is_admin(self):
        return self.role == self.ADMIN

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
            )
        ]
