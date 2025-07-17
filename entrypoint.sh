#!/bin/sh

echo "Aspetto che il database sia pronto..."
while ! nc -z db 5432; do
  sleep 1
done
