from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    """Фильтр для поиска по списку ингредиентов
    (поиск ведется по вхождению в начало названия)."""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(
        method='filter_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_favorited(self, queryset, name, value):
        """Фильтруем рецепты по избранным."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтруем рецепты по их наличию в корзине покупок."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(shopping_cart__user=user)
        return queryset
