from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, Tag
from users.models import Follow, User
from .filters import IngredientFilter, RecipeFilter
from .paginations import PageRequiredPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer, UserInfoSerializer)


class CustomUserViewSet(UserViewSet):
    """Вьюсет пользователей."""
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer
    pagination_class = PageRequiredPagination
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        
        if request.method == 'POST':
            serializer = FollowSerializer(author, data=request.data,
                                          context={"request": request})
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=request.user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            subscription = get_object_or_404(Follow, user=request.user, author=author)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = PageRequiredPagination
    
    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeCreateUpdateSerializer
    
    def perform_create(self, serializer):
        
        serializer.save(author=self.request.user)
    
    def action_post_delete(self, pk, serializer_class):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        item = serializer_class.Meta.model.objects.filter(user=user,
                                                          recipe=recipe)
        
        if self.request.method == 'POST':
            serializer = serializer_class(data={'user': user.id, 'recipe': pk},
                                          context={'request': self.request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if self.request.method == 'DELETE':
            if item.exists():
                item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({'error': 'Рецепт отсутствует в списке или '
                                      'удален'},
                            status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['POST', 'DELETE'], detail=True)
    def favorite(self, request, pk):
        return self.action_post_delete(pk, FavoriteSerializer)
    
    @action(methods=['POST', 'DELETE'], detail=True)
    def shopping_cart(self, request, pk):
        return self.action_post_delete(pk, ShoppingCartSerializer)
    
    @action(detail=False)
    def download_shopping_cart(self, request):
        title = 'recipe__ingredients__name'
        measurement = 'recipe__ingredients__measurement_unit'
        quantity = 'recipe__recipe_ingredient__amount'
        
        ingredients = request.user.shopping_cart.select_related(
            'recipe').order_by(title).values(title, measurement).annotate(
            amount=Sum(quantity)).all()
        
        if not ingredients:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        text = 'Список покупок:\n\n'
        for number, ingredient in enumerate(ingredients, start=1):
            amount = ingredient['amount']
            text += (f'{number}) '
                     f'{ingredient[title]} - '
                     f'{amount} '
                     f'{ingredient[measurement]}\n')
        
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
