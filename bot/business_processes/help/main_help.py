from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.business_processes.purchases.utils.list_menu_keyboard import list_menu_keyboard_builder
from bot.create_bot import MyBot
from bot.emoji import emoji
from bot.middlewares import i18n
from bot.translate import transl

help_router = Router()


class HelpCommand:

    @staticmethod
    @help_router.message(F.text == emoji['help'])
    async def help_command_handler(message: Message):
        telegram_bot_id = message.from_user.id
        lang = i18n.current_locale
        message_text = transl[lang]['main_help']
        keyboard = await list_menu_keyboard_builder(telegram_bot_id)
        await MyBot.bot.send_message(chat_id=telegram_bot_id,
                                     text=message_text,
                                     reply_markup=keyboard,
                                     parse_mode='Markdown')

