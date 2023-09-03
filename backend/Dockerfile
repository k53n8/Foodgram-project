FROM python:3.9

WORKDIR /app

# Скачиваем скрипт wait-for-it
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY . .

# Запускаем скрипт wait-for-it перед запуском нашего приложения
CMD /wait-for-it.sh db:5432 -- gunicorn --bind 0.0.0.0:10000 foodgram.wsgi