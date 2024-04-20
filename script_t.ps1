# PowerShell script
echo "start"
$POSTGRES_PASSWORD = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")
$DJANGO_USERNAME = [Environment]::GetEnvironmentVariable("DJANGO_USERNAME")
$DJANGO_USER_PASSWORD = [Environment]::GetEnvironmentVariable("DJANGO_USER_PASSWORD")
$API_TOKEN = [Environment]::GetEnvironmentVariable("API_TOKEN")
$LINUX_SERVER_IP = [Environment]::GetEnvironmentVariable("LINUX_SERVER_IP")


ssh -i C:\Users\lars5\.ssh\id_rsa lars50@172.19.140.180 @"
#!/bin/bash

echo "exporting variables"
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD
export DJANGO_USERNAME=$DJANGO_USERNAME
export DJANGO_USER_PASSWORD=$DJANGO_USER_PASSWORD
export API_TOKEN=$API_TOKEN
export COMPOSE_PROJECT_NAME=shopping_list_test

echo "Stopping containers:"
docker stop bot_t django_t postgres_t

echo "rm containers:"
docker rm bot_t django_t postgres_t

echo "removing docker images:"
docker image rm shopping_list_test_bot_t shopping_list_test_django_t:latest

echo "removing docker-network named shopping_list_net_t:"
docker network rm shopping_list_net_t

echo "creating docker-network named shopping_list_net_t:"
docker network create --subnet=172.16.0.0/16 shopping_list_net_t

echo "moving to /home/lars50/django_bot_t"
mkdir -m a=rwx /home/lars50/django_bot_t
cd /home/lars50/django_bot_t

echo "removing old version code"
rm -rf ./*

echo "downloading last version code:"
git clone https://github.com/mithlars/shopping_list_bot_plus_django_postgres

echo "moving to the project folder"
cd shopping_list_bot_plus_django_postgres

# echo "removing base docker images:"
# docker image rm django_base bot_base

echo "\nbuild base image for django\n"
docker build -t django_base:latest -f djDocker/Dockerfile.base .

echo "\nbuild base image for bot\n"
docker build -t bot_base:latest -f Dockerfile.bot_base .

echo "building new versions of images and upping new versions of containers:"
docker-compose -f docker-compose_t.yml up -d

echo "end"
"@