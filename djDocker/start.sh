#!/bin/bash
export DB_CONNECTOR=postgres_container_config
python manage.py makemigrations list
python manage.py migrate list
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username=os.environ.get('DJANGO_USERNAME')).exists():
    user = User.objects.create_user(username=os.environ.get('DJANGO_USERNAME'), password=os.environ.get('DJANGO_USER_PASSWORD'))
else:
    user = User.objects.get(username=os.environ.get('DJANGO_USERNAME'))
with open('./core/telegram_bot_user_id.py', 'w') as f:
    f.write("telegram_bot_user_id = " + str(user.id))
EOF
#while true; do sleep 1000; done
python manage.py runserver 0.0.0.0:8000


