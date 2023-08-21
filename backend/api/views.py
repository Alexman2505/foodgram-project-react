from collections import defaultdict
from djoser.views import UserViewSet

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.viewsets import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from api.serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    RecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredients,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class CustomPageNumberPagination(PageNumberPagination):
    """Кастомный пагинатор"""

    page_size_query_param = 'page_size'


class CustomUserViewSet(UserViewSet):
    """Кастомный Viewset модели пользователя."""

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def list(self, request):
        queryset = self.get_queryset()
        paginator = CustomPageNumberPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получаем список пользователей,
        на которого подписан текущий пользователь"""
        queryset = User.objects.filter(following__user=request.user)
        paginator = CustomPageNumberPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = SubscriptionSerializer(
            paginated_queryset,
            many=True,
            context={
                'request': request,
                'format': self.format_kwarg,
                'view': self,
            },
        )
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        """Этот метод позволяет текущему пользователю подписаться
        или отписаться от другого пользователя.
        """
        author = get_object_or_404(User, id=id)
        subscription = Subscription.objects.filter(
            user=request.user, author=author
        )
        if request.method == 'DELETE':
            if not subscription:
                return Response(
                    {'errors': 'Подписка уже удалена.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if subscription:
            return Response(
                {'errors': 'Вы уже подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if author == request.user:
            return Response(
                {'errors': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Subscription.objects.create(user=request.user, author=author)
        serializer = SubscriptionSerializer(
            author,
            context={
                'request': request,
                'format': self.format_kwarg,
                'view': self,
            },
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(ReadOnlyModelViewSet):
    """Viewset модели тега."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Viewset модели ингредиента."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Viewset модели рецепта."""

    queryset = Recipe.objects.prefetch_related(
        'author', 'tags', 'ingredients'
    ).all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    def handle_action(self, request, pk, model_class):
        if request.method == "POST":
            data, status = self.create_recipe_user(request, pk, model_class)
        else:
            data, status = self.delete_recipe_user(request, pk, model_class)
        return data, status

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Действия с избранным: добавляем/удаляем рецепт."""
        data, status = self.handle_action(request, pk, Favorite)
        return Response(data, status=status)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        """Действия с корзиной: добавляем/удаляем рецепт."""
        data, status = self.handle_action(request, pk, ShoppingCart)
        return Response(data, status=status)

    @action(
        methods=['get'], detail=False, permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Выгружаем список продуктов из корзины (формат txt)."""
        ingredients = (
            RecipeIngredients.objects.filter(
                recipe__shoppingcart__user=request.user
            )
            .values(
                'ingredient__name', 'ingredient__measurement_unit', 'amount'
            )
            .order_by('ingredient__name')
        )
        shopping_list = self.create_ingredient_list(ingredients)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            'Список_покупок.txt'
        )
        return response

    def create_ingredient_list(self, queryset) -> list:
        """Доп.функция: создаем список продуктов по рецептам из корзины."""
        ingredient_data = defaultdict(int)
        for ingredient in queryset:
            ingredient_name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['amount']
            key = f'{ingredient_name} ({measurement_unit})'
            ingredient_data[key] += amount

        ingredient_list = []
        ingredient_list.append('Список продуктов: \n')
        for ingredient, amount in ingredient_data.items():
            ingredient_list.append(f'{ingredient} - {amount} \n')

        return ingredient_list

    def manage_recipe_user(self, request, pk, model, action):
        """Общая функция для создания/удаления связки
        рецепт<->пользователь по id рецепта.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        if action == 'create':
            obj, created = model.objects.get_or_create(
                recipe=recipe, user=request.user
            )
            if not created:
                return (
                    {"message": f"Уже есть рецепт с id = {pk}."},
                    status.HTTP_400_BAD_REQUEST,
                )
        elif action == 'delete':
            try:
                favorite_recipe = model.objects.get(
                    recipe=recipe, user=request.user
                )
                favorite_recipe.delete()
            except model.DoesNotExist:
                return (
                    {"message": f"Рецепт с id = {pk} не найден."},
                    status.HTTP_404_NOT_FOUND,
                )
        serializer = RecipeListSerializer(recipe, context={'request': request})
        return (
            (serializer.data, status.HTTP_201_CREATED)
            if action == 'create'
            else (None, status.HTTP_204_NO_CONTENT)
        )

    def create_recipe_user(self, request, pk, model):
        """Доп.функция: создаем связку рецепт<->пользователь по id рецепта."""
        return self.manage_recipe_user(request, pk, model, action='create')

    def delete_recipe_user(self, request, pk, model):
        """Доп.функция: удаляем связку рецепт<->пользователь по id рецепта."""
        return self.manage_recipe_user(request, pk, model, action='delete')
