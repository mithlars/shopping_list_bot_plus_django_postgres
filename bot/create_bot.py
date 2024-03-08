from constants import API_TOKEN
from aiogram import Bot, Dispatcher


class MyBot:
    # Объект бота
    bot = Bot(token=API_TOKEN)
    # Диспетчер
    dp = Dispatcher()
