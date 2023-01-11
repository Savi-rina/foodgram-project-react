from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Модель пользователя."""
    email = models.EmailField(verbose_name='Электронная почта', unique=True,
                              max_length=50, )
    username = models.CharField(verbose_name='Логин', max_length=150,
                                unique=True, )
    password = models.CharField('Пароль', max_length=150, )
    first_name = models.CharField(verbose_name='Имя', max_length=100, )
    last_name = models.CharField(verbose_name='Фамилия', max_length=100, )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'password', 'first_name', 'last_name')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [UniqueConstraint(fields=('username', 'email'),
                                        name='unique_username_email', )]
    
    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок."""
    user = models.ForeignKey(User, related_name='follower',
                             verbose_name='Подписчик',
                             on_delete=models.CASCADE, )
    author = models.ForeignKey(User, related_name='following',
                               verbose_name='Автор',
                               on_delete=models.CASCADE, )
    
    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(fields=('user', 'author'), name='unique_follow')]
    
    def __str__(self):
        return f'{self.user} подписан на {self.author}'
