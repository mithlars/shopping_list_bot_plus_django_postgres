import os

API_TOKEN = os.getenv("API_TOKEN")

django_address = os.getenv("DJANGO_ADDRESS")
django_login_url = f"{django_address}/login/"

admin_telegram_id = 129727111

startup_admin_message = "Бот вышел в онлайн"

start_welcome_message = "Welcome to the bot"

DJANGO_USERNAME = os.getenv("DJANGO_USERNAME")
DJANGO_USER_PASSWORD = os.getenv("DJANGO_USER_PASSWORD")

buttons_styles = ['pics', 'text', 'both']
