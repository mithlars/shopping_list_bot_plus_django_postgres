# PowerShell script
echo "start"
$POSTGRES_PASSWORD = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")
$DJANGO_USERNAME = [Environment]::GetEnvironmentVariable("DJANGO_USERNAME")
$DJANGO_USER_PASSWORD = [Environment]::GetEnvironmentVariable("DJANGO_USER_PASSWORD")
$API_TOKEN = [Environment]::GetEnvironmentVariable("API_PROD_TEST_TOKEN")
$LINUX_SERVER_IP = [Environment]::GetEnvironmentVariable("LINUX_SERVER_IP")

ssh -i C:\Users\lars5\.ssh\id_rsa root@$LINUX_SERVER_IP @"
#!/bin/bash

echo "exporting variables"
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD
export DJANGO_USERNAME=$DJANGO_USERNAME
export DJANGO_USER_PASSWORD=$DJANGO_USER_PASSWORD
export API_TOKEN=$API_TOKEN
export COMPOSE_PROJECT_NAME=shopping_list

echo "Stopping containers:"
docker stop bot django postgres

echo "rm containers:"
docker rm bot django postgres

echo "removing docker images:"
docker image rm shopping_list_bot shopping_list_django:latest

echo "removing docker-network named shopping_list_net:"
docker network rm shopping_list_net

echo "creating docker-network named shopping_list_net:"
docker network create --subnet=172.18.0.0/16 shopping_list_net

echo "\nmoving to /home/django_bot\n"
mkdir -m a=rwx /home/django_bot
cd /home/django_bot

echo "\nremoving old version code\n"
rm -rf ./*

echo "\ndownloading last version code:\n"
git clone https://github.com/mithlars/shopping_list_bot_plus_django_postgres

echo "moving to the project folder"
cd shopping_list_bot_plus_django_postgres

# echo "\nremoving base docker images:\n"
# docker image rm django_base bot_base

echo "\nbuild base image for django\n"
docker build -t django_base:latest -f djDocker/Dockerfile.base .

echo "\nbuild base image for bot\n"
docker build -t bot_base:latest -f Dockerfile.bot_base .

echo "building new versions of images and upping new versions of containers:"
docker-compose up -d

echo "end"
"@