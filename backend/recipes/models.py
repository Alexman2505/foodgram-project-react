from django.core.validators import MinValueValidator
from django.db import models
from users.models import User


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет в HEX',
        max_length=7,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        max_length=200,
        unique=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиента."""

    name = models.CharField(
        verbose_name='Название',
        max_length=200
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты',
        through='RecipeIngredients'
    )
    image = models.ImageField(
        verbose_name='Фото',
        upload_to='recipes/'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200
    )
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(
            1, message='Время приготовления не может быть меньше 1 минуты.')],
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-pub_date', 'name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='уникальность_сочетания_автор_название_рецепта'
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


class RecipeIngredients(models.Model):
    """Модель состава ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipeingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='recipeingredients')
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиентов'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='уникальность_сочетания_рецепт_ингредиент'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'


class Favorite(models.Model):
    """Модель избранного рецепта."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='уникальность_сочетания_избранного_пользователь_рецепт'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное.'


class ShoppingCart(models.Model):
    """Модель корзины."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping_cart',
    )

    class Meta:
        verbose_name = 'Корзина покупок'
        verbose_name_plural = 'Корзины покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='уникальность_сочетания_корзины_пользователь_рецепт'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в корзину покупок.'
