from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAdminOrReadOnly, IsAuthorOrReadOnly
from .serializers import (ChangePasswordSerializer, CustomUserCreateSerializer,
                          CustomUserSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeListSerializer,
                          RecipeSerializer, SubscriptionSerializer,
                          TagSerializer)


class CustomUserViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Кастомный Viewset модели пользователя."""
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserCreateSerializer
        return CustomUserSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={
                'request': request,
                'format': self.format_kwarg,
                'view': self
            }
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        subscription = Subscription.objects.filter(
            user=request.user, author=author)
        if request.method == 'DELETE' and not subscription:
            return Response(
                {'errors': 'Подписка уже удалена.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if subscription:
            return Response(
                {'errors': 'Вы уже подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if author == request.user:
            return Response(
                {'errors': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=request.user, author=author)
        serializer = SubscriptionSerializer(
            author,
            context={
                'request': request,
                'format': self.format_kwarg,
                'view': self
            }
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CurrentUserMeView(views.APIView):
    """View class просмотра текущего пользователя (себя)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(
            request.user,
            context={
                'request': request,
                'format': self.format_kwarg,
                'view': self
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(views.APIView):
    """View class изменения пароля."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        return Response(
            {'message': 'Пароль успешно изменен.'},
            status=status.HTTP_200_OK
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset модели тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset модели ингредиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Viewset модели рецепта."""
    queryset = Recipe.objects.prefetch_related(
        'author', 'tags', 'ingredients').all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateSerializer

    @action(methods=['post', 'delete'], detail=True)
    def favorite(self, request, pk):
        """Действия с избранным: добавляем/удаляем рецепт."""
        if request.method == "POST":
            data, status = self.create_recipe_user(request, pk, Favorite)
            return Response(data, status=status)
        data, status = self.delete_recipe_user(request, pk, Favorite)
        return Response(data, status=status)

    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        """Действия с корзиной: добавляем/удаляем рецепт."""
        if request.method == "POST":
            data, status = self.create_recipe_user(request, pk, ShoppingCart)
            return Response(data, status=status)
        data, status = self.delete_recipe_user(request, pk, ShoppingCart)
        return Response(data, status=status)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Выгружаем список продуктов из корзины (формат txt)."""
        ingredients = RecipeIngredients.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'amount').order_by('ingredient__name')
        shopping_list = self.create_ingredient_list(ingredients)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format('Список_покупок.txt')
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

    def create_recipe_user(self, request, pk, model):
        """Доп.функция: создаем связку рецепт<->пользователь по id рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        obj, created = model.objects.get_or_create(
            recipe=recipe,
            user=request.user
        )
        if not created:
            return (
                {"message": f"Уже есть рецепт с id = {pk}."},
                status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeListSerializer(
            recipe,
            context={'request': request}
        )
        return (serializer.data, status.HTTP_201_CREATED)

    def delete_recipe_user(self, request, pk, model):
        """Доп.функция: удаляем связку рецепт<->пользователь по id рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        favorite_recipe = get_object_or_404(
            model,
            recipe=recipe,
            user=request.user
        )
        favorite_recipe.delete()
        return (
            {"message": f"Рецепт с id = {pk} удален."},
            status.HTTP_204_NO_CONTENT
        )
