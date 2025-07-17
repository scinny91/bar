FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
#RUN DJANGO_SETTINGS_MODULE=bar_site.settings python manage.py collectstatic --noinput
CMD ["gunicorn", "bar_app.wsgi:application", "--bind", "0.0.0.0:8000"]