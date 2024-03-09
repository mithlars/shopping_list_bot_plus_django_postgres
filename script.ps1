# PowerShell script
$POSTGRES_PASSWORD = [Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")
$DJANGO_USERNAME = [Environment]::GetEnvironmentVariable("DJANGO_USERNAME")
$DJANGO_USER_PASSWORD = [Environment]::GetEnvironmentVariable("DJANGO_USER_PASSWORD")
$API_TOKEN = [Environment]::GetEnvironmentVariable("API_TOKEN")

$sshCommand = @"
#!/bin/bash
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD
export DJANGO_USERNAME=$DJANGO_USERNAME
export DJANGO_USER_PASSWORD=$DJANGO_USER_PASSWORD
export API_TOKEN=$API_TOKEN
cd /home/django_bot
git clone https://github.com/mithlars/shopping_list_bot_plus_django_postgres
cd shopping_list_bot_plus_django_postgres
docker-compose up -d
"@

ssh -i C:\Users\lars5\.ssh\id_rsa root@165.227.159.101 "$sshCommand"