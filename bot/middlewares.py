from abc import ABC

from aiogram.types import Message, Update
from aiogram.utils.i18n import I18nMiddleware, I18n, FSMI18nMiddleware
from typing_extensions import Optional

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api


class LanguageMiddleware(I18nMiddleware):

    async def get_locale(self, data: dict, event: Update = None, message: Message = None, ) -> None:
        if event.message:
            telegram_user_id = event.message.from_user.id
        else:
            telegram_user_id = event.callback_query.from_user.id
        # Здесь получите язык пользователя из базы данных
        options = await get_profiles_options_api(telegram_user_id)
        lang = options["telegram_language"]
        return lang
