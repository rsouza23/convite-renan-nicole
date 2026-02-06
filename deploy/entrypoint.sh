#!/bin/bash

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Rodar migrações
python manage.py migrate

# Garantir que o superusuário seja criado (caso não exista)
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
EOF

# Iniciar o Nginx
/usr/sbin/nginx -g 'daemon off;' &

# Iniciar o Gunicorn
gunicorn bigday.wsgi:application --bind 0.0.0.0:8000
