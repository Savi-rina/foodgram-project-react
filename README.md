## Foodgram

"Foodgram" is a product assistant where users have an opportunity to 
publish 
recipes, add other people's recipes to favorites and subscribe authors who 
post incredible recipes to the site.
Besides, the "Shopping list" feature allows users to create a list of products 
that need to be bought for cooking of selected dishes.

## 1. Technologies:

    - Python
    - Django
    - Djangorestframework
    - Docker
    - Nginx
    - PostgresSQL
    - React

## 2. How to launch using containers:

#### 1) Run build and docker compose (from "infra" directory);
#### 2) Make migrations;
#### 3) Collect static;
#### 4) Create superuser;
#### 5) Import ingredients;
#### 6) Make database dump (if needed);


```
docker compose up -d --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py import_data
docker compose exec backend python manage.py dumpdata > fixtures.json
 ```

## 3. Site and credentials for admin panel:
```
http://51.250.18.15/recipes
Email: admin@admin.com
Password: admin
```

## 4. Requests examples for API:

#### Actions with users:

**GET:** `/api/users/` - to get all users list

**GET:** `/api/users/{id}/` - to get a user`s profile

**GET:** `/api/users/me/` - to get a current user


#### Actions with recipes:

**GET:** `/api/recipes/` - to get all recipes list

**POST:** `/api/recipes/` - to create a recipe

## 5. Backend created by:

Irina Savenko [GitHub](https://github.com/Savi-rina)


