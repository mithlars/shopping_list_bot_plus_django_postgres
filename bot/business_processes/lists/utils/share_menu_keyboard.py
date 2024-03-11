from typing import Dict

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.business_processes.options.utils.get_profiles_options_api import get_profiles_options_api
from bot.emoji import emoji
from bot.translate import transl


def share_menu_keyboard_buttons(lang: str) -> Dict[str, Dict]:
    buttons_long = transl[lang]['share_menu']['buttons']
    buttons_short = transl[lang]['share_menu']['buttons_short']
    buttons = {  # "access", "surrounding", "add_me", "back_to_lists", "back"
        'pics': {  # 'pics': ["Доступ к списку", "Окружение", "Добавь меня", "↩️📦", "↩️📋"]
            'access':        buttons_long['access'],
            'surrounding':   buttons_long['surrounding'],
            'add_me':        buttons_long['add_me'],
            'back_to_lists': emoji['back'] + emoji['lists'],
            'back':          emoji['back'] + emoji['list']
        },
        'text': {  # 'text': ["Доступ к списку", "Окружение", "Добавь меня", "Назад к спискам", "назад"]
            'access':        buttons_long['access'],
            'surrounding':   buttons_long['surrounding'],
            'add_me':        buttons_long['add_me'],
            'back_to_lists': buttons_long['back_to_lists'],
            'back':          buttons_long['back']
        },
        'both': {  # 'both': ["Доступ к списку", "Окружение", "Добавь меня", "↩️📦к спискам", "↩️📋назад"]
            'access':        buttons_short['access'],
            'surrounding':   buttons_short['surrounding'],
            'add_me':        buttons_short['add_me'],
            'back_to_lists': emoji['back'] + emoji['lists'] + buttons_short['back_to_lists'],
            'back':          emoji['back'] + emoji['list'] + buttons_short['back']
        },
    }  # TODO: Доделать сортировку групп
    return buttons


async def share_menu_keyboard(telegram_user_id: int) -> ReplyKeyboardMarkup:
    options = await get_profiles_options_api(telegram_user_id)
    lang = options["telegram_language"]
    buttons = share_menu_keyboard_buttons(lang)
    style = options["telegram_buttons_style"]
    builder = ReplyKeyboardBuilder()
    for button_text in buttons[style].values():
        builder.add(KeyboardButton(text=button_text))
    builder.adjust(3, 2)
    keyboard = builder.as_markup(resize_keyboard=True)
    return keyboard
