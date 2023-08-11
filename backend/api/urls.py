from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (ChangePasswordView, CurrentUserMeView, CustomUserViewSet,
                    IngredientViewSet, RecipeViewSet, TagViewSet)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('users/me/', CurrentUserMeView.as_view()),
    path('users/set_password/', ChangePasswordView.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
