# PowerShell script
$POSTGRES_PASSWORD = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")
$DJANGO_USERNAME = [Environment]::GetEnvironmentVariable("DJANGO_USERNAME")
$DJANGO_USER_PASSWORD = [Environment]::GetEnvironmentVariable("DJANGO_USER_PASSWORD")
$API_TOKEN = [Environment]::GetEnvironmentVariable("API_TOKEN")


ssh -i C:\Users\lars5\.ssh\id_rsa root@165.227.159.101 @"
#!/bin/bash
# Экспорт переменных в sh-сессию:
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD
export DJANGO_USERNAME=$DJANGO_USERNAME
export DJANGO_USER_PASSWORD=$DJANGO_USER_PASSWORD
export API_TOKEN=$API_TOKEN
export COMPOSE_PROJECT_NAME=shopping_list

# Проверяем существование docker-сети:
docker network inspect shopping_list_net >/dev/null 2>&1 && \
# Если сеть существует, проверяем настройки подсети:
SUBNET=$(docker network inspect shopping_list_net -f '{{(index .IPAM.Config 0).Subnet}}') || \
# Если сеть не существует, создаем новую:
docker network create --subnet=172.18.0.0/16 shopping_list_net
# Если сеть существует, но настройки подсети отличаются, создаем новую:
if [ "$SUBNET" != "172.18.0.0/16" ]; then
  docker network rm shopping_list_net
  docker network create --subnet=172.18.0.0/16 shopping_list_net
fi

# Останавливаем контейнеры:
docker stop bot django postgres
# Удаляем контейнеры:
docker rm bot django postgres
# Удаляем образы:
docker image rm shopping_list_bot shopping_list_django:latest

# Переходим в папку в которой хранится папка проекта:
cd /home/django_bot
# Удаляем старую версию кода проекта:
rm -rf ./*
# Загружаем последнюю версию кода проекта:
git clone https://github.com/mithlars/shopping_list_bot_plus_django_postgres

# Переходим в папку проекта:
cd shopping_list_bot_plus_django_postgres
# Запускаем сборку образов и запуск контейнеров:
docker-compose up -d
"@