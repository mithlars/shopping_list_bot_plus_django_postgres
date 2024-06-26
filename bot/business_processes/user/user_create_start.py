from aiogram import Router
from aiogram.types import Message, User
from aiogram.filters import CommandStart
from requests import Response

from bot.business_processes.lists.list_create import ListCreateAPI
from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_builder
from bot.create_bot import MyBot
from bot.constants import django_address

from bot.api.django_auth import django_auth, update_last_request_time

from aiogram.utils.i18n import gettext as _


class RegisterAPI:

    @staticmethod
    @update_last_request_time(django_auth)
    async def register_new_user(user: User) -> Response:
        """
        Add new profile request to Django.
        Returns report message.
        """
        url = f"{django_address}/telegram_register/"
        data = {
            "telegram_user_id": user.id,
            "telegram_user_name": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language_code": user.language_code
        }
        response = await django_auth.session.post(url=url, data=data)
        return response


start_router = Router()


class Start:

    @staticmethod
    @start_router.message(CommandStart())
    async def create_new_user(message: Message):
        telegram_user_id = message.from_user.id
        await RegisterAPI.register_new_user(message.from_user)  # TODO: Перевести:
        await ListCreateAPI.create_new_list(telegram_user_id, _("First list"), "")
        keyboard = await list_menu_keyboard_builder(telegram_user_id)
        start_welcome_message = _("Welcome to the bot")
        await MyBot.bot.send_message(chat_id=telegram_user_id, text=start_welcome_message, reply_markup=keyboard)
