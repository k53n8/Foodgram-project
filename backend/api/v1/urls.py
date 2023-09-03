from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

v1_router = DefaultRouter()
v1_router.register('users', UserViewSet, basename='users')
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('tags', TagViewSet, basename='genres')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')


auth_urls = [
    path('token/login/', TokenCreateView.as_view()),
    path('token/logout/', TokenDestroyView.as_view())
]

urlpatterns = [
    path('auth/', include(auth_urls)),
    path('', include(v1_router.urls)),
]
