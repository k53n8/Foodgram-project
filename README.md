# Foodgram
[![foodgram_workflow](https://github.com/k53n8/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/k53n8/foodgram-project-react/actions/workflows/foodgram_workflow.yml)
### Описание
На сайте Foodgram пользователи могут публиковать свои рецепты, смотреть публикации других пользователей и подписываться на них.
Для удобства можно скачать список ингридентов для нужного рецепта.
### Стек технологий:
- Django
- REST Api 
- Djoser
- Docker
- GitHub Actions
- PostgreSQL
### Запуск проекта:
- Создайте в корне проекта файл виртуального окружения `.env` и заполните его по образцу `.env.example`
- Далее перейдите в директорию `infra` и выполните там команду:\
`docker compose -f docker-compose.yml up -d`\
Это запустит docker-контейнеры с БД, сетевой конфигурации, бэкенда и фронтэнда.
- Применяем миграции:\
`docker compose -f docker-compose.yml exec backend python manage.py migrate`
- Собираем статику:\
`docker compose -f docker-compose.yml exec backend python manage.py collectstatic --no-input`
- Импортируем список ингредиентовd в БД:\
`docker compose -f docker-compose.yml exec backend python manage.py import_csv_data`
- Документация к проекту доступна по эндпойнту `http://foodgram.ydns.eu/api/docs/redoc.html`
### Пример запроса:
```
GET /api/users/
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "email": "ogz2ir@ya.ru",
            "id": 3,
            "username": "Oleja _tashi",
            "first_name": "Юра",
            "last_name": "К."
        },
        {
            "email": "sup@sup.com",
            "id": 1,
            "username": "SUPERADMIN",
            "first_name": "Админ",
            "last_name": "Суперпользователь"
        },
        {
            "email": "test@test.com",
            "id": 2,
            "username": "Testoviy",
            "first_name": "Семён",
            "last_name": "Тестовый"
        }
    ]
}
```
### Авторы проекта:
- Команда ЯндексПрактикум
- Олег Иванов


