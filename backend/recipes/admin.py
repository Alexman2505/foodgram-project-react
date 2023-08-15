from django.contrib.admin import register, ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin
from import_export.resources import ModelResource

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(TabularInline):
    model = RecipeIngredients
    extra = 0
    min_num = 1


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    """Управление рецептами в админке."""

    list_display = ('id', 'name', 'author', 'text', 'cooking_time', 'pub_date')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'


@register(Tag)
class TagAdmin(ModelAdmin):
    """Управление тегами в админке."""

    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name',)
    empty_value_display = '-пусто-'


class IngredientResource(ModelResource):
    """Необходим для импорта ингредиентов для import_export"""

    class Meta:
        model = Ingredient


@register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    """Управление ингредиентами в админке."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'
    resource_class = IngredientResource


@register(RecipeIngredients)
class RecipeIngredientsAdmin(ModelAdmin):
    """Управление ингредиентами в рецептах в админке."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient')
    empty_value_display = '-пусто-'


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    """Управление избранными рецептами в админке."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    """Управление корзиной покупок в админке."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user', 'recipe')
    list_filter = ('user', 'recipe')
    empty_value_display = '-пусто-'
