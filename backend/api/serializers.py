from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class GetSubscribedMixin:
    """Миксин для отображения информации о подписках"""
    def get_is_subscribed(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=object.id).exists()
    

class CreateUserSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя."""
    
    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')


class UserInfoSerializer(UserSerializer, GetSubscribedMixin):
    """Сериализатор для отображения информации о пользователе."""
    is_subscribed = SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор отображения краткой информации о рецепте."""
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        
        
class FollowSerializer(serializers.ModelSerializer, GetSubscribedMixin):
    """Сериализатор для подписок."""
    recipes = ShortRecipeSerializer(read_only=True, many=True)
    recipes_count = SerializerMethodField(read_only=True)
    is_subscribed = SerializerMethodField(read_only=True)
    
    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count')
        model = User
        read_only_fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count')
    
    def get_recipes_count(self, object):
        return object.recipes.count()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов рецепта."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор отображения информации о рецепте."""
    author = UserInfoSerializer(read_only=True)
    tags = TagSerializer(many=True)
    image = Base64ImageField()
    ingredients = RecipeIngredientsSerializer(source='recipe_ingredient',
                                              many=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart')
    
    def get_is_favorited(self, obj):
        user = self.context['request'].user
        
        if user.is_anonymous:
            return False
        
        return Favorite.objects.filter(user=user, recipe=obj).exists()
    
    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        
        if user.is_anonymous:
            return False
        
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
    
    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор отображения добавления/обновления рецепта."""
    author = serializers.ReadOnlyField(required=False)
    tags = serializers.SlugRelatedField(slug_field='id',
                                        queryset=Tag.objects.all(), many=True)
    ingredients = serializers.ListField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(MinValueValidator(1, message='Время приготовления не'
                                                 'может быть'
                                                 ' меньше 1 минуты.'),))
    
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time', 'ingredients',
                  'tags', 'text', 'author')
    
    def validate_ingredients(self, data):
        if not data:
            raise exceptions.ValidationError(
                'Добавьте хотя бы один ингредиент.')
        
        ingredients = [item['id'] for item in data]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'Ингредиенты в рецепте не могут повторяться.')
        
        return data
    
    def recipe_amount_ingredients_write(recipe, ingredients):
        for ingredient in ingredients:
            ingredient_object = get_object_or_404(Ingredient,
                                                  id=ingredient.get('id'))
            RecipeIngredient.objects.create(recipe=recipe,
                                            ingredient=ingredient_object,
                                            amount=ingredient['amount'])
    
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        RecipeCreateUpdateSerializer.recipe_amount_ingredients_write(recipe,
                                                                     ingredients)
        
        return recipe
    
    def update(self, instance, validated_data):
        ingredients = validated_data.get('ingredients')
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        tags = validated_data.get('tags')
        if tags:
            instance.tags.clear()
            instance.tags.set(tags)
        
        if ingredients:
            instance.ingredients.clear()
            RecipeCreateUpdateSerializer.recipe_amount_ingredients_write(
                instance, ingredients)
        
        instance.save()
        return instance
    
    def to_representation(self, instance):
        request = self.context.get('request')
        serializer = RecipeSerializer(instance, context={'request': request})
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления/удаления рецепта в избранное."""
    
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        
        validators = [UniqueTogetherValidator(queryset=Favorite.objects.all(),
                                              fields=('user', 'recipe'),
                                              message='Рецепт уже добавлен в '
                                                      'избранное')]
    
    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeSerializer(instance.recipe, context=context).data


class ShoppingCartSerializer(FavoriteSerializer):
    """Сериализатор списка покупок."""
    
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(queryset=ShoppingCart.objects.all(),
                                    fields=('user', 'recipe'),
                                    message='Рецепт уже есть в '
                                            'списке покупок')]
 