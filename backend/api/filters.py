from django.contrib.auth import get_user_model
from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    ModelMultipleChoiceFilter,
)

from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(FilterSet):
    """Фильтр для поиска по списку ингредиентов
    (поиск ведется по вхождению в начало названия)."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    """Фильтр для рецептов."""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = BooleanFilter(method='filter_favorite_or_cart')
    is_in_shopping_cart = BooleanFilter(method='filter_favorite_or_cart')

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
        )

    def filter_favorite_or_cart(self, queryset, name, value):
        user = self.request.user
        if value and not user.is_anonymous:
            field_name = (
                'favorite' if name == 'is_favorited' else 'shoppingcart'
            )
            filter_parameters = {f'{field_name}__user': user}
            return queryset.filter(**filter_parameters)
        return queryset
