from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UsersViewSet

v1_router = DefaultRouter()
v1_router.register('users', UsersViewSet, basename='users')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]
