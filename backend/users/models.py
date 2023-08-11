from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    username = models.CharField(
        verbose_name='Логин',
        max_length=150,
        unique=True,
        null=False,
        blank=False
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=150
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='Уникальность_подписчиков'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='Ограничение_подписки_на_самого_себя'
            )
        ]

    def __str__(self) -> str:
        return f'Подписка {self.user.username} на {self.author.username}.'
