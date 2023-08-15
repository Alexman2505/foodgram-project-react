from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import (
    CASCADE,
    CharField,
    DateTimeField,
    ForeignKey,
    ImageField,
    ManyToManyField,
    Model,
    PositiveIntegerField,
    SlugField,
    TextField,
    UniqueConstraint,
)

from users.models import User


class Tag(Model):
    """Модель тега."""

    name = CharField(verbose_name='Название', max_length=200, unique=True)
    color = CharField(
        verbose_name='Цвет в HEX',
        max_length=7,
        unique=True,
        validators=[
            RegexValidator(
                regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
                message="Введенное значение не является цветом в формате HEX!",
            )
        ],
    )
    slug = SlugField(
        verbose_name='Уникальный слаг', max_length=200, unique=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(Model):
    """Модель ингридиента."""

    name = CharField(verbose_name='Название', max_length=200)
    measurement_unit = CharField(
        verbose_name='Единица измерения', max_length=200
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(Model):
    """Модель рецепта."""

    tags = ManyToManyField(Tag, verbose_name='Теги', related_name="recipes")
    author = ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=CASCADE,
        related_name='recipes',
    )
    ingredients = ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='RecipeIngredients',
    )
    image = ImageField(
        verbose_name='Изображение рецепта', upload_to='recipes/'
    )
    name = CharField(verbose_name='Название рецепта', max_length=200)
    text = TextField(verbose_name='Описание рецепта')
    cooking_time = PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1, message='Время приготовления не может быть меньше 1 минуты.'
            )
        ],
    )
    pub_date = DateTimeField(verbose_name='Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date', 'name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            UniqueConstraint(
                fields=['author', 'name'],
                name='уникальность_сочетания_автор_название_рецепта',
            )
        ]

    def is_favorited(self, user):
        """Проверяем, находится ли рецепт в избранном."""
        return self.favorites.filter(user=user).exists()

    def is_in_shopping_cart(self, user):
        """Проверяем, находится ли рецепт в корзине"""
        return self.shopping_cart.filter(user=user).exists()

    def __str__(self):
        return self.name


class RecipeIngredients(Model):
    """Модель состава ингредиентов в рецепте."""

    recipe = ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=CASCADE,
        related_name='recipeingredients',
    )
    ingredient = ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=CASCADE,
        related_name='recipeingredients',
    )
    amount = PositiveIntegerField(
        verbose_name='Количество ингредиентов',
        validators=[
            MinValueValidator(
                1, message="Минимальное количество ингридиентов 1!"
            )
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ["-id"]
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='уникальность_сочетания_рецепт_ингредиент',
            )
        ]

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'


class Favorite(Model):
    """Модель избранного рецепта."""

    user = ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=CASCADE,
        related_name='favorites',
    )
    recipe = ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=CASCADE,
        related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='уникальность_сочетания_избранного_пользователь_рецепт',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(Model):
    """Модель корзины."""

    user = ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=CASCADE,
        related_name='shopping_cart',
    )
    recipe = ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='уникальность_сочетания_корзины_пользователь_рецепт',
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в корзину покупок.'
