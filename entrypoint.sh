#!/bin/sh

echo "Aspetto che il database sia pronto..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Database pronto, avvio Gunicorn"
exec gunicorn bar_app.wsgi:application --bind 0.0.0.0:8000