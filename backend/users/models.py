from django.contrib.auth.models import AbstractUser
from django.db.models import (
    CASCADE,
    CharField,
    CheckConstraint,
    EmailField,
    ForeignKey,
    F,
    Model,
    Q,
    UniqueConstraint,
)


class User(AbstractUser):
    """Модель пользователя."""

    email = EmailField(
        verbose_name='Адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
        null=False,
    )
    username = CharField(
        verbose_name='Логин',
        max_length=150,
        unique=True,
        null=False,
        blank=False,
    )
    first_name = CharField(verbose_name='Имя', max_length=150, blank=False)
    last_name = CharField(verbose_name='Фамилия', max_length=150, blank=False)
    password = CharField(verbose_name='Пароль', max_length=150)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(Model):
    """Модель подписки пользователей."""

    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='follower',
        verbose_name="Подписчик",
    )
    author = ForeignKey(
        User, on_delete=CASCADE, related_name='following', verbose_name="Автор"
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

        constraints = [
            UniqueConstraint(
                fields=['user', 'author'], name='Уникальность_подписчиков'
            ),
            CheckConstraint(
                check=~Q(user=F('author')),
                name='Ограничение_подписки_на_самого_себя',
            ),
        ]

    def __str__(self) -> str:
        return f'Подписка {self.user.username} на {self.author.username}.'
