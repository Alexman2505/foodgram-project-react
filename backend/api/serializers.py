import base64

from django.contrib.auth.hashers import check_password
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import Ingredient, Recipe, RecipeIngredients, Tag
from rest_framework import serializers
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Декодируем фото."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = {self.context["request"].user.username}
            data = ContentFile(base64.b64decode(imgstr), name=f'{name}.' + ext)
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериализатор регистрации новых пользователей."""
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password',
        )

    def validate_username(self, value):
        if value.lower() == 'me':
            raise serializers.ValidationError(
                'Имя пользователя "me" недопустимо.')
        return value


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор отображения информации о пользователе."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Определяем подписан ли пользователь на просматриваемого
        пользователя (значение параметра is_subscribed: true или false)."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user).exists()


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор изменения пароля."""
    new_password = serializers.CharField()
    current_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("Текущий пароль неверен.")
        return value


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор подписки на других авторов."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )
        depth = 1

    def get_recipes(self, obj):
        """Определяем список рецептов в подписке."""
        recipes_limit = self.context['request'].GET.get('recipes_limit')
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeListSerializer(
            recipes,
            many=True,
            read_only=True
        ).data

    def get_recipes_count(self, obj):
        """Определяем общее количество рецептов в подписке."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиента."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор состава ингридиентов в сохраненном рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор состава ингридиентов в создаваемом рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для связки: рецепт<->пользователь
    (подписка, избранное)."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    tags = TagSerializer(many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        """Определяем, является ли рецепт избранным для пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_favorited(request.user)

    def get_is_in_shopping_cart(self, obj):
        """Определяем, находится ли рецепт в корзине пользователя."""
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return obj.is_in_shopping_cart(request.user)


class RecipeCreateSerializer(RecipeSerializer):
    """Сериализатор создания и изменения рецепта."""
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())
    ingredients = RecipeIngredientCreateSerializer(
        source='recipeingredients',
        many=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',
        )

    def validate(self, data):
        for field in ('tags', 'ingredients', 'name', 'text', 'cooking_time'):
            if not self.initial_data.get(field):
                raise serializers.ValidationError(
                    f'Не заполнено поле `{field}`')
        ingredients = self.initial_data['ingredients']
        ingredients_set = set()
        for ingredient in ingredients:
            if not ingredient.get('amount') or not ingredient.get('id'):
                raise serializers.ValidationError(
                    'Необходимо указать `amount` и `id` для ингредиента.')
            if not int(ingredient['amount']) > 0:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть меньше 1.')
            if ingredient['id'] in ingredients_set:
                raise serializers.ValidationError(
                    'Необходимо исключить повторяющиеся ингредиенты.')
            ingredients_set.add(ingredient['id'])
        return data

    def create(self, validated_data):
        """Создание нового рецепта с сохранением связанных тегов и
        иенредиентов."""
        request = self.context.get('request')
        author = request.user
        validated_data['author'] = author
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)
        self.create_recipe_ingredient(recipe, ingredients)

        return recipe

    def update(self, instance, validated_data):
        """Изменение рецепта с обновлением связанных тегов и
        ингредиентов."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')

        instance.ingredients.clear()
        instance.tags.clear()

        super().update(instance, validated_data)

        instance.tags.set(tags)
        self.create_recipe_ingredient(instance, ingredients)

        return instance

    def create_recipe_ingredient(self, recipe, ingredients):
        """Доп.функция: создаем связку рецепт<->ингредиент."""
        recipe_ingredients = []

        for ing in ingredients:
            ingredient_id = ing['id']
            ingredient_amount = ing['amount']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            recipe_ingredient = RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_amount)
            recipe_ingredients.append(recipe_ingredient)

        RecipeIngredients.objects.bulk_create(recipe_ingredients)
