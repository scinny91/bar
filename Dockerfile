FROM python:3.10-slim
WORKDIR /app

# Installa dipendenze di sistema necessarie per mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
#RUN DJANGO_SETTINGS_MODULE=bar_site.settings python manage.py collectstatic --noinput
#CMD ["gunicorn", "bar_app.wsgi:application", "--bind", "0.0.0.0:8000"]

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh