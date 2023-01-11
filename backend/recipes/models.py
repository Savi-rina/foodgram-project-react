from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(verbose_name='Название ингредиента',
                            max_length=100)
    measurement_unit = models.CharField(verbose_name='Единица измерения',
                                        max_length=10)
    
    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
    
    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(verbose_name='Тег', max_length=30, unique=True)
    color = models.CharField(max_length=20, verbose_name='Цвет')
    slug = models.SlugField(max_length=20, verbose_name='Слаг', unique=True)
    
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
    
    def __str__(self):
        return f'{self.name}'


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField(verbose_name='Название рецепта', max_length=200)
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         through='RecipeIngredient',
                                         related_name='recipe')
    image = models.ImageField(verbose_name='Изображение',
                              upload_to='recipes_media')
    text = models.TextField(verbose_name='Описание рецепта')
    
    author = models.ForeignKey(to=User, on_delete=models.CASCADE,
                               related_name='recipes', verbose_name='Автор')
    
    cooking_time = models.IntegerField(verbose_name='Время приготовления',
                                       validators=(
                                       MinValueValidator(limit_value=1,
                                           message='Время приготовления не '
                                                   'может быть меньше 1 '
                                                   'минуты.'),))
    tags = models.ManyToManyField(Tag, verbose_name='Теги',
                                  related_name='recipes')
    pub_date = models.DateTimeField(auto_now=True,
                                    verbose_name='Дата публикации')
    
    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
    
    def __str__(self):
        return f'{self.name[:100]}'


class RecipeIngredient(models.Model):
    """Промежуточная модель ингредиент_рецепт."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='recipe_ingredient',
                               )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.IntegerField(verbose_name='Количество', validators=(
        MinValueValidator(limit_value=2,
                          message='Количество ингредиентов должно быть '
                                  'больше одного'),))
    
    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [UniqueConstraint(fields=('recipe', 'ingredient'),
                                        name='уникальные_ингредиенты_в_рецепте')]
    
    def __str__(self):
        return f'{self.recipe}: {self.ingredient} – {self.amount}'


class Favorite(models.Model):
    """Модель избранного."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='favorite')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепты', related_name='favorite')
    
    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (UniqueConstraint(fields=('user', 'recipe'),
                                        name='уникальные_рецепты_в_избранном'),)
    
    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь',
                             related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               verbose_name='Рецепты',
                               related_name='shopping_cart')

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'
        constraints = (UniqueConstraint(fields=('user', 'recipe'),
                                        name='уникальные_рецепты_в_списке_'
                                             'покупок'),)
    
    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'
